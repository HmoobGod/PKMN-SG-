#!/usr/bin/env python3
"""Public-fixture combined parser and post-cleanup safety checks."""
import socket
import unittest
from unittest.mock import patch

import cloud_rsp_combined_fixture as lab
from pr26_exact_probe_parser_reference import parse_registers, parse_stop

class CombinedPublicFixtureTests(unittest.TestCase):
    def test_original_pr26_parser_accepts_actual_public_reply_grammar(self):
        self.assertEqual(parse_stop(b"S02"), "S02")
        self.assertEqual(len(parse_registers(b"00"*68)),16)

    def test_original_pr26_parser_denies_short_or_unparseable_payload(self):
        for raw in (b"00"*63,b"xx"*68):
            with self.subTest(raw=raw[:8]):
                with self.assertRaises(ValueError):
                    parse_registers(raw)
        with self.assertRaises(ValueError):
            parse_stop(b"OK")

    def test_stale_ok_cannot_certify_post_removal_stop(self):
        with patch.object(lab,"request",return_value=b"OK"):
            with self.assertRaises(ValueError):
                lab.verified_post_cleanup_stop(object())

    def test_valid_post_removal_stop(self):
        with patch.object(lab,"request",return_value=b"S02") as read:
            self.assertEqual(lab.verified_post_cleanup_stop(object()),"S02")
            self.assertEqual(read.call_args.args[1],b"?")

    def test_network_interface_failure_precedes_emulator_creation(self):
        with patch.object(lab,"inspect_network",side_effect=lab.IsolationError("bad interfaces")), \
             patch.object(lab.subprocess,"Popen") as popen, \
             patch.object(lab,"check_no_egress") as egress, \
             patch.object(lab.sys,"argv",["fixture"]):
            with self.assertRaisesRegex(lab.IsolationError,"bad interfaces"):
                lab.run()
            popen.assert_not_called()
            egress.assert_not_called()

    def test_egress_failure_precedes_emulator_creation(self):
        with patch.object(lab,"inspect_network",return_value=()), \
             patch.object(lab,"check_no_egress",side_effect=lab.IsolationError("egress reachable")), \
             patch.object(lab.subprocess,"Popen") as popen, \
             patch.object(lab.sys,"argv",["fixture"]):
            with self.assertRaisesRegex(lab.IsolationError,"egress reachable"):
                lab.run()
            popen.assert_not_called()

    def test_private_input_args_fail_before_preflight(self):
        with patch.object(lab.sys,"argv",["fixture","/tmp/some-private.gba"]), \
             patch.object(lab,"inspect_network") as guard, \
             patch.object(lab.subprocess,"Popen") as popen:
            with self.assertRaisesRegex(RuntimeError,"no private ROM"):
                lab.run()
            guard.assert_not_called()
            popen.assert_not_called()

if __name__=="__main__":
    unittest.main()
