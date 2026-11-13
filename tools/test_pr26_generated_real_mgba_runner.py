#!/usr/bin/env python3
"""Generated-ROM-only source guards; these tests do not launch mGBA."""
import hashlib
import unittest
from unittest.mock import MagicMock, patch

import pr26_generated_real_mgba_runner as runner


class PublicRealSocketFixtureTests(unittest.TestCase):
    def test_exact_generated_rom_identity_and_bytes(self):
        rom = runner.generated_thumb_rom()
        self.assertEqual(len(rom), 32768)
        self.assertEqual(
            hashlib.sha256(rom).hexdigest(),
            "cfa20bc9ccad2131abeedaed0d1d5aa49425f8bce5616370d0b6659c7cd4804b",
        )
        self.assertEqual(rom[0xC0:0xC4], bytes.fromhex("00009fe5"))
        self.assertEqual(rom[0x100:0x102], bytes.fromhex("fee7"))
        self.assertNotIn(b"Pokemon Soulgold", rom)

    def test_only_four_exact_public_raw_commands(self):
        self.assertEqual(runner.ALLOWED_PUBLIC_RAW,
                         frozenset({b"m080000c0,4", b"m08000100,2",
                                    b"Z0,08000100,2", b"z0,08000100,2"}))
        sock, rsp = MagicMock(), MagicMock()
        rsp._features_negotiated = True
        rsp._feature_negotiation_failed = False
        rsp.running = False
        rsp.receive.return_value = b"OK"
        self.assertEqual(runner.fixed_public_request(sock, rsp, b"Z0,08000100,2"), b"OK")
        sock.sendall.assert_called_once_with(b"$Z0,08000100,2#86")
        rsp.receive.assert_called_once_with()
        for command in (b"Z0,0806b370,2", b"z0,080000c0,2", b"c",
                        b"s", b"G000", b"M02000000,2:00", b"m02000000,2",
                        b"qSupported:swbreak+;hwbreak+", "", b""):
            with self.subTest(command=command):
                with self.assertRaisesRegex(ValueError, "only exact"):
                    runner.fixed_public_request(sock, rsp, command)

    def test_cannot_issue_public_raw_without_features_or_when_running(self):
        for fields in (
            dict(_features_negotiated=False, _feature_negotiation_failed=False, running=False),
            dict(_features_negotiated=True, _feature_negotiation_failed=True, running=False),
            dict(_features_negotiated=True, _feature_negotiation_failed=False, running=True),
        ):
            with self.subTest(fields=fields):
                rsp, sock = MagicMock(), MagicMock()
                for key, value in fields.items():
                    setattr(rsp, key, value)
                with self.assertRaisesRegex(ValueError, "stopped negotiated"):
                    runner.fixed_public_request(sock, rsp, b"Z0,08000100,2")
                sock.sendall.assert_not_called()

    def test_reject_private_path_args_or_private_input_switch_before_preflight(self):
        with patch.object(runner.sys, "argv", ["fixture", "--rom", "/private/game.gba"]), \
             patch.dict(runner.os.environ, {}, clear=True), \
             patch.object(runner, "inspect_network") as inspect:
            with self.assertRaisesRegex(RuntimeError, "forbids private"):
                runner.run()
            inspect.assert_not_called()
        with patch.object(runner.sys, "argv", ["fixture"]), \
             patch.dict(runner.os.environ, {"SOULGOLD_ALLOW_PRIVATE_INPUTS": "1"}, clear=True), \
             patch.object(runner, "inspect_network") as inspect:
            with self.assertRaisesRegex(RuntimeError, "forbids private"):
                runner.run()
            inspect.assert_not_called()

    def test_prelaunch_network_failure_never_starts_emulator(self):
        with patch.object(runner.sys, "argv", ["fixture"]), \
             patch.dict(runner.os.environ, {}, clear=True), \
             patch.object(runner, "inspect_network", side_effect=RuntimeError("blocked")), \
             patch.object(runner.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(RuntimeError, "blocked"):
                runner.run()
            popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
