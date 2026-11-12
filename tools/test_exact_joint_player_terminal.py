#!/usr/bin/env python3
"""Synthetic original actor0/PP/Main join tests; NOT a native battle replay."""
import unittest
import verify_exact_joint_player_terminal as v

def event(step,kind,**kw):
    d={k:0 for k in v.FIELDS}
    d.update(frame=3200,step=step,pc=0x081C1234,opcode=0,kind=kind,
             stage=0 if kind in v.MARKERS else 1,slot=255,flags=4,
             battlers=2,inbattle=2,callback1=0x0808CBDD,callback2=0x0808F225)
    if kind in v.MARKERS:d["pc"]=v.MARKERS[kind]
    if kind in v.ADDRESS:d["address"]=v.ADDRESS[kind]
    if kind==9:d.update(address=v.PP,slot=0)
    d.update(kw)
    return d

def fixture(pp=True):
    rows=[event(i,i+1) for i in range(7)]
    rows[0]["r0"]=0;rows[0]["r2"]=10;rows[0]["r3"]=256
    rows[1]["r0"]=0;rows[1]["r1"]=1;rows[1]["r3"]=6
    rows[4]["r0"]=0;rows[5]["r0"]=325;rows[6]["r2"]=1
    if pp:
        rows.append(event(7,9,pc=v.WRITER,r1=v.PP,before=20,after=19))
    rows.append(event(8,10,before=2,after=0,inbattle=0))
    rows.append(event(9,11,pc=0x0808E33C,before=0x0808CBDD,
                      after=0x081C7589,inbattle=0,callback1=0x081C7589))
    rows.append(event(10,12,pc=0x081AED58,before=0x0808F225,
                      after=0x081C9FC5,inbattle=0,callback1=0x081C7589,
                      callback2=0x081C9FC5))
    return dict(schema=v.SCHEMA,current_sha256=v.CURRENT,
                modified_sha256=v.MODIFIED,save_sha256=v.SAVE,
                guest_writes=0,host_move_menu_inputs=0,new_hook_installed=False,
                status=1,start_frame=3200,end_frame=3202,window_frames=2,
                steps=11,initial_main=2,final_main=0,
                initial_cb1=0x0808CBDD,final_cb1=0x081C7589,
                initial_cb2=0x0808F225,final_cb2=0x081C9FC5,
                initial_pp=[20,10,10,20],final_pp=[19 if pp else 20,10,10,20],
                events=rows)

class OriginalJoinTests(unittest.TestCase):
    def test_complete_mock_correlates_but_not_promotes(self):
        x=v.audit(fixture())
        self.assertEqual(x["full_marker_sequence_candidates"],1)
        self.assertEqual(x["attributed_original_pp_writer_candidates"],1)
        self.assertEqual(x["main_clear_precedes_later_callback_in_same_run"],1)
        self.assertFalse(x["original_outcome_writer_pc_certified"])
        self.assertFalse(x["full_native_terminal_certified"])
        self.assertFalse(x["production_promotion_authorized"])
    def test_missing_pp_remains_unclassified(self):
        x=v.audit(fixture(pp=False))
        self.assertEqual(x["original_emissions_without_attributed_pp_writer"],1)
        self.assertFalse(x["unmatched_pp_cause_certified"])
    def test_empty_window_no_proof(self):
        d=fixture(pp=False);d["events"]=[];d["final_main"]=2
        d["final_cb1"]=d["initial_cb1"];d["final_cb2"]=d["initial_cb2"]
        x=v.audit(d);self.assertEqual(x["original_actor0_emitter_candidates"],0)
    def reject(self,fn):
        x=fixture();fn(x)
        with self.assertRaises(ValueError):v.audit(x)
    def test_disallow_guest_writes(self):self.reject(lambda x:x.update(guest_writes=1))
    def test_disallow_host_move_input(self):self.reject(lambda x:x.update(host_move_menu_inputs=1))
    def test_disallow_hook(self):self.reject(lambda x:x.update(new_hook_installed=True))
    def test_wrong_current(self):self.reject(lambda x:x.update(current_sha256="bad"))
    def test_wrong_modified(self):self.reject(lambda x:x.update(modified_sha256="bad"))
    def test_wrong_save(self):self.reject(lambda x:x.update(save_sha256="bad"))
    def test_wrong_schema(self):self.reject(lambda x:x.update(schema="v0"))
    def test_private_field(self):self.reject(lambda x:x.update(raw_private_rom=b"bad"))
    def test_trace_overflow(self):self.reject(lambda x:x.update(status=3))
    def test_budget_exhausted(self):self.reject(lambda x:x.update(status=2))
    def test_invalid_frame(self):self.reject(lambda x:x.update(end_frame=3201))
    def test_bad_step(self):self.reject(lambda x:x["events"][3].update(step=100))
    def test_bad_order(self):self.reject(lambda x:x["events"].reverse())
    def test_bad_event_field(self):self.reject(lambda x:x["events"][0].update(raw="private"))
    def test_bool_not_int(self):self.reject(lambda x:x["events"][0].update(frame=True))
    def test_bad_original_emit_pc(self):self.reject(lambda x:x["events"][0].update(pc=0x0809E6BA))
    def test_bad_move_action(self):self.reject(lambda x:x["events"][0].update(r2=9))
    def test_wrong_target(self):self.reject(lambda x:x["events"][0].update(r3=0))
    def test_untrusted_player_battler(self):self.reject(lambda x:x["events"][0].update(r0=1))
    def test_emitter_after_main_clear(self):self.reject(lambda x:x["events"][0].update(inbattle=0))
    def test_validator_wrong_owner(self):self.reject(lambda x:x["events"][3].update(r0=1))
    def test_wrong_native_slot_commit(self):self.reject(lambda x:x["events"][4].update(r0=2))
    def test_wrong_native_move_id(self):self.reject(lambda x:x["events"][5].update(r0=157))
    def test_wrong_native_target_commit(self):self.reject(lambda x:x["events"][6].update(r2=0))
    def test_not_real_pp_pointer(self):self.reject(lambda x:x["events"][7].update(address=v.PP+1))
    def test_pp_chain_mismatch(self):self.reject(lambda x:x["events"][7].update(before=18))
    def test_missing_pp_write_not_silent(self):self.reject(lambda x:x["events"].pop(7))
    def test_fake_main_bit(self):self.reject(lambda x:x["events"][8].update(after=3))
    def test_no_main_write(self):self.reject(lambda x:x["events"].pop(8))
    def test_missing_callback1(self):self.reject(lambda x:x["events"].pop(9))
    def test_missing_callback2(self):self.reject(lambda x:x["events"].pop(10))
    def test_callback1_before_bad(self):self.reject(lambda x:x["events"][9].update(before=0))
    def test_callback2_before_bad(self):self.reject(lambda x:x["events"][10].update(before=0))
    def test_main_final_mismatch(self):self.reject(lambda x:x.update(final_main=2))
    def test_cb_final_mismatch(self):self.reject(lambda x:x.update(final_cb2=0))
    def test_pp_final_mismatch(self):self.reject(lambda x:x.update(final_pp=[20,10,10,20]))
    def test_wrong_callback_address(self):self.reject(lambda x:x["events"][9].update(address=v.CB2))
    def test_wrong_store_stage(self):self.reject(lambda x:x["events"][8].update(stage=0))
    def test_wrong_marker_stage(self):self.reject(lambda x:x["events"][0].update(stage=1))
    def test_pp_changes_not_writer_counted(self):
        x=fixture()
        x["events"][7].update(pc=0x081FB8DA)
        y=v.audit(x)
        self.assertEqual(y["original_native_pp_writer_events"],0)
        self.assertEqual(y["non_writer_pp_byte_mutations"],1)
    def test_incomplete_marker_chain_not_execution(self):
        x=fixture()
        x["events"][2].update(pc=v.MARKERS[4],kind=4)
        y=v.audit(x)
        self.assertEqual(y["full_marker_sequence_candidates"],0)
        self.assertEqual(y["attributed_original_pp_writer_candidates"],0)
    def test_disallow_manual_menu_marker(self):
        x=fixture()
        x["events"].insert(7,event(7,8))
        with self.assertRaises(ValueError):v.audit(x)

if __name__=="__main__":unittest.main()
