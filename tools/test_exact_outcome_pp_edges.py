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
        row(5,12,0x0809E6BA,v.PP,20,19,0,r1=v.PP,r6=19,opcode=0x700E),
        row(2,20,0x081C1234, v.MAIN+0x439,2,0,inbattle=0),
        row(3,24,0x0808E33C,v.MAIN,0x0808CBDD,0x081C7589,
            r4=v.MAIN,callback1=0x081C7589),
        row(4,27,0x081AED58,v.MAIN+4,0x0808F225,0x080C4265,
            r3=v.MAIN,callback2=0x080C4265),
    ]
    return data


class ExactOutcomePpEdgeTests(unittest.TestCase):
    def test_every_poststep_watcher_value_matches_live_snapshot(self):
        self.assertFalse(v.audit(fixture())["production_promotion_authorized"])
        for index, field in ((3,"inbattle"),(4,"callback1"),(5,"callback2")):
            with self.subTest(kind=fixture()["events"][index]["kind"]):
                d=fixture()
                d["events"][index][field]=d["events"][index]["before"]
                with self.assertRaisesRegex(ValueError,"poststep watcher"):
                    v.audit(d)
        for kind, field, address in ((9,"flags",0x02001AB4),
                                     (10,"pending",0x02001D2C)):
            with self.subTest(kind=kind):
                d=fixture()
                d["events"].insert(2,row(kind,5,0x08012340,address,4,5)
                                   if kind==9 else
                                   row(kind,5,0x08012340,address,0,1))
                with self.assertRaisesRegex(ValueError,"poststep watcher"):
                    v.audit(d)

    def test_changed_flag_and_pending_snapshots_succeed(self):
        d=fixture()
        d["events"].insert(2,row(9,5,0x08012340,0x02001AB4,4,5,flags=5))
        d["events"].insert(3,row(10,7,0x08012340,0x02001D2C,0,1,pending=1))
        self.assertFalse(v.audit(d)["full_native_terminal_certified"])

    def test_missing_watcher_intermediate_value_denied(self):
        d=fixture()
        d["events"].insert(2,row(9,5,0x08012340,0x02001AB4,4,5,flags=5))
        d["events"].insert(3,row(9,7,0x08012340,0x02001AB4,3,4,flags=4))
        with self.assertRaisesRegex(ValueError,"watcher chronology"):
            v.audit(d)

    def test_two_poststep_changes_on_same_cpu_step_agree(self):
        d=fixture()
        # One instruction changed both Main and Callback1; C emits one
        # poststep record for each. Same CPU snapshot and same final RAM
        # context even though their before/after bytes differ.
        a,b=d["events"][3],d["events"][4]
        b.update(step=a["step"],frame=a["frame"],pc=a["pc"],r4=a["r4"],
                 inbattle=0)
        a["callback1"]=b["after"]
        self.assertFalse(v.audit(d)["production_promotion_authorized"])
        b["pending"]=1
        with self.assertRaisesRegex(ValueError,"contradictory poststep"):
            v.audit(d)

    @staticmethod
    def shared_step_pair():
        d=fixture()
        # Marker is PRE-step; FLAGS watcher fires POST-step. Same C CPU
        # snapshot, but changed RAM/context fields need not be identical.
        d["events"].insert(1,row(9,1,0x0806BD80,0x02001AB4,4,5,
                                 r0=0,r2=10,flags=5))
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
        self.denied(lambda d:d.update(schema="sg-original-outcome-pp-instruction-edges-v2"))
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
        # Public fake image must contain the explicitly recorded synthetic
        # STRB halfword, not imply a zero opcode at every instruction PC.
        for e in d["events"]:
            off=e["pc"]-0x08000000
            image[off:off+2]=e["opcode"].to_bytes(2,"little")
        v.verify_original_event_opcodes(d["events"],image)
        for e in d["events"]:
            with self.subTest(kind=e["kind"],pc=e["pc"]):
                image[e["pc"]-0x08000000]=0xA5
                with self.assertRaisesRegex(ValueError,"CPU opcode parity"):
                    v.verify_original_event_opcodes(d["events"],image)
                off=e["pc"]-0x08000000
                image[off:off+2]=e["opcode"].to_bytes(2,"little")
        with self.assertRaisesRegex(ValueError,"outside byte-pinned"):
            v.verify_original_event_opcodes(d["events"],bytearray(1024))
    def test_thumb_strb_immediate_effective_address(self):
        regs=(0,v.PP,0,0,0,0,v.PP+1,v.PP)
        self.assertEqual(v.observed_thumb_strb_address(0x700E,regs),v.PP)
        self.assertEqual(v.observed_thumb_strb_address(0x704E,regs),v.PP+1)
        # Newly recorded r5..r7 are legitimate original Thumb-1 low regs.
        self.assertEqual(v.observed_thumb_strb_address(0x703E,regs),v.PP)
        self.assertEqual(v.observed_thumb_strb_address(0x7036,regs),v.PP+1)
        self.assertIsNone(v.observed_thumb_strb_address(0x780E,regs)) # LDRB
        self.assertIsNone(v.observed_thumb_strb_address(0x600E,regs)) # STR word
        # STRB r6,[r7,#1] cannot wrap a 32-bit effective address.
        self.assertIsNone(v.observed_thumb_strb_address(0x707E,
                          (0,0,0,0,0,0,0,0xFFFFFFFF)))
        with self.assertRaisesRegex(ValueError,"r0-r7"):
            v.observed_thumb_strb_address(0x700E,regs[:5])
        with self.assertRaisesRegex(ValueError,"r0-r7"):
            v.observed_thumb_strb_address(0x700E,
                (0,0,0,0,0,0,True,v.PP))

    def test_thumb_strb_register_offset_address(self):
        # Thumb STRB r3,[r0,r1] = 0x5443, address from the two
        # independently recorded PRE-step original CPU registers.
        regs=(v.PP-1,1,0,0,0,0,0,0)
        self.assertEqual(v.observed_thumb_strb_address(0x5443,regs),v.PP)
        self.assertIsNone(v.observed_thumb_strb_address(0x5C43,regs))
        self.assertEqual(v.observed_thumb_strb_address(0x54C3,regs),v.PP-1)
        self.assertIsNone(v.observed_thumb_strb_address(0x5443,
                         (0xFFFFFFFF,1,0,0,0,0,0,0)))
        # STRB r6,[r5,r7]: Rb=5, Rm=7, Rt=6 -> 0x55EE.
        high=(0,0,0,0,0,v.PP-1,19,1)
        self.assertEqual(v.observed_thumb_strb_address(0x55EE,high),v.PP)
        self.assertIsNone(v.observed_thumb_strb_address(0x55EE,
                               (0,0,0,0,0,0xFFFFFFFF,19,1)))

    def test_pp_writer_full_low_register_address_is_only_candidate(self):
        for opcode, regs in (
            (0x703E,{"r7":v.PP,"r6":19}),
            (0x55EE,{"r5":v.PP-1,"r7":1,"r6":19}),
        ):
            with self.subTest(opcode=hex(opcode)):
                d=fixture()
                d["events"][2].update(opcode=opcode,**regs)
                result=v.audit(d)
                self.assertEqual(result["original_pp_writer_single_byte_debits_seen"],1)
                self.assertFalse(result["one_use_request_ownership_certified"])
                self.assertFalse(result["previous_two_pp_unmatched_submissions_classified"])
                self.assertFalse(result["full_native_terminal_certified"])
                self.assertFalse(result["production_promotion_authorized"])

    def test_pp_writer_delta_two_and_bad_high_register_deny(self):
        for opcode, vals in (
            (0x703E,{"r7":v.PP+1,"r6":19}),
            (0x703E,{"r7":v.PP,"r6":20}),
            (0x55EE,{"r5":0xFFFFFFFF,"r7":1,"r6":19}),
            (0x55EE,{"r5":v.PP-1,"r7":1,"r6":18}),
        ):
            with self.subTest(opcode=hex(opcode),registers=vals):
                d=fixture()
                d["events"][2].update(opcode=opcode,**vals)
                result=v.audit(d)
                self.assertEqual(result["original_pp_writer_single_byte_debits_seen"],0)
                self.assertEqual(result["other_player_pp_byte_changes_not_certified"],1)
        d=fixture()
        d["events"][2].update(before=21,after=19) # -2 is not -1
        result=v.audit(d)
        self.assertEqual(result["original_pp_writer_single_byte_debits_seen"],0)
        self.assertFalse(result["production_promotion_authorized"])

    def test_pp_writer_requires_strb_and_matching_effective_address(self):
        for opcode,regchange in ((0x0000,{}),(0x780E,{}),(0x704E,{}),
                                  (0x700E,{"r1":v.PP+1}),
                                  (0x7006,{}),(0x54C3,{})):
            with self.subTest(opcode=hex(opcode),registers=regchange):
                d=fixture()
                d["events"][2].update(opcode=opcode,**regchange)
                z=v.audit(d)
                self.assertEqual(z["original_pp_writer_single_byte_debits_seen"],0)
                self.assertEqual(z["other_player_pp_byte_changes_not_certified"],1)
                self.assertFalse(z["production_promotion_authorized"])

    def test_pp_writer_register_offset_is_only_candidate(self):
        d=fixture()
        d["events"][2].update(opcode=0x5443,r0=v.PP-1,r1=1,r3=19)
        z=v.audit(d)
        self.assertEqual(z["original_pp_writer_single_byte_debits_seen"],1)
        self.assertFalse(z["previous_two_pp_unmatched_submissions_classified"])
        self.assertFalse(z["one_use_request_ownership_certified"])

    @staticmethod
    def outcome_candidate_fixture(opcode=0x703E, **registers):
        # Public FAKE original EWRAM outcome candidate, NOT an authenticated
        # gBattleOutcome address or actual original ROM guest CPU result.
        d=fixture()
        candidate=0x02002345
        d["candidate_outcome_byte_address"]=candidate
        cpu={"r7":candidate,"r6":1,"opcode":opcode}
        cpu.update(registers)
        d["events"].insert(3,row(1,18,0x08012340,candidate,0,1,**cpu))
        return d

    def test_exact_thumb_strb_explains_only_candidate_byte_store(self):
        d=self.outcome_candidate_fixture()
        report=v.audit(d)
        self.assertEqual(report["candidate_outcome_byte_transitions"],1)
        self.assertEqual(report["candidate_outcome_strb_writer_matches_unverified"],1)
        self.assertEqual(report["candidate_outcome_unattributed_byte_transitions"],0)
        self.assertEqual(report["candidate_outcome_writer_pc_candidates_unverified"],
                         [0x08012340])
        # A genuine source-level byte STORE is NOT evidence the candidate
        # address is the real gBattleOutcome or that overworld returned.
        self.assertTrue(report["candidate_outcome_address_unverified"])
        self.assertFalse(report["original_battle_outcome_decision_pc_certified"])
        self.assertFalse(report["full_native_terminal_certified"])
        self.assertFalse(report["production_promotion_authorized"])

    def test_nonstore_wrong_source_target_or_overflow_is_unattributed(self):
        for op, regs in (
            (0x783E,{}),                   # LDRB not a STORE
            (0x603E,{}),                   # STR word not byte
            (0x703E,{"r6":2}),            # wrong Rt byte
            (0x703E,{"r7":0x02002346}),   # wrong effective address
            (0x55EE,{"r5":0xFFFFFFFF,
                      "r7":1,"r6":1}),    # register offset overflow
            (0x7000,{}),                   # zero base, not candidate
        ):
            with self.subTest(op=hex(op),regs=regs):
                report=v.audit(self.outcome_candidate_fixture(op,**regs))
                self.assertEqual(report["candidate_outcome_byte_transitions"],1)
                self.assertEqual(report["candidate_outcome_strb_writer_matches_unverified"],0)
                self.assertEqual(report["candidate_outcome_unattributed_byte_transitions"],1)
                self.assertEqual(report["candidate_outcome_writer_pc_candidates_unverified"],[])
                self.assertFalse(report["original_battle_outcome_decision_pc_certified"])

    def test_outcome_candidate_writer_pc_list_is_unique_and_chronological(self):
        d=self.outcome_candidate_fixture()
        d["events"].insert(4,row(
            1,19,0x08012340,d["candidate_outcome_byte_address"],1,2,
            opcode=0x703E,r7=d["candidate_outcome_byte_address"],r6=2))
        report=v.audit(d)
        self.assertEqual(report["candidate_outcome_byte_transitions"],2)
        self.assertEqual(report["candidate_outcome_strb_writer_matches_unverified"],2)
        self.assertEqual(report["candidate_outcome_unattributed_byte_transitions"],0)
        self.assertEqual(report["candidate_outcome_writer_pc_candidates_unverified"],
                         [0x08012340])
        self.assertFalse(report["full_native_terminal_certified"])

    def test_outcome_candidate_alone_does_not_invent_writer_or_terminal(self):
        report=v.audit(fixture())
        self.assertEqual(report["candidate_outcome_byte_transitions"],0)
        self.assertEqual(report["candidate_outcome_strb_writer_matches_unverified"],0)
        self.assertEqual(report["candidate_outcome_unattributed_byte_transitions"],0)
        self.assertEqual(report["candidate_outcome_writer_pc_candidates_unverified"],[])
        self.assertFalse(report["original_battle_outcome_decision_pc_certified"])

    def test_original_store_source_byte_from_full_cpu_r0_to_r7(self):
        registers=(0,v.PP,0,19,0,99,19,255)
        self.assertEqual(v.observed_thumb_strb_source_byte(0x700E,registers),19)
        self.assertEqual(v.observed_thumb_strb_source_byte(0x5443,registers),19)
        self.assertEqual(v.observed_thumb_strb_source_byte(0x700D,registers),99)
        self.assertEqual(v.observed_thumb_strb_source_byte(0x700F,registers),255)
        for op in (0x780E,0x600E,0x0000):
            self.assertIsNone(v.observed_thumb_strb_source_byte(op,registers))
        with self.assertRaisesRegex(ValueError,"r0-r7"):
            v.observed_thumb_strb_source_byte(0x700E,registers[:5])

    def test_thumb_source_byte_must_match_pp_after_value(self):
        for key,value in (("r6",18),("r6",20),("r6",0),("r6",0x100),
                          ("r6",0xFFFFFFFF)):
            with self.subTest(reg=key,value=value):
                d=fixture()
                d["events"][2][key]=value
                z=v.audit(d)
                self.assertEqual(z["original_pp_writer_single_byte_debits_seen"],0)
                self.assertEqual(z["other_player_pp_byte_changes_not_certified"],1)
                self.assertFalse(z["production_promotion_authorized"])
        d=fixture()
        d["events"][2]["r6"]=0x12340013  # low byte = 19
        self.assertEqual(v.audit(d)["original_pp_writer_single_byte_debits_seen"],1)

    def test_pp_source_register_mutation_same_cpu_step_denied(self):
        d=self.shared_step_pair()
        d["events"][1]["r6"]=11
        with self.assertRaisesRegex(ValueError,"split or forged"):
            v.audit(d)

    def test_v2_trace_missing_new_c_source_cpu_registers_denied(self):
        self.denied(lambda d:d.update(schema="sg-original-outcome-pp-instruction-edges-v2"))
        self.denied(lambda d:d["events"][2].pop("r7"))
        self.denied(lambda d:d["events"][2].update(r6=True))

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
    def test_candidate_not_battlers_alias(self):
        self.denied(lambda d:d.update(candidate_outcome_byte_address=0x02001AB8))
    def test_candidate_not_request_buffer_pointer_alias(self):
        for addr in range(0x02001C6C,0x02001C70):
            with self.subTest(addr=hex(addr)):
                self.denied(lambda d,addr=addr:
                            d.update(candidate_outcome_byte_address=addr))
    def test_known_reserved_alias_boundaries_agree_with_c(self):
        for addr in (0x02001AB9,0x02001C70,v.PP+4,0x02001D30,
                     0x02002345):
            with self.subTest(addr=hex(addr)):
                d=fixture()
                d["candidate_outcome_byte_address"]=addr
                report=v.audit(d)
                self.assertTrue(report["candidate_outcome_address_unverified"])
                self.assertFalse(report["original_battle_outcome_decision_pc_certified"])
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
