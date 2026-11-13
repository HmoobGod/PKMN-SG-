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

    def test_strict_pre_c_public_startup_sentinel(self):
        runner.validate_generated_preflight("S02", 0, b"00009fe5", b"fee7")
        for status, pc, arm, thumb in (
            ("S05", 0, b"00009fe5", b"fee7"),
            ("T05hwbreak:;", 0, b"00009fe5", b"fee7"),
            ("S02", 0x080000C0, b"00009fe5", b"fee7"),
            ("S02", True, b"00009fe5", b"fee7"),
            ("S02", 0, b"ffffffff", b"fee7"),
            ("S02", 0, b"00009fe5", b"0000"),
            ("S02", 0, b"00009fe5", "fee7"),
        ):
            with self.subTest(status=status, pc=pc, arm=arm, thumb=thumb):
                with self.assertRaisesRegex(RuntimeError, "generated public pre-c"):
                    runner.validate_generated_preflight(status, pc, arm, thumb)

    def test_read_preflight_failure_has_no_z0_or_continue(self):
        import inspect
        run_source = inspect.getsource(runner.run)
        self.assertLess(
            run_source.index("read_verified_generated_preflight(sock, rsp)"),
            run_source.index('fixed_public_request(sock, rsp, b"Z0,08000100,2")'),
        )
        for bad_stop, pc in ((b"S05", 0), (b"S02", 0x080000C0)):
            with self.subTest(status=bad_stop, pc=pc):
                rsp, sock = MagicMock(), MagicMock()
                values = [0] * 15 + [pc]
                regdata = b"".join(x.to_bytes(4, "little") for x in values).hex().encode()
                rsp.send.side_effect = [bad_stop, regdata]
                with patch.object(runner, "fixed_public_request",
                                  side_effect=[b"00009fe5", b"fee7"]) as requests:
                    with self.assertRaisesRegex(RuntimeError, "generated public pre-c"):
                        runner.read_verified_generated_preflight(sock, rsp)
                self.assertEqual(
                    [c.args[2] for c in requests.call_args_list],
                    [b"m080000c0,4", b"m08000100,2"],
                )
                self.assertNotIn(b"Z0,08000100,2",
                                 b"".join(c.args[2] for c in requests.call_args_list))
                self.assertNotIn("c", [c.args[0] for c in rsp.send.call_args_list])

    def test_generated_cleanup_requires_exact_observed_s02(self):
        runner.validate_generated_post_cleanup("S02")
        for bad in ("S05", "T05hwbreak:;", "S02k", "", 2, None):
            with self.subTest(status=bad):
                with self.assertRaisesRegex(RuntimeError, "post-z0 stop"):
                    runner.validate_generated_post_cleanup(bad)

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
        sock.sendall.assert_called_once_with(b"$Z0,08000100,2#9d")
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
