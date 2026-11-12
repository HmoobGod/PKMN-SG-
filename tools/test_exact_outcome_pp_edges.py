#!/usr/bin/env python3
"""Synthetic mutation and privilege-denial tests. NOT a native gameplay run."""
import copy
import unittest
import verify_exact_outcome_pp_edges as v


def row(kind, step, pc, address=0, before=0, after=0, slot=255, **regs):
    r={k:0 for k in v.FIELDS}
    r.update(frame=3980+step//4,step=step,pc=pc,kind=kind,address=address,
             before=before,after=after,slot=slot,flags=4,battlers=2,
             pending=0,inbattle=2,callback1=0x0808CBDD,callback2=0x0808F225)
    r.update(regs)
    return r


def fixture():
    data=dict(schema=v.SCHEMA,current_sha256=v.CURRENT,
              modified_sha256=v.MODIFIED,save_sha256=v.SAVE,
              guest_writes=0,host_move_menu_inputs=0,new_hook_installed=False,
              candidate_outcome_byte_address=0,status=1,steps=300)
    data["events"]=[
        row(6,1,0x0806BD80,r0=0,r2=10),
        row(7,3,0x0806B370,r0=0,r1=1,r3=6),
        row(5,12,0x0809E6BA,v.PP,20,19,0,r1=v.PP),
        row(2,20,v.MAIN+0x200, v.MAIN+0x439,2,0),
        row(3,24,0x0808E33C,v.MAIN,0x0808CBDD,0x081C7589,
            r4=v.MAIN,callback1=0x081C7589),
        row(4,27,0x081AED58,v.MAIN+4,0x0808F225,0x080C4265,
            r3=v.MAIN,callback2=0x080C4265),
    ]
    return data


class ExactOutcomePpEdgeTests(unittest.TestCase):
    def test_fixture_is_only_triage(self):
        z=v.audit(fixture())
        self.assertEqual(z["original_pp_writer_single_byte_debits_seen"],1)
        self.assertEqual(z["original_callback_pointer_transitions"],2)
        self.assertFalse(z["full_native_terminal_certified"])
        self.assertFalse(z["original_battle_outcome_decision_pc_certified"])
        self.assertFalse(z["production_promotion_authorized"])
    def denied(self,change):
        d=fixture();change(d)
        with self.assertRaises(ValueError):v.audit(d)
    def test_wrong_rom_identity(self):self.denied(lambda d:d.update(modified_sha256=v.CURRENT))
    def test_input_injection(self):self.denied(lambda d:d.update(host_move_menu_inputs=1))
    def test_guest_writes(self):self.denied(lambda d:d.update(guest_writes=1))
    def test_new_hook(self):self.denied(lambda d:d.update(new_hook_installed=True))
    def test_wrong_schema(self):self.denied(lambda d:d.update(schema="invented"))
    def test_unfinished(self):self.denied(lambda d:d.update(status=2))
    def test_unbounded_steps(self):self.denied(lambda d:d.update(steps=0x100000000))
    def test_no_events(self):self.denied(lambda d:d.update(events=[]))
    def test_wrong_cpu_fields(self):self.denied(lambda d:d["events"][0].update(rom_bytes="no"))
    def test_wrong_cpu_integer(self):self.denied(lambda d:d["events"][0].update(pc="0x0806bd80"))
    def test_emitter_enemy(self):self.denied(lambda d:d["events"][0].update(r0=1))
    def test_emitter_not_move(self):self.denied(lambda d:d["events"][0].update(r2=9))
    def test_wrong_reply(self):self.denied(lambda d:d["events"][1].update(r1=0))
    def test_fake_native_writer(self):self.denied(lambda d:d["events"][2].update(pc=0x123))
    def test_wrong_own_pp_address(self):self.denied(lambda d:d["events"][2].update(address=v.PP+1))
    def test_duplicate_stale_step(self):self.denied(lambda d:d["events"].insert(1,copy.deepcopy(d["events"][0])))
    def test_reverse_instruction_order(self):self.denied(lambda d:d["events"].reverse())
    def test_callback_wrong_register(self):self.denied(lambda d:d["events"][4].update(r4=0))
    def test_callback_wrong_value(self):self.denied(lambda d:d["events"][5].update(callback2=0))
    def test_callback_wrong_base(self):self.denied(lambda d:d["events"][5].update(address=0))
    def test_bad_outcome_candidate(self):self.denied(lambda d:d.update(candidate_outcome_byte_address=v.MAIN))
    def test_candidate_unproven(self):
        d=fixture();d.update(candidate_outcome_byte_address=0x02002345)
        d["events"].insert(2,row(1,5,0x08012340,0x02002345,0,1))
        result=v.audit(d)
        self.assertEqual(result["candidate_outcome_byte_transitions"],1)
        self.assertFalse(result["original_battle_outcome_decision_pc_certified"])
    def test_candidate_wrong_address(self):
        def change(d):
            d.update(candidate_outcome_byte_address=0x02002345)
            d["events"].insert(2,row(1,5,0x08012340,0x02002346,0,1))
        self.denied(change)
    def test_other_pp_writer_not_native(self):
        d=fixture();d["events"][2].update(pc=0x081FB8DA)
        result=v.audit(d)
        self.assertEqual(result["original_pp_writer_single_byte_debits_seen"],0)
        self.assertEqual(result["other_player_pp_byte_changes_not_certified"],1)
    def test_possible_pp_writer_no_debit_not_counted(self):
        d=fixture();d["events"][2].update(after=21)
        result=v.audit(d)
        self.assertEqual(result["original_pp_writer_single_byte_debits_seen"],0)
    def test_manual_menu_marker_not_full_terminal(self):
        d=fixture();d["events"].append(row(8,32,0x0806449C))
        result=v.audit(d)
        self.assertEqual(result["manual_move_menu_markers"],1)
        self.assertFalse(result["full_native_terminal_certified"])

if __name__ == "__main__": unittest.main()
