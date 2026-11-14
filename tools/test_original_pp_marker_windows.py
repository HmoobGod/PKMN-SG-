#!/usr/bin/env python3
"""Public original PP window triage; no ROM, private trace or emulator."""
import copy
import unittest
import triage_original_pp_marker_windows as v
from test_exact_outcome_pp_edges import fixture,row

class PpMarkerWindowsTests(unittest.TestCase):
    @staticmethod
    def pp_edge(step,slot=0,before=20,after=19):
        return row(5,step,0x0809E6BA,v.PP+slot,before,after,slot,
                   r1=v.PP+slot,r6=after,opcode=0x700E)
    def test_existing_public_synthetic_trace_does_not_classify_real_causes(self):
        z=v.triage(fixture())
        self.assertEqual(z["original_emitter_marker_windows_unverified"],1)
        self.assertEqual(z["windows_with_reply_marker_unverified"],1)
        self.assertEqual(z["one_syntactic_pp_writer_in_window_unverified"],1)
        self.assertEqual(z["no_syntactic_pp_writer_in_window_UNCLASSIFIED"],0)
        self.assertFalse(z["historical_two_pp_missing_causes_classified"])
        self.assertFalse(z["actual_pp_execution_or_cancellation_certified"])
        self.assertEqual(z["native_gameplay_scenarios_accepted"],0)
        self.assertFalse(z["production_authorized"])
    def test_without_pp_writer_is_unknown_not_cancellation(self):
        d=fixture();d["events"]=[e for e in d["events"] if e["kind"]!=5]
        z=v.triage(d)
        self.assertEqual(z["no_syntactic_pp_writer_in_window_UNCLASSIFIED"],1)
        self.assertEqual(z["syntactic_pp_writer_candidates_total"],0)
        self.assertFalse(z["actual_pp_execution_or_cancellation_certified"])
    def test_two_pp_debits_in_same_window_stay_ambiguous(self):
        d=fixture();d["events"].insert(3,self.pp_edge(16,1,10,9))
        z=v.triage(d)
        self.assertEqual(z["multiple_syntactic_pp_writers_in_window_AMBIGUOUS"],1)
        self.assertEqual(z["one_syntactic_pp_writer_in_window_unverified"],0)
        self.assertFalse(z["historical_two_pp_missing_causes_classified"])
    def test_pp_writer_before_first_emitter_never_assigned_to_later_emit(self):
        d=fixture();d["events"].insert(0,self.pp_edge(0,1,10,9))
        z=v.triage(d)
        self.assertEqual(z["pp_changes_before_any_emit_unattributed"],1)
        self.assertEqual(z["one_syntactic_pp_writer_in_window_unverified"],1)
        self.assertFalse(z["real_actor0_one_use_engine_request_certified"])
    def test_next_emitter_starts_distinct_unverified_window(self):
        d=fixture()
        d["events"].extend([row(6,32,0x0806BD80,r0=0,r2=10),
                            row(7,34,0x0806B370,r0=0,r1=1,r3=6)])
        z=v.triage(d)
        self.assertEqual(z["original_emitter_marker_windows_unverified"],2)
        self.assertEqual(z["one_syntactic_pp_writer_in_window_unverified"],1)
        self.assertEqual(z["no_syntactic_pp_writer_in_window_UNCLASSIFIED"],1)
        self.assertEqual(z["windows"][1]["reply_count"],1)
        self.assertFalse(z["actual_pp_execution_or_cancellation_certified"])
    def test_nonstore_or_wrong_pp_delta_not_syntactic_candidate(self):
        for opcode,before,after in ((0x780E,20,19),(0x700E,21,19)):
            with self.subTest(opcode=hex(opcode),before=before):
                d=fixture();d["events"][2].update(opcode=opcode,before=before,after=after,r6=after)
                z=v.triage(d)
                self.assertEqual(z["syntactic_pp_writer_candidates_total"],0)
                self.assertEqual(z["other_pp_changes_in_emitter_windows_unattributed"],1)
    def test_bad_cpu_identity_field_or_promotion_claim_rejected(self):
        for change in (lambda d:d["events"][2].update(r7=True),
                       lambda d:d.update(production_authorized=True),
                       lambda d:d["events"].append(copy.deepcopy(d["events"][2])),
                       lambda d:d.update(guest_writes=1)):
            d=fixture();change(d)
            with self.assertRaises((ValueError,TypeError)):
                v.triage(d)
if __name__=="__main__":
    unittest.main()
