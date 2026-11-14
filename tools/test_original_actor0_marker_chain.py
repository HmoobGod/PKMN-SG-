#!/usr/bin/env python3
"""Public synthetic event-chain mutations only: no original game or ROM."""
import copy
import unittest
import triage_original_actor0_marker_chain as tool
from test_exact_outcome_pp_edges import fixture, row
from verify_exact_outcome_pp_edges import PP, MAIN

def synthetic():
    d = fixture()
    stages = [
        row(13, 4, 0x08094330),      # original validator PC
        row(14, 5, 0x0809435C),      # original slot commit PC
        row(15, 6, 0x08094374),      # original move commit PC
        row(16, 7, 0x08094380),      # original target commit PC
        row(12, 9, 0x0806261C, r0=0),  # controller completion
    ]
    d["events"].extend(stages)
    d["events"].sort(key=lambda e:e["step"])
    return d

def report(d):
    return tool.evaluate(d)

def count(d):
    return report(d)["candidate_complete_original_marker_chains_UNVERIFIED"]

class OriginalMarkerChainTests(unittest.TestCase):
    def test_positive_only_unverified_syntactic_chain(self):
        z=report(synthetic())
        self.assertEqual(z["candidate_complete_original_marker_chains_UNVERIFIED"],1)
        self.assertEqual(z["missing_or_ambiguous_original_marker_chains"],0)
        self.assertFalse(z["actual_engine_issued_one_use_request_certified"])
        self.assertFalse(z["actual_original_dynamic_legality_certified"])
        self.assertFalse(z["original_pp_execution_or_cancellation_certified"])
        self.assertEqual(z["original_native_gameplay_accepted"],0)
        self.assertFalse(z["production_authorized"])
    def test_missing_each_kind_prevents_joint_claim(self):
        for kind in (7,12,13,14,15,16,5):
            with self.subTest(kind=kind):
                d=synthetic()
                d["events"]=[e for e in d["events"] if e["kind"]!=kind]
                self.assertEqual(count(d),0)
    def test_duplicate_each_kind_denies_unique_chain(self):
        for kind in (7,12,13,14,15,16):
            with self.subTest(kind=kind):
                d=synthetic();e=next(x for x in d["events"] if x["kind"]==kind)
                duplicate=copy.deepcopy(e)
                duplicate.update(step=e["step"]+1,frame=3980+(e["step"]+1)//4)
                # Identical PP watcher transitions are not duplicated here;
                # markers at a new real CPU step are legal but ambiguous.
                d["events"].append(duplicate)
                d["events"].sort(key=lambda x:x["step"])
                self.assertEqual(count(d),0)
    def test_swapped_move_target_order_denies(self):
        d=synthetic()
        x=next(e for e in d["events"] if e["kind"]==15)
        y=next(e for e in d["events"] if e["kind"]==16)
        x["step"],y["step"]=y["step"],x["step"]
        x["frame"],y["frame"]=y["frame"],x["frame"]
        d["events"].sort(key=lambda x:x["step"])
        self.assertEqual(count(d),0)
    def test_pp_writer_before_target_is_not_valid_joint_candidate(self):
        d=synthetic()
        p=next(x for x in d["events"] if x["kind"]==5)
        p["step"]=7;p["frame"]=3980+7//4
        # A marker and PP watcher on same original CPU step must share
        # original PC/opcode/regs. Instead move the target later.
        p["step"]=8;p["frame"]=3980+8//4
        target=next(e for e in d["events"] if e["kind"]==16)
        target["step"]=10;target["frame"]=3980+10//4
        # Completion before target remains possible; stage order still true.
        d["events"].sort(key=lambda x:x["step"])
        self.assertEqual(count(d),0)
    def test_controller_completion_can_precede_pp_debit(self):
        d=synthetic()
        self.assertLess(next(e for e in d["events"] if e["kind"]==12)["step"],
                        next(e for e in d["events"] if e["kind"]==5)["step"])
        self.assertEqual(count(d),1)
    def test_controller_completion_after_pp_debit_also_possible(self):
        d=synthetic()
        e=next(x for x in d["events"] if x["kind"]==12)
        e["step"]=17;e["frame"]=3980+17//4
        d["events"].sort(key=lambda x:x["step"])
        self.assertEqual(count(d),1)
    def test_manual_barrier_denies_even_when_markers_follow(self):
        d=synthetic()
        d["events"].insert(2,row(8,4,0x0806449C))
        # Avoid distinct original instruction PC on same step.
        d["events"][-1]["step"]=6
        d["events"][-1]["frame"]=3980+6//4
        # Better: place manual marker at step 2, between emitter and reply.
        d["events"]=[x for x in d["events"] if x["kind"]!=8]
        d["events"].append(row(8,2,0x0806449C))
        d["events"].sort(key=lambda x:x["step"])
        self.assertEqual(count(d),0)
    def test_inbattle_clear_denies_postclear_pp_chain(self):
        d=synthetic()
        edge=next(e for e in d["events"] if e["kind"]==2)
        edge["step"]=10;edge["frame"]=3980+10//4
        d["events"].sort(key=lambda x:x["step"])
        self.assertEqual(count(d),0)
    def test_second_emitter_before_stage_completion_denies(self):
        d=synthetic()
        d["events"].append(row(6,10,0x0806BD80,r0=0,r2=10))
        d["events"].sort(key=lambda x:x["step"])
        self.assertEqual(count(d),0)
    def test_unverified_pp_byte_delta_not_thumb_store_denied(self):
        d=synthetic()
        e=next(e for e in d["events"] if e["kind"]==5)
        e["opcode"]=0x780E
        self.assertEqual(count(d),0)
    def test_multi_pp_byte_changes_are_ambiguous(self):
        d=synthetic()
        d["events"].append(row(5,13,0x0809E6BA,PP+1,20,19,1,
                               r1=PP+1,r6=19,opcode=0x700E))
        d["events"].sort(key=lambda x:x["step"])
        self.assertEqual(count(d),0)
    def test_bad_cpu_snapshot_or_trace_privileges_rejected(self):
        for mutate in (lambda d:d["events"][2].update(r5=True),
                       lambda d:d.update(guest_writes=1),
                       lambda d:d.update(production_authorized=True)):
            d=synthetic();mutate(d)
            with self.assertRaises((ValueError,TypeError)):
                report(d)
    def test_no_emitter_never_establishes_a_chain(self):
        d=synthetic()
        d["events"]=[e for e in d["events"] if e["kind"]!=6]
        z=report(d)
        self.assertEqual(z["candidate_complete_original_marker_chains_UNVERIFIED"],0)
        self.assertFalse(z["actual_engine_issued_one_use_request_certified"])

if __name__=="__main__":
    unittest.main()
