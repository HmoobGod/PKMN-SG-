#!/usr/bin/env python3
"""Synthetic denial tests for original Thumb STRB scouting, NOT native proof."""
import copy
import unittest
import verify_exact_thumb_byte_stores as v


def row(step=5, frame=100, address=0x02000100, h=0x7008):
    r=[2, address,0,0,0,0,0,0]
    return dict(frame=frame,step_index=step,pc=0x08001000,halfword=h,
                form=1,address=address,base_register=1,offset_register=255,
                source_register=0,old_byte=0,new_byte=2,expected_byte=2,
                registers=r,battle_flags=4,battlers=2,pending=0,inbattle=2,
                callback1=0x0808CBDD,callback2=0x0808F225)


def fixture():
    return dict(schema=v.SCHEMA,current_sha256=v.CURRENT,
                modified_sha256=v.MODIFIED,save_sha256=v.SAVE,
                guest_writes=0,host_move_menu_inputs=0,new_hook_installed=False,
                status=1,guest_steps=200,start_frame=99,end_frame=120,
                window_frames=20,range_lo=0x02000000,range_hi=0x0203FFFF,
                events=[row()],start_inbattle=2,end_inbattle=0,
                start_callback1=0x0808CBDD,start_callback2=0x0808F225,
                end_callback1=0x081C7589,end_callback2=0x081C9FC5)


class ThumbStoreAudit(unittest.TestCase):
    def test_realistic_synthetic_strb_still_blocks_promotion(self):
        r=v.audit(fixture())
        self.assertEqual(r['candidate_byte_stores'],1)
        self.assertEqual(r['candidate_addresses_hex'],['0x02000100'])
        self.assertTrue(r['callback2_changed'])
        self.assertFalse(r['original_battle_outcome_writer_pc_certified'])
        self.assertFalse(r['full_native_terminal_certified'])
        self.assertFalse(r['production_promotion_authorized'])
    def test_no_candidates_cannot_prove_terminal(self):
        d=fixture();d['events']=[]
        r=v.audit(d)
        self.assertEqual(r['candidate_byte_stores'],0)
        self.assertFalse(r['authentic_gbattleoutcome_address_identified'])
    def denied(self, change):
        d=fixture();change(d)
        with self.assertRaises((ValueError,TypeError,KeyError)):
            v.audit(d)
    def test_wrong_rom(self):self.denied(lambda d:d.update(modified_sha256='wrong'))
    def test_wrong_save(self):self.denied(lambda d:d.update(save_sha256='wrong'))
    def test_guest_mutation(self):self.denied(lambda d:d.update(guest_writes=1))
    def test_manual_input(self):self.denied(lambda d:d.update(host_move_menu_inputs=1))
    def test_installed_hook(self):self.denied(lambda d:d.update(new_hook_installed=True))
    def test_bad_status(self):self.denied(lambda d:d.update(status=2))
    def test_bad_status_bool(self):self.denied(lambda d:d.update(status=True))
    def test_too_many_steps(self):self.denied(lambda d:d.update(guest_steps=0x100000000))
    def test_empty_step_budget(self):self.denied(lambda d:d.update(guest_steps=0))
    def test_oversized_events(self):self.denied(lambda d:d.update(events=[row() for _ in range(8193)]))
    def test_overlap_regions(self):self.denied(lambda d:d.update(range_hi=0x03007FFF))
    def test_mmio_region(self):self.denied(lambda d:d.update(range_lo=0x04000000,range_hi=0x04000100))
    def test_no_frame_budget_completed(self):self.denied(lambda d:d.update(end_frame=100))
    def test_unknown_key(self):self.denied(lambda d:d.update(hidden_guest_bytes='bad'))
    def test_unknown_event_key(self):self.denied(lambda d:d['events'][0].update(raw_memory='bad'))
    def test_negative_pc(self):self.denied(lambda d:d['events'][0].update(pc=-1))
    def test_iwram_execution_pc(self):self.denied(lambda d:d['events'][0].update(pc=0x03001000))
    def test_misaligned_pc(self):self.denied(lambda d:d['events'][0].update(pc=0x08001001))
    def test_fake_thumb_opcode(self):self.denied(lambda d:d['events'][0].update(halfword=0x7808))
    def test_opcode_does_not_match_form(self):self.denied(lambda d:d['events'][0].update(form=2))
    def test_opcode_does_not_match_source(self):self.denied(lambda d:d['events'][0].update(source_register=3))
    def test_opcode_does_not_match_base(self):self.denied(lambda d:d['events'][0].update(base_register=2))
    def test_opcode_does_not_match_addr(self):self.denied(lambda d:d['events'][0].update(address=0x02000101))
    def test_wrong_expected_byte(self):self.denied(lambda d:d['events'][0].update(expected_byte=3))
    def test_wrong_written_byte(self):self.denied(lambda d:d['events'][0].update(new_byte=3))
    def test_did_not_change(self):self.denied(lambda d:d['events'][0].update(old_byte=2))
    def test_big_value(self):self.denied(lambda d:d['events'][0].update(new_byte=8))
    def test_spurious_bool_register(self):self.denied(lambda d:d['events'][0].update(registers=[True]+d['events'][0]['registers'][1:]))
    def test_duplicated_step(self):self.denied(lambda d:d['events'].append(copy.deepcopy(d['events'][0])))
    def test_event_after_budget(self):self.denied(lambda d:d['events'][0].update(step_index=201))
    def test_frame_before_start(self):self.denied(lambda d:d['events'][0].update(frame=98))
    def test_wrong_battlers(self):self.denied(lambda d:d['events'][0].update(battlers=4))
    def test_wrong_battle_flags(self):self.denied(lambda d:d['events'][0].update(battle_flags=8))
    def test_inbattle_oversized(self):self.denied(lambda d:d['events'][0].update(inbattle=256))
    def test_register_addr_overflow(self):
        d=fixture();d['events'][0]['registers'][1]=0xFFFFFFFF
        d['events'][0]['halfword']=0x7048
        with self.assertRaises(ValueError):v.audit(d)
    def test_register_offset_form(self):
        d=fixture();e=d['events'][0]
        e.update(halfword=0x5488,form=2,offset_register=2)
        self.assertEqual(v.audit(d)['candidate_byte_stores'],1)
    def test_bad_register_offset_form(self):
        d=fixture();e=d['events'][0]
        e.update(halfword=0x5488,form=2,offset_register=2)
        e['registers'][2]=1
        with self.assertRaises(ValueError):v.audit(d)
    def test_iwram_allowed_as_independent_scan(self):
        d=fixture();e=d['events'][0]
        d.update(range_lo=0x03000000,range_hi=0x03007FFF)
        e['registers'][1]=e['address']=0x03000100
        r=v.audit(d)
        self.assertEqual(r['ram_region'],'IWRAM')
        self.assertFalse(r['authentic_gbattleoutcome_address_identified'])
    def test_outcome_never_certified_even_after_callback(self):
        d=fixture();d['events'][0].update(battle_flags=0,battlers=0,inbattle=0)
        r=v.audit(d)
        self.assertFalse(r['original_battle_outcome_writer_pc_certified'])
        self.assertFalse(r['production_promotion_authorized'])


if __name__=='__main__': unittest.main()
