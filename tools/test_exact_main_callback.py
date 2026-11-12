#!/usr/bin/env python3
"""Fail-closed original Main callback synthetic CPU mutation tests."""
import unittest
import verify_exact_main_callback as m
def fixture():
    rows=[]
    for f,pc,kind,before,after in m.EXPECTED:
        e={k:0 for k in m.FIELDS}
        e.update(frame=f,pc=pc,kind=kind,before=before,after=after,
                 flags=4,battlers=2,pending=0,inbattle=0)
        if kind==1:e.update(r4=m.MAIN,r2=after)
        if kind==2:e.update(r3=m.MAIN,r0=after)
        if kind==4:e.update(main_state=after)
        rows.append(e)
    return rows
class OriginalMainHandoff(unittest.TestCase):
    def test_verified_fixture_scope_denies_promotion(self):
        r=m.audit(fixture())
        self.assertTrue(r["original_callback_cpu_handoff_witness"])
        self.assertFalse(r["prior_battle_outcome_decision_certified"])
        self.assertFalse(r["production_promotion_authorized"])
    def denied(self,fn):
        x=fixture();fn(x)
        with self.assertRaises(ValueError):m.audit(x)
    def test_missing_first_callback(self):self.denied(lambda a:a.pop(0))
    def test_wrong_callback1_pc(self):self.denied(lambda a:a[0].update(pc=0))
    def test_wrong_callback1_main_base(self):self.denied(lambda a:a[0].update(r4=0))
    def test_wrong_callback1_value(self):self.denied(lambda a:a[0].update(r2=0))
    def test_wrong_callback2_pc(self):self.denied(lambda a:a[1].update(pc=0))
    def test_wrong_callback2_base(self):self.denied(lambda a:a[1].update(r3=0))
    def test_wrong_callback2_value(self):self.denied(lambda a:a[1].update(r0=0))
    def test_reordered_writes(self):self.denied(lambda a:a.reverse())
    def test_wrong_intermediate_callback(self):self.denied(lambda a:a[2].update(after=0))
    def test_missing_final_field_callback(self):self.denied(lambda a:a[-2].update(after=0))
    def test_main_state_transition_false(self):self.denied(lambda a:a[4].update(main_state=2))
    def test_no_main_state_reset(self):self.denied(lambda a:a[-1].update(after=3))
    def test_not_wild_single(self):self.denied(lambda a:a[0].update(flags=8))
    def test_not_two_battlers(self):self.denied(lambda a:a[0].update(battlers=4))
    def test_pending_not_cleared(self):self.denied(lambda a:a[1].update(pending=1))
    def test_main_still_inbattle(self):self.denied(lambda a:a[1].update(inbattle=2))
    def test_wrong_frame(self):self.denied(lambda a:a[0].update(frame=3999))
    def test_wrong_object_type(self):self.denied(lambda a:a[0].update(frame="3984"))
    def test_private_cpu_bytes_not_accepted(self):self.denied(lambda a:a[0].update(private_bytes="bad"))
    def test_extra_callback_write(self):self.denied(lambda a:a.append(dict(a[-1])))
if __name__=="__main__":unittest.main()
