#!/usr/bin/env python3
"""Synthetic field-return and native flag-edge negatives; no game bytes."""
import unittest
import verify_exact_next_wild as m

def fixture():
    rows=[]
    for i in range(14):
        rows.append(dict(trial=0,step=i,direction=m.DIRECTIONS[i%4],
                 frame=6755+260*i if i<13 else 9994,
                 result=1 if i<13 else 2,
                 flags=4,pc="0x188" if i<13 else "0x806ad48",flag_changes=[]))
    template=dict(r0=0,r1=0,r2=0,r3=0,kind0=0,kind1=0)
    rows[-1]["flag_changes"]=[
        dict(frame=9957,pc="0x80c501e",before=4,after=0,**template),
        dict(frame=9993,pc="0x808d71a",before=0,after=4,**template)]
    return rows
class NativeNewWild(unittest.TestCase):
    def test_synthetic_second_wild_not_terminal_certificate(self):
        x=m.summarize(fixture())
        self.assertTrue(x["original_field_to_second_wild_roundtrip_observed"])
        self.assertFalse(x["previous_battle_outcome_writer_pc_certified"])
        self.assertFalse(x["previous_overworld_main_callback_pc_certified"])
        self.assertFalse(x["production_promotion_authorized"])
    def reject(self,fn):
        x=fixture();fn(x)
        with self.assertRaises(ValueError):m.summarize(x)
    def test_wrong_sequence(self):self.reject(lambda x:x[2].update(step=4))
    def test_wrong_direction(self):self.reject(lambda x:x[3].update(direction="A"))
    def test_manual_ack_trial(self):self.reject(lambda x:x[2].update(trial=1))
    def test_wrong_frame(self):self.reject(lambda x:x[1].update(frame=1))
    def test_no_second_constructor(self):self.reject(lambda x:x[-1].update(result=1))
    def test_wrong_guest_constructor(self):self.reject(lambda x:x[-1].update(pc="0x0"))
    def test_wrong_original_battle_flag(self):self.reject(lambda x:x[2].update(flags=0))
    def test_late_other_flag_edge(self):
        self.reject(lambda x:x[8]["flag_changes"].append(dict(x[-1]["flag_changes"][0])))
    def test_missing_flag_reset(self):self.reject(lambda x:x[-1]["flag_changes"].pop(0))
    def test_wrong_reset_pc(self):self.reject(lambda x:x[-1]["flag_changes"][0].update(pc="0x808d71a"))
    def test_reset_flags_not_zero(self):self.reject(lambda x:x[-1]["flag_changes"][0].update(after=4))
    def test_reset_not_from_wild(self):self.reject(lambda x:x[-1]["flag_changes"][0].update(before=0))
    def test_wrong_new_wild_write_pc(self):self.reject(lambda x:x[-1]["flag_changes"][1].update(pc="0x80c501e"))
    def test_new_flag_not_four(self):self.reject(lambda x:x[-1]["flag_changes"][1].update(after=8))
    def test_reordered_native_flag_cpu_writes(self):
        self.reject(lambda x:x[-1]["flag_changes"].reverse())
    def test_wrong_controller_ownership(self):self.reject(lambda x:x[-1]["flag_changes"][0].update(kind0=3))
    def test_untrusted_evidence_extra(self):self.reject(lambda x:x[0].update(private_game_bytes="no"))
    def test_wrong_extra_edge(self):self.reject(lambda x:x[-1]["flag_changes"].append(dict(x[-1]["flag_changes"][1])))
    def test_absent_witness(self):self.reject(lambda x:x.clear())
    def test_invalid_pc_type(self):self.reject(lambda x:x[-1]["flag_changes"][0].update(pc=123))
if __name__=="__main__":unittest.main()
