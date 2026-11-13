#!/usr/bin/env python3
"""Bounded negative tests; never substitute for actual hosted-mGBA run."""
import socket
import unittest
from cloud_mgba_rsp_fixture import encode_rsp
from cloud_mgba_z0_fixture import SET, REMOVE, breakpoint_request

class Z0FixtureTests(unittest.TestCase):
    def pair(self):
        a,b=socket.socketpair()
        a.settimeout(0.3)
        b.settimeout(0.3)
        self.addCleanup(a.close); self.addCleanup(b.close)
        return a,b

    def test_exact_packets(self):
        self.assertEqual(SET,b"Z0,080000c0,4")
        self.assertEqual(REMOVE,b"z0,080000c0,4")

    def test_denials_send_no_bytes(self):
        a,b=self.pair()
        for cmd in (b"c",b"s",b"\x03",b"Z0,080000c0,2",
                    b"Z0,080000c4,4",b"z0,080000c4,4",
                    b"Z2,080000c0,4",b"M080000c0,4:ffff",
                    b"P0=ffffffff",b"m080000c0,4"):
            with self.subTest(cmd=cmd):
                with self.assertRaises(ValueError):
                    breakpoint_request(a,cmd)
                with self.assertRaises(socket.timeout):
                    b.recv(1)

    def test_install_ack(self):
        a,b=self.pair()
        b.sendall(b"$OK#9a")
        self.assertEqual(breakpoint_request(a,SET),b"OK")
        self.assertEqual(b.recv(200),encode_rsp(SET)+b"+")

    def test_removal_ack(self):
        a,b=self.pair()
        b.sendall(b"$OK#9a")
        self.assertEqual(breakpoint_request(a,REMOVE),b"OK")
        self.assertEqual(b.recv(200),encode_rsp(REMOVE)+b"+")

    def test_negative_reply_rejected(self):
        for bad in (b"",b"E01",b"S05",b"T05"):
            a,b=self.pair()
            frame=b"$"+bad+b"#"+f"{sum(bad)&255:02x}".encode("ascii")
            b.sendall(frame)
            with self.assertRaisesRegex(RuntimeError,"did not acknowledge"):
                breakpoint_request(a,SET)

    def test_corrupt_checksum_rejected(self):
        a,b=self.pair()
        b.sendall(b"$OK#00")
        with self.assertRaisesRegex(RuntimeError,"checksum mismatch"):
            breakpoint_request(a,SET)
        self.assertEqual(b.recv(200),encode_rsp(SET)+b"-")


class RoundtripSafetyTests(unittest.TestCase):
    """Exercise full request ordering with scripted real and mock RSP stubs."""

    def fake_reads(self, events, *, regs=b"00" * 64, rom=b"feffffea"):
        def read(_sock, command):
            events.append(("read", command))
            return {b"?": b"S02", b"g": regs, b"m080000c0,4": rom}[command]
        return read

    def test_invalid_register_or_rom_never_installs_breakpoint(self):
        from unittest.mock import patch
        import cloud_mgba_z0_fixture as fixture
        for regs, rom in ((b"00" * 63, b"feffffea"),
                          (b"00" * 64, b"00000000")):
            events = []
            def breakpoint(_sock, command):
                events.append(("breakpoint", command))
                return b"OK"
            with self.subTest(regs_len=len(regs), rom=rom):
                with patch.object(fixture, "request", side_effect=self.fake_reads(events, regs=regs, rom=rom)), \
                     patch.object(fixture, "breakpoint_request", side_effect=breakpoint):
                    with self.assertRaises(RuntimeError):
                        fixture.roundtrip(object())
            self.assertEqual(events, [("read", b"?"), ("read", b"g"),
                                      ("read", b"m080000c0,4")])

    def test_full_roundtrip_orders_reads_then_install_then_remove(self):
        from unittest.mock import patch
        import cloud_mgba_z0_fixture as fixture
        events = []
        def breakpoint(_sock, command):
            events.append(("breakpoint", command))
            return b"OK"
        with patch.object(fixture, "request", side_effect=self.fake_reads(events)), \
             patch.object(fixture, "breakpoint_request", side_effect=breakpoint):
            self.assertEqual(fixture.roundtrip(object()),
                             (b"S02", b"00" * 64, b"feffffea"))
        self.assertEqual(events, [("read", b"?"), ("read", b"g"),
                                  ("read", b"m080000c0,4"),
                                  ("breakpoint", SET), ("breakpoint", REMOVE)])

    def test_failed_removal_is_explicit_error(self):
        from unittest.mock import patch
        import cloud_mgba_z0_fixture as fixture
        events = []
        def breakpoint(_sock, command):
            events.append(command)
            if command == REMOVE:
                raise RuntimeError("stub rejected removal")
            return b"OK"
        with patch.object(fixture, "request", side_effect=self.fake_reads([])), \
             patch.object(fixture, "breakpoint_request", side_effect=breakpoint):
            with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
                fixture.roundtrip(object())
        self.assertEqual(events, [SET, REMOVE])

    def scripted_ambiguous_install(self, install_reply):
        """Real socket framing: bad/missing install ACK still sends z0 exactly once."""
        from unittest.mock import patch
        import cloud_mgba_z0_fixture as fixture
        import threading
        a, b = socket.socketpair()
        a.settimeout(0.45)
        b.settimeout(0.9)
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        seen, worker_errors = [], []
        def stub():
            try:
                expected = encode_rsp(SET)
                sent = b.recv(len(expected))
                if sent != expected:
                    raise AssertionError("unexpected install packet " + repr(sent))
                seen.append(SET)
                if install_reply is not None:
                    b.sendall(install_reply)
                    self.assertEqual(b.recv(1), b"-")  # bad checksum NAK
                expected_remove = encode_rsp(REMOVE)
                sent = b.recv(len(expected_remove))
                if sent != expected_remove:
                    raise AssertionError("missing exact removal " + repr(sent))
                seen.append(REMOVE)
                b.sendall(b"$OK#9a")
                self.assertEqual(b.recv(1), b"+")
            except Exception as exc:
                worker_errors.append(exc)
        thread = threading.Thread(target=stub, daemon=True)
        thread.start()
        with patch.object(fixture, "request", side_effect=self.fake_reads([])):
            if install_reply is None:
                with self.assertRaises(socket.timeout):
                    fixture.roundtrip(a)
            else:
                with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                    fixture.roundtrip(a)
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive(), "fixture stub must terminate")
        self.assertEqual(worker_errors, [], f"scripted stub failures: {worker_errors}")
        self.assertEqual(seen, [SET, REMOVE])

    def test_corrupted_install_reply_still_removes(self):
        self.scripted_ambiguous_install(b"$OK#00")

    def test_no_install_reply_timeout_still_removes(self):
        self.scripted_ambiguous_install(None)


if __name__ == "__main__":
    unittest.main()
