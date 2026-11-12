#!/usr/bin/env python3
"""Synthetic deny tests for exact ROM PP writer; no private witness in CI."""
import unittest
import verify_exact_pp_writer as v

def event(kind,frame,pc,**k):
    x={name:0 for name in v.ALLOWED-{"pc"}}
    x.update(kind=kind,frame=frame,pc=pc,flags=4)
    x.update(k)
    return x

def fixture():
    events=[]
    for start,after in ((4977,19),(5147,18)):
        events.extend([
            event(1,start,"0x806bd80",r0=0,r2=10,r3=256),
            event(2,start,"0x806b370",r0=0,r1=1,r3=6),
            event(8,start,"0x806261c",r0=0),
            event(3,start+1,"0x8094330",r0=0),
            event(4,start+1,"0x809435c",r0=0),
            event(5,start+1,"0x8094374",r0=325),
            event(6,start+1,"0x8094380",r2=1),
            event(9,start+46 if after==19 else start+48,
                  v.WRITER,r1=v.OWN_PP,slot=0,before=after+1,after=after),
        ])
    return events

class PlayerPpWriteTests(unittest.TestCase):
    def test_native_player_two_debits_not_production(self):
        r=v.summarize(fixture())
        self.assertEqual(r["original_native_pp_debit_events"],2)
        self.assertEqual(r["native_write_frames"],[5023,5195])
        self.assertFalse(r["production_promotion_authorized"])
    def reject(self,fn):
        x=fixture();fn(x)
        with self.assertRaises(ValueError):v.summarize(x)
    def test_actor_is_player(self):self.reject(lambda x:x[0].update(r0=1))
    def test_no_item_action(self):self.reject(lambda x:x[0].update(r2=9))
    def test_target_one(self):self.reject(lambda x:x[0].update(r3=0))
    def test_source_wrong_move(self):self.reject(lambda x:x[5].update(r0=157))
    def test_no_original_reply(self):self.reject(lambda x:x.pop(1))
    def test_wrong_player_completion(self):self.reject(lambda x:x[2].update(r0=1))
    def test_wrong_validator(self):self.reject(lambda x:x[3].update(r0=1))
    def test_wrong_slot(self):self.reject(lambda x:x[4].update(r0=2))
    def test_wrong_target_commit(self):self.reject(lambda x:x[6].update(r2=0))
    def test_write_before_commit(self):self.reject(lambda x:x.insert(5,x.pop(7)))
    def test_pp_wrong_pointer(self):self.reject(lambda x:x[7].update(r1=v.OWN_PP+1))
    def test_pp_wrong_slot(self):self.reject(lambda x:x[7].update(slot=1))
    def test_pp_not_one_decrement(self):self.reject(lambda x:x[7].update(after=17))
    def test_pp_increases(self):self.reject(lambda x:x[7].update(after=21))
    def test_late_pp_writer(self):self.reject(lambda x:x[7].update(frame=5120))
    def test_duplicate_pp_writer(self):
        self.reject(lambda x:x.insert(8,dict(x[7])))
    def test_unknown_battle_mode(self):self.reject(lambda x:x[0].update(flags=8))
    def test_wrong_event_fields(self):self.reject(lambda x:x[0].update(raw_rom=b"not allowed"))
    def test_out_of_order(self):self.reject(lambda x:x[0].update(frame=5200))
    def test_no_move(self):self.reject(lambda x:[q.update(kind=10) for q in x if q["kind"]==1])
    def test_confounding_memory_write_does_not_count(self):
        x=fixture()
        x.insert(8,event(9,5030,"0x81fb8da",slot=1,before=15,after=10))
        # Confounder has no authority to count as move PP usage.
        r=v.summarize(x)
        self.assertEqual(r["original_native_pp_debit_events"],2)
        self.assertEqual(r["source_copy_or_other_byte_changes_not_pp_certified"],1)
    def test_submitted_without_pp_is_unclassified(self):
        x=fixture()
        x.pop(15)
        r=v.summarize(x)
        self.assertEqual(r["unattributed_submissions"],1)
        self.assertFalse(r["battle_terminal_certified"])

if __name__=="__main__":unittest.main()
