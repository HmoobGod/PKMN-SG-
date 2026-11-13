#!/usr/bin/env python3
"""Tests for mGBA 0.10.5 source-backed qSupported fixture-only stop negotiation."""
import unittest
from unittest.mock import MagicMock, patch

import cloud_rsp_thumb_hit_fixture as hit
import cloud_rsp_thumb_qsupported_fixture as negotiated
from cloud_rsp_thumb2_fixture import THUMB_READ, THUMB_SET, THUMB_REMOVE
from pr26_exact_probe_parser_reference import parse_stop


def regs(pc=0x08000100):
    words = [0] * 15 + [pc] + [0x20]
    return b"".join(value.to_bytes(4, "little") for value in words).hex().encode("ascii")


class PublicNegotiatedStopTests(unittest.TestCase):
    def test_exact_literal_qsupported_request_and_capability_reply(self):
        sock = MagicMock()
        with patch.object(hit, "recv_rsp", return_value=hit.PUBLIC_QSUPPORTED_REPLY) as recv:
            hit.negotiate_public_breakpoint_details(sock)
        sock.sendall.assert_called_once_with(hit.encode_rsp(b"qSupported:swbreak+;hwbreak+"))
        recv.assert_called_once_with(sock)

    def test_capability_response_is_literal_and_not_self_referential(self):
        # Pin the upstream mGBA 0.10.5 string independently of production.
        self.assertEqual(hit.PUBLIC_QSUPPORTED, b"qSupported:swbreak+;hwbreak+")
        self.assertEqual(
            hit.PUBLIC_QSUPPORTED_REPLY,
            b"swbreak+;hwbreak+;qXfer:features:read+;"
            b"qXfer:memory-map:read+;QStartNoAckMode+",
        )

    def test_main_forwards_opt_in_and_prints_negotiated_evidence_only_then(self):
        # Main integration, not just run_one_hit: fail if the mode is silently
        # ignored or if default output misleadingly claims negotiated T05.
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                proc = MagicMock()
                proc.poll.return_value = None
                proc.wait.return_value = 0
                peer = MagicMock()
                peer.__enter__.return_value = peer
                result = ((0x08000100, "T05hwbreak:;", False) if enabled
                          else (0x08000100, "S05k", True))
                with patch.object(hit.sys, "argv", ["public-fixture"]), \
                     patch.object(hit, "inspect_network", return_value=("v4:127.0.0.1",)), \
                     patch.object(hit, "check_no_egress"), \
                     patch.object(hit.subprocess, "Popen", return_value=proc), \
                     patch.object(hit.socket, "create_connection", return_value=peer), \
                     patch.object(hit, "run_one_hit", return_value=result) as runner, \
                     patch("builtins.print") as printed:
                    hit.main(negotiated_public=enabled)
                if enabled:
                    runner.assert_called_once_with(peer, negotiated_public=True)
                else:
                    runner.assert_called_once_with(peer)
                text = "\n".join(str(call.args[0]) for call in printed.call_args_list)
                self.assertEqual(
                    "PR26_STRICT_STOP_GRAMMAR: T05hwbreak:;" in text, enabled
                )
                self.assertEqual("MGBA_0105_QSUPPORTED_PROFILE:" in text, enabled)
                self.assertEqual("EVIDENCE_ONLY:" in text, not enabled)
                proc.terminate.assert_called_once()
                proc.wait.assert_called_once_with(timeout=3)

    def test_reject_missing_or_unexpected_capability_before_breakpoint(self):
        for reply in (b"", b"swbreak+;hwbreak-", b"swbreak+",
                      b"swbreak+;hwbreak+;UNEXPECTED", b"OK"):
            with self.subTest(reply=reply):
                sock = MagicMock()
                with patch.object(hit, "recv_rsp", return_value=reply):
                    with self.assertRaisesRegex(hit.HitError, "capability negotiation mismatch"):
                        hit.negotiate_public_breakpoint_details(sock)
                sock.sendall.assert_called_once_with(
                    hit.encode_rsp(b"qSupported:swbreak+;hwbreak+")
                )

    def scripted(self, *, reply=b"T05hwbreak:;"):
        events = []
        responses = [b"S02", regs(0x080000c0), b"00009fe5", regs()]
        def negotiate(sock):
            events.append(("q", hit.PUBLIC_QSUPPORTED))
        def request(sock, command):
            events.append(("read", command))
            return responses.pop(0)
        def memory(sock, command):
            events.append(("mem", command))
            return b"fee7"
        def breakpoint(sock, command):
            events.append(("bp", command))
            return b"OK"
        def cont(sock, command):
            events.append(("c", command))
            return reply
        return events, negotiate, request, memory, breakpoint, cont

    def test_qsupported_precedes_all_preflight_and_strict_T05_proves_hit(self):
        events, negotiate, request, memory, breakpoint, cont = self.scripted()
        with patch.object(hit, "negotiate_public_breakpoint_details", side_effect=negotiate), \
             patch.object(hit, "request", side_effect=request), \
             patch.object(hit, "thumb_memory", side_effect=memory), \
             patch.object(hit, "thumb_breakpoint", side_effect=breakpoint), \
             patch.object(hit, "one_continue", side_effect=cont):
            pc, stop, nonstandard = hit.run_one_hit(object(), negotiated_public=True)
        self.assertEqual((pc, stop, nonstandard), (0x08000100, "T05hwbreak:;", False))
        self.assertEqual(events, [
            ("q", hit.PUBLIC_QSUPPORTED), ("read", b"?"), ("read", b"g"),
            ("read", b"m080000c0,4"), ("mem", THUMB_READ),
            ("bp", THUMB_SET), ("c", b"c"), ("read", b"g"), ("bp", THUMB_REMOVE),
        ])

    def test_negotiated_S05k_is_not_promoted_to_strict_stop(self):
        events, negotiate, request, memory, breakpoint, cont = self.scripted(reply=b"S05k")
        with patch.object(hit, "negotiate_public_breakpoint_details", side_effect=negotiate), \
             patch.object(hit, "request", side_effect=request), \
             patch.object(hit, "thumb_memory", side_effect=memory), \
             patch.object(hit, "thumb_breakpoint", side_effect=breakpoint), \
             patch.object(hit, "one_continue", side_effect=cont):
            with self.assertRaisesRegex(hit.HitError, "not exact T05hwbreak"):
                hit.run_one_hit(object(), negotiated_public=True)
        self.assertEqual([e for e in events if e[0] == "bp"], [("bp", THUMB_SET)])
        self.assertEqual([e for e in events if e[0] == "c"], [("c", b"c")])
        self.assertNotIn(("bp", THUMB_REMOVE), events)

    def test_any_unexpected_T05_payload_fails_closed_in_negotiated_mode(self):
        for bad in (b"T05", b"T05swbreak:;", b"T05hwbreak:;junk", b"S05"):
            with self.subTest(reply=bad):
                events, negotiate, request, memory, breakpoint, cont = self.scripted(reply=bad)
                with patch.object(hit, "negotiate_public_breakpoint_details", side_effect=negotiate), \
                     patch.object(hit, "request", side_effect=request), \
                     patch.object(hit, "thumb_memory", side_effect=memory), \
                     patch.object(hit, "thumb_breakpoint", side_effect=breakpoint), \
                     patch.object(hit, "one_continue", side_effect=cont):
                    with self.assertRaises(hit.HitError):
                        hit.run_one_hit(object(), negotiated_public=True)
                self.assertEqual([e for e in events if e[0] == "c"], [("c", b"c")])

    def test_pr26_strict_parser_unchanged_and_T05_accepted(self):
        self.assertEqual(parse_stop(b"T05hwbreak:;"), "T05hwbreak:;")
        with self.assertRaises(ValueError):
            parse_stop(b"S05k")
        with self.assertRaises(ValueError):
            parse_stop(b"S05kk")

    def test_public_wrapper_sets_negotiation_without_new_cli_options(self):
        with patch.object(negotiated, "main") as main:
            negotiated.run()
        main.assert_called_once_with(negotiated_public=True)


if __name__ == "__main__":
    unittest.main()
