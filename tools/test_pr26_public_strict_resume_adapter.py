#!/usr/bin/env python3
"""Synthetic-only adapter tests; no private game ROM/save or live-game probe."""
import socket
import threading
import unittest
from unittest.mock import patch

import capture_original_request_rsp as source
import pr26_public_strict_resume_adapter as strict
from test_capture_original_request_rsp import FakeGDB, registers, packet


def fixture(**kw):
    remote = FakeGDB(
        stop_pcs=[strict.GENERATED_THUMB_PC],
        resume_stop_reply=b"T05hwbreak:;",
        **kw,
    )
    remote.gettimeout = lambda: getattr(remote, "timeout", 2.0)
    rsp = source.RSP(remote)
    adapter = strict.PublicStrictStopAdapter(rsp)
    return remote, rsp, adapter


class GeneratedAdapterTests(unittest.TestCase):
    def test_literal_fresh_negotiation_one_c_and_exact_pc(self):
        remote, rsp, a = fixture()
        self.assertEqual(a.negotiate(), source.PUBLIC_QSUPPORTED_REPLY)
        self.assertEqual(a.one_generated_stop(), strict.GENERATED_THUMB_PC)
        self.assertEqual(remote.commands,
                         [source.PUBLIC_QSUPPORTED_COMMAND, "c", "g"])
        self.assertFalse(rsp.running)
        self.assertFalse(rsp._feature_negotiation_failed)
        self.assertEqual(remote.timeout, 2.0)
        with self.assertRaisesRegex(ValueError, "one continue"):
            a.one_generated_stop()
        self.assertNotIn("z0,08000100,2", remote.commands)

    def test_cannot_continue_without_features_or_after_any_preflight(self):
        remote, rsp, a = fixture()
        with self.assertRaisesRegex(ValueError, "must negotiate"):
            a.one_generated_stop()
        self.assertEqual(remote.commands, [])
        self.assertEqual(rsp.send("?"), b"S02")
        with self.assertRaisesRegex(ValueError, "first on a fresh"):
            a.negotiate()
        self.assertEqual(remote.commands, ["?"])

    def test_noncanonical_stop_poison_and_no_cleanup_or_post_g(self):
        for bad in (b"S05k", b"S05", b"T05", b"T05swbreak:;",
                    b"T05hwbreak:;junk", b"T05hwbreak:;\n"):
            remote, rsp, a = fixture()
            remote.resume_stop_reply = bad
            a.negotiate()
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "not exact negotiated"):
                    a.one_generated_stop()
            self.assertEqual(remote.commands, [source.PUBLIC_QSUPPORTED_COMMAND, "c"])
            self.assertTrue(rsp.running)
            self.assertTrue(rsp._feature_negotiation_failed)
            with self.assertRaises(ValueError):
                rsp.send("g")
            self.assertNotIn("z0,08000100,2", remote.commands)

    def test_bad_generated_pc_poison_even_after_valid_stop(self):
        remote, rsp, a = fixture()
        remote.stop_pcs = [0x08000300]
        a.negotiate()
        with self.assertRaisesRegex(ValueError, "poststop PC"):
            a.one_generated_stop()
        self.assertEqual(remote.commands, [source.PUBLIC_QSUPPORTED_COMMAND, "c", "g"])
        self.assertTrue(rsp._feature_negotiation_failed)
        with self.assertRaises(ValueError):
            rsp.send("?")

    def test_ack_disconnect_and_keyboard_interrupt_poison(self):
        remote, rsp, a = fixture(disconnect_on="c")
        a.negotiate()
        with self.assertRaises(ConnectionError):
            a.one_generated_stop()
        self.assertTrue(rsp._feature_negotiation_failed)
        self.assertTrue(rsp.running)
        self.assertEqual(remote.commands, [source.PUBLIC_QSUPPORTED_COMMAND, "c"])
        remote, rsp, a = fixture()
        a.negotiate()
        with patch.object(rsp, "receive", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                a.one_generated_stop()
        self.assertTrue(rsp._feature_negotiation_failed)
        self.assertTrue(rsp.running)
        self.assertNotIn("g", remote.commands)

    def test_timeout_rejects_without_any_continue(self):
        remote, rsp, a = fixture()
        a.negotiate()
        for bad in (0, -1, 3.001, True, float("nan"), "3"):
            with self.subTest(timeout=bad):
                with self.assertRaises(ValueError):
                    a.one_generated_stop(timeout=bad)
        self.assertEqual(remote.commands, [source.PUBLIC_QSUPPORTED_COMMAND])

    def test_real_os_socket_pair_ack_mode_receiver_generated_bytes(self):
        # Genuine OS socket and exact PR26 wire receiver; server sends only
        # synthetic generated-target bytes, NOT a commercial ROM or mGBA.
        client, server = socket.socketpair()
        client.settimeout(2.0)
        server.settimeout(2.0)
        errors = []
        received = []

        def read_request():
            while True:
                ch = server.recv(1)
                if ch == b"+":
                    continue
                if ch != b"$":
                    raise AssertionError("expected RSP packet start")
                break
            data = bytearray()
            while True:
                ch = server.recv(1)
                if ch == b"#":
                    break
                data.extend(ch)
            tail = server.recv(2)
            if int(tail, 16) != (sum(data) & 255):
                raise AssertionError("request checksum wrong")
            return bytes(data)

        def serve():
            try:
                scripted = (
                    (source.PUBLIC_QSUPPORTED_COMMAND.encode("ascii"),
                     source.PUBLIC_QSUPPORTED_REPLY),
                    (b"c", b"T05hwbreak:;"),
                    (b"g", registers(strict.GENERATED_THUMB_PC)),
                )
                for request, response in scripted:
                    payload = read_request()
                    received.append(payload)
                    if payload != request:
                        raise AssertionError("unapproved generated-socket packet")
                    server.sendall(b"+" + packet(response))
                # The client sends a final ACK for the g response.
                if server.recv(1) != b"+":
                    raise AssertionError("missing final GDB ACK")
            except BaseException as error:
                errors.append(error)
            finally:
                server.close()

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        try:
            rsp = source.RSP(client)
            a = strict.PublicStrictStopAdapter(rsp)
            self.assertEqual(a.negotiate(), source.PUBLIC_QSUPPORTED_REPLY)
            self.assertEqual(a.one_generated_stop(timeout=2),
                             strict.GENERATED_THUMB_PC)
            self.assertFalse(rsp._feature_negotiation_failed)
            self.assertFalse(rsp.running)
        finally:
            client.close()
            thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(received,
                         [source.PUBLIC_QSUPPORTED_COMMAND.encode(), b"c", b"g"])
        self.assertNotIn(b"Z0", b"".join(received))

    def test_original_private_run_capture_has_no_adapter_calls(self):
        import inspect
        private_source = inspect.getsource(source.run_capture)
        self.assertNotIn("PublicStrictStopAdapter", private_source)
        self.assertNotIn("negotiate_public_breakpoint_capabilities", private_source)
        self.assertNotIn("strict_public_negotiated_stop", private_source)


if __name__ == "__main__":
    unittest.main()
