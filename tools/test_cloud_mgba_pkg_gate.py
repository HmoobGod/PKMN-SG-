#!/usr/bin/env python3
"""Fail-closed independent tests for exact dpkg Version, no substring acceptance."""
import subprocess
import unittest
from unittest.mock import patch
import cloud_mgba_pkg_gate as gate


class ExactMGBAVersionTests(unittest.TestCase):
    def test_expected_full_version_exact_only(self):
        self.assertEqual(gate.require_version("0.10.5+dfsg-3build1"),
                         "0.10.5+dfsg-3build1")

    def test_substrings_never_pass(self):
        for value in (
            "0.10.5", "0.10.5+dfsg-3build12", "0.10.5+dfsg-3build1\nanother",
            "mgba-sdl 0.10.5+dfsg-3build1", "0.10.5+dfsg-3build1-extra",
            "0.10.6+dfsg-3build1", "1:0.10.5+dfsg-3build1", "",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(RuntimeError, "mismatch"):
                    gate.require_version(value)

    def test_dpkg_version_field_exact_query(self):
        with patch.object(gate.subprocess, "check_output",
                          return_value="0.10.5+dfsg-3build1") as check:
            self.assertEqual(gate.verify_package_version(),
                             "0.10.5+dfsg-3build1")
        check.assert_called_once_with(
            ["dpkg-query", "-W", "-f=${Version}", "mgba-sdl"],
            text=True, timeout=6,
        )

    def test_failed_dpkg_query_is_not_accepted(self):
        with patch.object(gate.subprocess, "check_output",
                          side_effect=subprocess.CalledProcessError(1, "dpkg-query")):
            with self.assertRaises(subprocess.CalledProcessError):
                gate.verify_package_version()

    def test_argv_rejected(self):
        with patch.object(gate.sys, "argv", ["verify", "/tmp/private.gba"]), \
             patch.object(gate, "verify_package_version") as verify:
            with self.assertRaisesRegex(RuntimeError, "does not accept"):
                gate.main()
            verify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
