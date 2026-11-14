#!/usr/bin/env python3
"""Generated fake original CPU event sequence; NO commercial ROM or emulator."""
import copy
import unittest
import triage_original_terminal_return_order as tool
from test_exact_outcome_pp_edges import fixture,row
from verify_exact_outcome_pp_edges import MAIN

CANDIDATE=0x02004020

def synthetic():
    d=fixture()
    d["candidate_outcome_byte_address"]=CANDIDATE
    d["events"].insert(3,row(1,15,0x08101234,CANDIDATE,0,1,
                r1=CANDIDATE,r6=1,opcode=0x700E))
    a=d["events"][5] # callback1, after insertion
    b=d["events"][6] # callback2
    a.update(opcode=0x6001,r0=MAIN,r1=a["after"])
    b.update(opcode=0x6001,r0=MAIN+4,r1=b["after"])
    return d

class OriginalTerminalOrderTests(unittest.TestCase):
    def test_synthetic_full_order_only_candidate_not_native(self):
        d=synthetic();out=tool.triage(d)
        self.assertEqual(out["main_inbattle_clear_segments_unverified"],1)
        self.assertEqual(out["ordered_result_main_callback1_callback2_sequences_unverified"],1)
        self.assertEqual(out["missing_ambiguous_or_out_of_order_segments"],0)
        self.assertFalse(out["original_outcome_decision_pc_certified"])
        self.assertFalse(out["original_overworld_callback_return_certified"])
        self.assertFalse(out["production_authorized"])
        self.assertEqual(out["original_gameplay_acceptance_scenarios"],0)
    def test_old_fixture_has_no_result_or_word_store_provenance(self):
        z=tool.triage(fixture())
        self.assertEqual(z["ordered_result_main_callback1_callback2_sequences_unverified"],0)
        self.assertEqual(z["main_inbattle_clear_segments_unverified"],1)
        self.assertFalse(z["full_original_native_terminal_certified"])
    def test_nonstore_result_cannot_qualify(self):
        d=synthetic();d["events"][3]["opcode"]=0x780E
        self.assertEqual(tool.triage(d)["ordered_result_main_callback1_callback2_sequences_unverified"],0)
    def test_candidate_result_after_main_clear_is_not_retrospective(self):
        d=synthetic()
        d["events"][3]["step"]=22
        d["events"][3]["frame"]=3980+22//4
        d["events"].sort(key=lambda x:x["step"])
        self.assertEqual(tool.triage(d)["ordered_result_main_callback1_callback2_sequences_unverified"],0)
    def test_callback1_and_callback2_order_must_match(self):
        d=synthetic()
        a,b=d["events"][-2:]
        a["step"],b["step"]=b["step"],a["step"]
        a["frame"],b["frame"]=b["frame"],a["frame"]
        d["events"].sort(key=lambda x:x["step"])
        self.assertEqual(tool.triage(d)["ordered_result_main_callback1_callback2_sequences_unverified"],0)
    def test_callback_word_source_mismatch_fail_closed(self):
        d=synthetic()
        d["events"][5]["r1"]^=4
        self.assertEqual(tool.triage(d)["ordered_result_main_callback1_callback2_sequences_unverified"],0)
    def test_second_callback1_transition_is_ambiguous(self):
        d=synthetic()
        first=d["events"][5]
        extra=copy.deepcopy(first)
        extra.update(step=25,frame=3980+25//4,before=first["after"],
                     after=0x081C7591,callback1=0x081C7591,r1=0x081C7591)
        d["events"].insert(6,extra)
        self.assertEqual(tool.triage(d)["ordered_result_main_callback1_callback2_sequences_unverified"],0)
    def test_manual_marker_breaks_return_sequence(self):
        d=synthetic()
        d["events"].insert(5,row(8,23,0x0806449C))
        self.assertEqual(tool.triage(d)["ordered_result_main_callback1_callback2_sequences_unverified"],0)
    def test_battle_resumed_breaks_callback_attribution(self):
        d=synthetic()
        d["events"].insert(5,row(2,23,0x081D0000,MAIN+0x439,0,2,inbattle=2))
        self.assertEqual(tool.triage(d)["ordered_result_main_callback1_callback2_sequences_unverified"],0)
    def test_manual_marker_before_main_clear_invalidates_stale_result(self):
        d=synthetic()
        d["events"].insert(4,row(8,18,0x0806449C))
        z=tool.triage(d)
        self.assertEqual(z["manual_cpu_barrier_steps_seen"],1)
        self.assertEqual(z["ordered_result_main_callback1_callback2_sequences_unverified"],0)
        self.assertEqual(z["segments"][0]["prior_result_steps"],[])
        self.assertFalse(z["original_overworld_callback_return_certified"])

    def test_manual_same_step_as_result_disallows_any_order(self):
        d=synthetic()
        m=row(8,15,0x08101234,opcode=0x700E,r1=CANDIDATE,r6=1)
        # Exact original PC check on kind8 forces its PC to 0x0806449C,
        # so same-step CPU parity only permits a matching PC. Model the
        # same instruction's result watcher instead of forging CPU metadata.
        m["pc"]=0x0806449C
        r=d["events"][3]
        r["pc"]=0x0806449C
        d["events"].insert(4,m)
        z=tool.triage(d)
        self.assertEqual(z["manual_cpu_barrier_steps_seen"],1)
        self.assertEqual(z["ordered_result_main_callback1_callback2_sequences_unverified"],0)
        d["events"][3],d["events"][4]=d["events"][4],d["events"][3]
        z=tool.triage(d)
        self.assertEqual(z["ordered_result_main_callback1_callback2_sequences_unverified"],0)

    def test_second_unattributed_result_transition_denies_sole_writer(self):
        d=synthetic()
        other=row(1,17,0x08105540,CANDIDATE,1,2,
                  r1=CANDIDATE,r6=2,opcode=0x780E)
        d["events"].insert(4,other)
        z=tool.triage(d)
        self.assertEqual(z["segments"][0]["prior_result_transition_steps"],[15,17])
        self.assertEqual(z["ordered_result_main_callback1_callback2_sequences_unverified"],0)

    def test_new_result_change_during_callbacks_aborts_return_hypothesis(self):
        d=synthetic()
        d["events"].insert(6,row(1,25,0x08105540,CANDIDATE,1,2,
                                 r1=CANDIDATE,r6=2,opcode=0x780E))
        z=tool.triage(d)
        self.assertEqual(z["segments"][0]["closed_by"],
                         "new_result_transition_after_main_clear")
        self.assertEqual(z["ordered_result_main_callback1_callback2_sequences_unverified"],0)
        self.assertFalse(z["full_original_native_terminal_certified"])

    def test_malformed_original_cpu_snapshot_denied_by_parent_audit(self):
        d=synthetic()
        d["events"][3]["opcode"]=True
        with self.assertRaises(ValueError):
            tool.triage(d)
    def test_unsupported_callback_pointer_is_not_promoted(self):
        d=synthetic()
        d["events"][5].update(after=0x02004001,callback1=0x02004001,r1=0x02004001)
        self.assertEqual(tool.triage(d)["ordered_result_main_callback1_callback2_sequences_unverified"],0)

if __name__=="__main__":
    unittest.main()
