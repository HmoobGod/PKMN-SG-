#!/usr/bin/env python3
"""Negative and ordering tests for public Thumb-2-byte breakpoint negotiation."""
import hashlib
import os
from pathlib import Path
import socket
import unittest
from unittest.mock import MagicMock, patch

from cloud_mgba_rsp_fixture import encode_rsp, make_fixture
import cloud_rsp_thumb2_fixture as thumb


class PublicThumb2FixtureTests(unittest.TestCase):
    def pair(self):
        a, b = socket.socketpair()
        a.settimeout(0.25)
        b.settimeout(0.25)
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        return a, b

    def test_original_generated_fixture_contains_thumb_entry_and_instruction(self):
        data = thumb.make_thumb_fixture()
        original = make_fixture()
        self.assertEqual(len(data), 32768)
        self.assertEqual(data[:0xC0], original[:0xC0])
        self.assertEqual(data[0xC0:0xC4], thumb.ARM_LDR)
        self.assertEqual(data[0xC4:0xC8], thumb.ARM_BX)
        self.assertEqual(int.from_bytes(data[0xC8:0xCC], "little"), thumb.THUMB_DEST)
        self.assertEqual(data[0x100:0x102], thumb.THUMB_LOOP)
        self.assertEqual(thumb.THUMB_DEST & 1, 1)
        self.assertEqual(thumb.THUMB_DEST & ~1, 0x08000100)
        self.assertEqual(data[0x102:], original[0x102:])

    def test_approved_pr26_reference_source_is_exact_git_blob(self):
        data = (Path(__file__).parent / "pr26_exact_probe_parser_reference.py").read_bytes()
        git_blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        self.assertEqual(hashlib.sha1(git_blob).hexdigest(),
                         "8c55e8acf9b0da6b7957de4a9c5eb84ecd6b1d78")

    def test_only_exact_thumb_memory_and_breakpoint_commands_allowed(self):
        a, b = self.pair()
        for cmd in (b"c", b"s", b"\x03", b"M08000100,2:0000",
                    b"Z0,08000100,4", b"Z0,08000102,2",
                    b"Z2,08000100,2", b"z0,08000102,2",
                    b"m08000100,4", b"m02000000,2"):
            with self.subTest(cmd=cmd):
                with self.assertRaises(ValueError):
                    thumb.thumb_breakpoint(a, cmd)
                with self.assertRaises(ValueError):
                    thumb.thumb_memory(a, cmd)
                with self.assertRaises(socket.timeout):
                    b.recv(1)

    def test_exact_memory_read_and_2byte_reply(self):
        a, b = self.pair()
        b.sendall(encode_rsp(b"fee7"))
        self.assertEqual(thumb.thumb_memory(a, thumb.THUMB_READ), b"fee7")
        self.assertEqual(b.recv(256), encode_rsp(thumb.THUMB_READ) + b"+")

    def test_wrong_thumb_instruction_fails_closed(self):
        a, b = self.pair()
        b.sendall(encode_rsp(b"0000"))
        with self.assertRaisesRegex(RuntimeError, "mapping mismatch"):
            thumb.thumb_memory(a, thumb.THUMB_READ)

    def test_gdb_accepts_exact_size_two_install_and_cleanup(self):
        for command in (thumb.THUMB_SET, thumb.THUMB_REMOVE):
            a, b = self.pair()
            b.sendall(b"$OK#9a")
            self.assertEqual(thumb.thumb_breakpoint(a, command), b"OK")
            self.assertEqual(b.recv(256), encode_rsp(command) + b"+")

    def fake_request(self, events, *, stop=b"S02", regs=b"00" * 68,
                     arm=b"00009fe5", after=b"S02"):
        answers = iter((stop, regs, arm, after))
        def reader(sock, cmd):
            events.append(("read", cmd))
            return next(answers)
        return reader

    def test_roundtrip_orders_preflight_and_cleanup(self):
        events = []
        def mem(sock, cmd):
            events.append(("mem", cmd))
            return b"fee7"
        def breakpoint(sock, cmd):
            events.append(("z0", cmd))
            return b"OK"
        with patch.object(thumb, "request", side_effect=self.fake_request(events)), \
             patch.object(thumb, "thumb_memory", side_effect=mem), \
             patch.object(thumb, "thumb_breakpoint", side_effect=breakpoint):
            result = thumb.thumb_roundtrip(object())
        self.assertEqual(result, ("S02", 16, b"fee7", "S02"))
        self.assertEqual(events, [
            ("read", b"?"), ("read", b"g"), ("read", b"m080000c0,4"),
            ("mem", thumb.THUMB_READ),
            ("z0", thumb.THUMB_SET), ("z0", thumb.THUMB_REMOVE),
            ("read", b"?"),
        ])

    def test_bad_preflight_never_sends_breakpoint(self):
        for which in ("stop", "regs", "arm"):
            events = []
            data = {"stop": b"S02", "regs": b"00" * 68, "arm": b"00009fe5"}
            data[which] = {"stop": b"OK", "regs": b"00" * 63,
                           "arm": b"00000000"}[which]
            with self.subTest(which=which):
                with patch.object(thumb, "request",
                                  side_effect=self.fake_request(events, **data)), \
                     patch.object(thumb, "thumb_breakpoint") as bp, \
                     patch.object(thumb, "thumb_memory") as mem:
                    with self.assertRaises(RuntimeError):
                        thumb.thumb_roundtrip(object())
                    bp.assert_not_called()
                    mem.assert_not_called()

    def test_install_error_still_triggers_exactly_one_removal(self):
        events = []
        def breakpoint(sock, command):
            events.append(command)
            if command == thumb.THUMB_SET:
                raise socket.timeout("ACK missing")
            return b"OK"
        with patch.object(thumb, "request", side_effect=self.fake_request([])), \
             patch.object(thumb, "thumb_memory", return_value=b"fee7"), \
             patch.object(thumb, "thumb_breakpoint", side_effect=breakpoint):
            with self.assertRaises(socket.timeout):
                thumb.thumb_roundtrip(object())
        self.assertEqual(events, [thumb.THUMB_SET, thumb.THUMB_REMOVE])

    def test_removal_error_must_not_be_reported_as_success(self):
        events = []
        def breakpoint(sock, command):
            events.append(command)
            if command == thumb.THUMB_REMOVE:
                raise RuntimeError("remove reply missing")
            return b"OK"
        with patch.object(thumb, "request", side_effect=self.fake_request([])), \
             patch.object(thumb, "thumb_memory", return_value=b"fee7"), \
             patch.object(thumb, "thumb_breakpoint", side_effect=breakpoint):
            with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
                thumb.thumb_roundtrip(object())
        self.assertEqual(events, [thumb.THUMB_SET, thumb.THUMB_REMOVE])

    def test_stale_ok_after_remove_is_not_valid_cpu_stop(self):
        events = []
        with patch.object(thumb, "request",
                          side_effect=self.fake_request(events, after=b"OK")), \
             patch.object(thumb, "thumb_memory", return_value=b"fee7"), \
             patch.object(thumb, "thumb_breakpoint", return_value=b"OK"):
            with self.assertRaises(ValueError):
                thumb.thumb_roundtrip(object())

    def test_private_input_guard_rejects_flag_and_extra_argv_before_launch(self):
        with patch.object(thumb.sys, "argv", ["thumb_fixture", "--rom=x.gba"]), \
             patch.object(thumb, "inspect_network") as inspect, \
             patch.object(thumb.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(RuntimeError, "private input"):
                thumb.run()
            inspect.assert_not_called()
            popen.assert_not_called()
        with patch.object(thumb.sys, "argv", ["thumb_fixture"]), \
             patch.dict(os.environ, {"SOULGOLD_ALLOW_PRIVATE_INPUTS": "1"}), \
             patch.object(thumb, "inspect_network") as inspect, \
             patch.object(thumb.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(RuntimeError, "private input"):
                thumb.run()
            inspect.assert_not_called()
            popen.assert_not_called()

    def test_run_prelaunch_gate_precedes_emulator(self):
        with patch.object(thumb.sys, "argv", ["thumb_fixture"]), \
             patch.object(thumb, "inspect_network", side_effect=RuntimeError("unsafe")) as inspect, \
             patch.object(thumb, "check_no_egress") as egress, \
             patch.object(thumb.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(RuntimeError, "unsafe"):
                thumb.run()
            inspect.assert_called_once()
            egress.assert_not_called()
            popen.assert_not_called()

    def test_run_real_sequence_is_isolation_launch_roundtrip_postcheck(self):
        events = []
        fake_process = MagicMock()
        fake_process.poll.return_value = None
        fake_process.wait.return_value = 0
        fake_sock = MagicMock()
        fake_sock.__enter__.return_value = fake_sock
        def inspect(*args, **kwargs):
            events.append(("inspect", bool(kwargs.get("require_listener"))))
            return ("v4:0.0.0.0",) if kwargs.get("require_listener") else ()
        def egress(*args, **kwargs):
            events.append(("egress",))
        def popen(*args, **kwargs):
            events.append(("launch",))
            return fake_process
        def connect(*args, **kwargs):
            events.append(("connect",))
            return fake_sock
        def roundtrip(_sock):
            events.append(("roundtrip",))
            return ("S02", 16, b"fee7", "S02")
        with patch.object(thumb.sys, "argv", ["thumb_fixture"]), \
             patch.object(thumb, "inspect_network", side_effect=inspect), \
             patch.object(thumb, "check_no_egress", side_effect=egress), \
             patch.object(thumb.subprocess, "Popen", side_effect=popen), \
             patch.object(thumb.socket, "create_connection", side_effect=connect), \
             patch.object(thumb, "thumb_roundtrip", side_effect=roundtrip), \
             patch("builtins.print"):
            thumb.run()
        self.assertEqual(events, [
            ("inspect", False), ("egress",), ("launch",), ("connect",),
            ("inspect", True), ("egress",), ("roundtrip",),
        ])
        fake_process.terminate.assert_called_once()
        fake_process.wait.assert_called_once()


    def test_arm_opcode_constants_independently_pinned(self):
        # Literal comparison catches a change to BOTH producer and constant.
        self.assertEqual(thumb.ARM_LDR, bytes.fromhex("00009fe5"))
        self.assertEqual(thumb.ARM_BX, bytes.fromhex("10ff2fe1"))
        self.assertEqual(thumb.THUMB_LOOP, bytes.fromhex("fee7"))

    def test_emulator_child_receives_only_allowlisted_environment(self):
        allowed = {"PATH", "DISPLAY", "XAUTHORITY", "HOME", "SDL_AUDIODRIVER"}
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.wait.return_value = 0
        mock_socket = MagicMock()
        mock_socket.__enter__.return_value = mock_socket
        captured = []
        def launch(*args, **kwargs):
            captured.append(dict(kwargs["env"]))
            return mock_process
        with patch.object(thumb.sys, "argv", ["thumb_fixture"]), \
             patch.dict(os.environ, {"SOULGOLD_TEST_SENTINEL": "MUST_NOT_PASS"}, clear=False), \
             patch.object(thumb, "inspect_network", return_value=("v4:0.0.0.0",)), \
             patch.object(thumb, "check_no_egress"), \
             patch.object(thumb.subprocess, "Popen", side_effect=launch), \
             patch.object(thumb.socket, "create_connection", return_value=mock_socket), \
             patch.object(thumb, "thumb_roundtrip", return_value=("S02", 16, b"fee7", "S02")), \
             patch("builtins.print"):
            thumb.run()
        self.assertEqual(len(captured), 1)
        self.assertFalse(set(captured[0]) - allowed, "unexpected child environment keys")
        self.assertNotIn("SOULGOLD_TEST_SENTINEL", captured[0])
        self.assertEqual(captured[0]["SDL_AUDIODRIVER"], "dummy")


if __name__ == "__main__":
    unittest.main()
