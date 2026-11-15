#!/usr/bin/env python3
"""Public fake CPU events only, no original ROM/save/emulator/trace."""
import unittest
from triage_original_actor0_controller_lifecycle import evaluate
from test_original_actor0_terminal_joint import complete_fixture
from test_exact_outcome_pp_edges import row
from verify_exact_outcome_pp_edges import PP

def result(data):
    return evaluate(data)

def possible(data):
    return result(data)["uninterrupted_owner_window_candidate_UNVERIFIED"]

class ControllerLifecycleTests(unittest.TestCase):
    def test_unmodified_synthetic_join_only_unverified(self):
        z=result(complete_fixture())
        self.assertTrue(z["upstream_original_joint_candidate_unverified"])
        self.assertTrue(z["uninterrupted_owner_window_candidate_UNVERIFIED"])
        for k in ("original_controller_mask_owner_bit_attested",
                  "original_one_use_request_ownership_certified",
                  "original_target_and_move_semantics_certified",
                  "pp_debit_or_cancellation_reason_certified",
                  "original_outcome_decision_pc_certified",
                  "original_overworld_return_certified",
                  "production_authorized"):
            self.assertFalse(z[k])
        self.assertEqual(z["native_gameplay_accepted"],0)

    def test_completion_after_result_rejected(self):
        d=complete_fixture()
        c=next(e for e in d["events"] if e["kind"]==12)
        c.update(step=19,frame=3980+19//4)
        d["events"].sort(key=lambda e:e["step"])
        self.assertFalse(possible(d))
        self.assertTrue(result(d)["upstream_original_joint_candidate_unverified"])
        self.assertFalse(result(d)["completion_before_candidate_result_unverified"])

    def test_flag_change_during_actor0_request_rejected(self):
        d=complete_fixture()
        d["events"].append(row(9,10,0x08102000,0x02001AB4,4,5,flags=5))
        d["events"].sort(key=lambda e:e["step"])
        z=result(d)
        self.assertEqual(z["controller_exec_mask_transition_steps_in_action_window"],[10])
        self.assertFalse(z["uninterrupted_owner_window_candidate_UNVERIFIED"])

    def test_pending_change_during_actor0_request_rejected(self):
        d=complete_fixture()
        d["events"].append(row(10,10,0x08102000,0x02001D2C,0,1,pending=1))
        d["events"].sort(key=lambda e:e["step"])
        z=result(d)
        self.assertEqual(z["original_pending_transition_steps_in_action_window"],[10])
        self.assertFalse(z["uninterrupted_owner_window_candidate_UNVERIFIED"])

    def test_mask_change_at_emitter_step_rejected_independent_row_order(self):
        d=complete_fixture()
        m=row(9,1,0x0806BD80,0x02001AB4,4,5,r0=0,r2=10,flags=5)
        d["events"].insert(1,m)
        z=result(d)
        self.assertEqual(z["controller_exec_mask_transition_steps_in_action_window"],[1])
        self.assertFalse(z["uninterrupted_owner_window_candidate_UNVERIFIED"])

    def test_pp_and_pending_same_cpu_step_ambiguous(self):
        d=complete_fixture()
        p=next(e for e in d["events"] if e["kind"]==5)
        pending=row(10,p["step"],p["pc"],0x02001D2C,0,1,
                    r1=PP,r6=p["after"],opcode=p["opcode"],pending=1)
        p["pending"]=1
        d["events"].append(pending)
        d["events"].sort(key=lambda e:(e["step"],e["kind"]))
        z=result(d)
        self.assertEqual(z["original_pending_transition_steps_in_action_window"],[p["step"]])
        self.assertFalse(possible(d))

    def test_outside_action_window_owner_change_does_not_reassign_pp(self):
        d=complete_fixture()
        d["events"].append(row(9,14,0x08102000,0x02001AB4,4,5,flags=5))
        d["events"].sort(key=lambda e:e["step"])
        self.assertTrue(possible(d))

    def test_absent_parent_pp_or_result_never_promoted(self):
        for k in (1,5,6,7,12):
            with self.subTest(kind=k):
                d=complete_fixture()
                d["events"]=[e for e in d["events"] if e["kind"]!=k]
                self.assertFalse(possible(d))

    def test_strict_original_audit_rejects_forged_context(self):
        for mutate in (lambda d:d.update(production_authorized=True),
                       lambda d:d["events"][0].update(flags=True),
                       lambda d:d.update(guest_writes=1)):
            d=complete_fixture()
            mutate(d)
            with self.assertRaises((ValueError,TypeError)):
                result(d)

if __name__=="__main__":
    unittest.main()
