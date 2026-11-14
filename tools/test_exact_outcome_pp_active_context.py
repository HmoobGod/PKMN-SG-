#!/usr/bin/env python3
"""Synthetic original outcome/PP actor0-context attribution negatives.

This calls public audit() only, never attest() and never opens private ROM,
save, trace, emulator or commercial game data.
"""
import copy
import unittest

import verify_exact_outcome_pp_edges as v
from test_exact_outcome_pp_edges import fixture, row


def qualified():
    d=fixture()
    # Historical player0 emitter marker packs foe battler 1 and move slot 0.
    d["events"][0]["r3"]=256
    return d


def pp_result(d):
    r=v.audit(d)
    assert r["full_native_terminal_certified"] is False
    assert r["one_use_request_ownership_certified"] is False
    assert r["production_promotion_authorized"] is False
    return r


def main_edge(step,before,after):
    return row(2,step,0x081C1234,address=v.MAIN+0x439,
               before=before,after=after,inbattle=after)


class OutcomePpActor0ContextTests(unittest.TestCase):
    def test_live_original_actor0_marker_is_candidate_not_certification(self):
        r=pp_result(qualified())
        self.assertEqual(r["original_pp_writer_single_byte_debits_seen"],1)
        self.assertEqual(r["contextual_actor0_pp_writer_candidates_unverified"],1)
        self.assertFalse(r["effective_move_restrictions_certified"])
        self.assertFalse(r["original_battle_outcome_decision_pc_certified"])

    def test_raw_pp_writer_without_well_formed_actor0_marker_not_attributed(self):
        for mutant in (
            lambda d:d["events"][0].update(r3=0),
            lambda d:d["events"][0].update(r3=512),
            lambda d:d["events"][0].update(flags=0),
            lambda d:d["events"][0].update(battlers=0),
            lambda d:d["events"][0].update(inbattle=0),
            lambda d:d["events"].pop(0),
        ):
            with self.subTest(mutant=str(mutant)):
                d=qualified()
                mutant(d)
                result=pp_result(d)
                self.assertEqual(result["original_pp_writer_single_byte_debits_seen"],1)
                self.assertEqual(result["contextual_actor0_pp_writer_candidates_unverified"],0)

    def test_raw_pp_writer_outside_live_wild_context_not_attributed(self):
        for delta in (dict(flags=0),dict(battlers=0),dict(inbattle=0)):
            with self.subTest(context=delta):
                d=qualified()
                d["events"][2].update(delta)
                result=pp_result(d)
                self.assertEqual(result["original_pp_writer_single_byte_debits_seen"],1)
                self.assertEqual(result["contextual_actor0_pp_writer_candidates_unverified"],0)

    def test_main_clear_retires_old_actor0_candidate_even_if_flags_stale(self):
        d=qualified()
        writer=d["events"].pop(2)
        d["events"].insert(2,main_edge(10,2,0))
        writer.update(step=12,frame=3983)
        d["events"].insert(3,writer)
        r=pp_result(d)
        self.assertEqual(r["original_pp_writer_single_byte_debits_seen"],1)
        self.assertEqual(r["contextual_actor0_pp_writer_candidates_unverified"],0)

    def test_main_clear_reentry_never_resuscitates_old_actor0(self):
        d=qualified()
        writer=d["events"].pop(2)
        d["events"][2:2]=[main_edge(10,2,0),main_edge(11,0,2)]
        writer.update(step=12,frame=3983)
        d["events"].insert(4,writer)
        r=pp_result(d)
        self.assertEqual(r["original_pp_writer_single_byte_debits_seen"],1)
        self.assertEqual(r["contextual_actor0_pp_writer_candidates_unverified"],0)

    def test_new_original_actor0_emitter_after_reentry_can_be_new_candidate(self):
        d=qualified()
        writer=d["events"].pop(2)
        new_emitter=row(6,12,0x0806BD80,r0=0,r2=10,r3=256)
        d["events"][2:2]=[main_edge(10,2,0),main_edge(11,0,2),
                         new_emitter]
        writer.update(step=14,frame=3983)
        d["events"].insert(5,writer)
        r=pp_result(d)
        self.assertEqual(r["original_player_emit_markers"],2)
        self.assertEqual(r["original_pp_writer_single_byte_debits_seen"],1)
        self.assertEqual(r["contextual_actor0_pp_writer_candidates_unverified"],1)
        self.assertFalse(r["one_use_request_ownership_certified"])

    def test_main_bit0_only_noise_does_not_close_candidate(self):
        d=qualified()
        d["events"].insert(2,main_edge(10,2,3))
        r=pp_result(d)
        self.assertEqual(r["contextual_actor0_pp_writer_candidates_unverified"],1)

    def test_wrong_slot_or_non_debit_is_not_candidate(self):
        d=qualified()
        d["events"][2].update(slot=1,address=v.PP+1,r1=v.PP+1)
        r=pp_result(d)
        self.assertEqual(r["original_pp_writer_single_byte_debits_seen"],1)
        self.assertEqual(r["contextual_actor0_pp_writer_candidates_unverified"],0)

        d=qualified()
        d["events"][2]["after"]=21  # a non-debit, even at original writer PC
        r=pp_result(d)
        self.assertEqual(r["original_pp_writer_single_byte_debits_seen"],0)
        self.assertEqual(r["contextual_actor0_pp_writer_candidates_unverified"],0)


if __name__=="__main__":
    unittest.main()
