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
        row(2,20,0x081C1234, v.MAIN+0x439,2,0),
        row(3,24,0x0808E33C,v.MAIN,0x0808CBDD,0x081C7589,
            r4=v.MAIN,callback1=0x081C7589),
        row(4,27,0x081AED58,v.MAIN+4,0x0808F225,0x080C4265,
            r3=v.MAIN,callback2=0x080C4265),
    ]
    return data


class ExactOutcomePpEdgeTests(unittest.TestCase):
    @staticmethod
    def shared_step_pair():
        d=fixture()
        # Marker is PRE-step; FLAGS watcher fires POST-step. Same C CPU
        # snapshot, but changed RAM/context fields need not be identical.
        d["events"].insert(1,row(9,1,0x0806BD80,0x02001AB4,4,5,
                                 r0=0,r2=10))
        return d

    def test_original_marker_and_memory_change_share_one_cpu_step(self):
        d=self.shared_step_pair()
        result=v.audit(d)
        self.assertEqual(result["original_player_emit_markers"],1)
        self.assertFalse(result["one_use_request_ownership_certified"])

    def test_same_step_opcode_disagreement_denied(self):
        d=self.shared_step_pair()
        d["events"][1]["opcode"]=0xBEEF
        with self.assertRaisesRegex(ValueError,"split or forged"):
            v.audit(d)

    def test_same_step_register_disagreement_denied(self):
        d=self.shared_step_pair()
        d["events"][1]["r4"]=0x42
        with self.assertRaisesRegex(ValueError,"split or forged"):
            v.audit(d)

    def test_same_step_frame_disagreement_denied(self):
        d=self.shared_step_pair()
        d["events"][1]["frame"]+=1
        with self.assertRaisesRegex(ValueError,"split or forged"):
            v.audit(d)

    def test_trace_supplied_promotion_key_denied(self):
        self.denied(lambda d:d.update(production_promotion_authorized=True))

    def test_boolean_guest_write_field_denied(self):
        self.denied(lambda d:d.update(guest_writes=False))

    def test_boolean_status_field_denied(self):
        self.denied(lambda d:d.update(status=True))

    def test_version_one_lacks_per_event_opcode_provenance(self):
        self.denied(lambda d:d.update(schema="sg-original-outcome-pp-instruction-edges-v1"))
    def test_missing_original_opcode_on_native_main_clear(self):
        self.denied(lambda d:d["events"][3].pop("opcode"))
    def test_unknown_zero_pc_main_transition_does_not_claim_terminal(self):
        self.denied(lambda d:d["events"][3].update(pc=0,opcode=0))
    def test_ram_pc_on_original_outcome_observation_rejected(self):
        self.denied(lambda d:d["events"][3].update(pc=v.MAIN+0x200))
    def test_odd_original_rom_pc_rejected(self):
        self.denied(lambda d:d["events"][3].update(pc=0x081C1235))
    def test_oversized_thumb_opcode_rejected(self):
        self.denied(lambda d:d["events"][3].update(opcode=0x10000))
    def test_opcode_bool_not_u32(self):
        self.denied(lambda d:d["events"][3].update(opcode=True))
    def test_each_observed_original_pc_is_byte_checked(self):
        d=fixture()
        # PUBLIC synthetic instruction image only, no protected original
        # ROM, save, emulator or private auth hashes are touched.
        image=bytearray(0x200000)
        v.verify_original_event_opcodes(d["events"],image)
        for e in d["events"]:
            with self.subTest(kind=e["kind"],pc=e["pc"]):
                image[e["pc"]-0x08000000]=0xA5
                with self.assertRaisesRegex(ValueError,"CPU opcode parity"):
                    v.verify_original_event_opcodes(d["events"],image)
                image[e["pc"]-0x08000000]=0
        with self.assertRaisesRegex(ValueError,"outside byte-pinned"):
            v.verify_original_event_opcodes(d["events"],bytearray(1024))
    def test_original_writer_pc_alone_never_certifies_real_outcome(self):
        d=fixture()
        d["events"][2]["opcode"]=0x700E
        report=v.audit(d)
        self.assertEqual(report["original_pp_writer_single_byte_debits_seen"],1)
        self.assertFalse(report["original_battle_outcome_decision_pc_certified"])
        self.assertFalse(report["full_native_terminal_certified"])
        self.assertFalse(report["production_promotion_authorized"])

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
    def test_candidate_not_pp_alias(self):self.denied(lambda d:d.update(candidate_outcome_byte_address=v.PP))
    def test_candidate_not_flags_alias(self):self.denied(lambda d:d.update(candidate_outcome_byte_address=0x02001AB5))
    def test_candidate_not_pending_alias(self):self.denied(lambda d:d.update(candidate_outcome_byte_address=0x02001D2D))
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
    def test_actor0_complete_marker(self):
        d=fixture();d["events"].insert(2,row(12,5,0x0806261C,r0=0))
        self.assertEqual(v.audit(d)["original_player_completion_markers"],1)
    def test_wrong_actor_completion_rejected(self):
        def change(d):d["events"].insert(2,row(12,5,0x0806261C,r0=1))
        self.denied(change)
    def test_wrong_validator_marker_pc(self):
        def change(d):d["events"].insert(2,row(13,5,0x08094332))
        self.denied(change)
    def test_native_slot_move_target_markers(self):
        d=fixture();d["events"][2:2]=[row(13,5,0x08094330),
                                      row(14,6,0x0809435C),
                                      row(15,7,0x08094374),
                                      row(16,8,0x08094380)]
        r=v.audit(d)
        self.assertEqual((r["original_validator_markers"],r["original_slot_commit_markers"],
                          r["original_move_commit_markers"],r["original_target_commit_markers"]),
                         (1,1,1,1))
    def test_manual_menu_marker_not_full_terminal(self):
        d=fixture();d["events"].append(row(8,32,0x0806449C))
        result=v.audit(d)
        self.assertEqual(result["manual_move_menu_markers"],1)
        self.assertFalse(result["full_native_terminal_certified"])

if __name__ == "__main__": unittest.main()
