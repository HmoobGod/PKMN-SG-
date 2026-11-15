#!/usr/bin/env python3
"""Generated fake original CPU events only; NEVER run private original game."""
import copy
import unittest
import triage_original_actor0_terminal_joint as joint
from test_original_actor0_marker_chain import synthetic
from test_exact_outcome_pp_edges import row
from verify_exact_outcome_pp_edges import MAIN

ADDR=0x02004020

def complete_fixture():
    d=synthetic()
    d["candidate_outcome_byte_address"]=ADDR
    d["events"].append(row(1,18,0x08101234,ADDR,0,1,
                           r1=ADDR,r6=1,opcode=0x700E))
    cb1=next(e for e in d["events"] if e["kind"]==3)
    cb2=next(e for e in d["events"] if e["kind"]==4)
    cb1.update(opcode=0x6001,r0=MAIN,r1=cb1["after"])
    cb2.update(opcode=0x6001,r0=MAIN+4,r1=cb2["after"])
    d["events"].sort(key=lambda x:x["step"])
    return d

def same_step_stmia_fixture():
    d=complete_fixture()
    cb1=next(e for e in d["events"] if e["kind"]==3)
    cb2=next(e for e in d["events"] if e["kind"]==4)
    cb2["step"]=cb1["step"]
    cb2["frame"]=cb1["frame"]
    # STMIA r0!, {r1,r2}: r0=Main, r1=callback1, r2=callback2.
    # Two poststep watchers must share exact PRE CPU registers/opcode,
    # while both poststep context snapshots must show BOTH new pointers.
    common=dict(pc=0x0808E33C,opcode=0xC006,
                r0=MAIN,r1=cb1["after"],r2=cb2["after"],r3=0,r4=MAIN,
                callback1=cb1["after"],callback2=cb2["after"])
    cb1.update(common)
    cb2.update(common)
    d["events"].sort(key=lambda e:e["step"])
    return d

def witness(d):
    return joint.evaluate(d)["joined_actor0_pp_result_main_callback_candidate_UNVERIFIED"]

class JointWitnessTests(unittest.TestCase):
    def test_original_stmia_same_cpu_step_callback_pair_unverified(self):
        d=same_step_stmia_fixture()
        z=joint.evaluate(d)
        self.assertTrue(z["same_original_cpu_step_stmia_callback_pair_UNVERIFIED"])
        self.assertTrue(z["exactly_one_ordered_full32_callback_wordstore_pair_UNVERIFIED"])
        self.assertTrue(witness(d))
        self.assertFalse(z["original_overworld_callback_execution_certified"])
        self.assertEqual(z["original_native_acceptance_scenarios"],0)

    def test_stmia_pair_rejects_wrong_word_source(self):
        d=same_step_stmia_fixture()
        for row_to_mutate in (3,4):
            with self.subTest(kind=row_to_mutate):
                x=copy.deepcopy(d)
                rows=[e for e in x["events"] if e["kind"] in (3,4)]
                for e in rows:
                    e["r2"] ^= 4
                self.assertFalse(witness(x))

    def test_stmia_pair_rejects_ldmia_base_in_list_or_empty_registers(self):
        for opcode in (0xC806,0xC007,0xC000):
            with self.subTest(opcode=hex(opcode)):
                d=same_step_stmia_fixture()
                for e in d["events"]:
                    if e["kind"] in (3,4):
                        e["opcode"]=opcode
                self.assertFalse(witness(d))

    def test_stmia_pair_rejects_misalignment_and_32bit_wrap(self):
        for base in (MAIN+1,0xFFFFFFFC):
            with self.subTest(base=base):
                d=same_step_stmia_fixture()
                for e in d["events"]:
                    if e["kind"] in (3,4):
                        e["r0"]=base
                self.assertFalse(witness(d))

    def test_same_cpu_step_two_str_writes_cannot_be_accepted(self):
        d=same_step_stmia_fixture()
        for e in d["events"]:
            if e["kind"] in (3,4):
                e["opcode"]=0x6001
        self.assertFalse(witness(d))

    def test_stmia_pair_requires_identical_pre_cpu_opcode_registers(self):
        d=same_step_stmia_fixture()
        next(e for e in d["events"] if e["kind"]==4)["r3"]=123
        with self.assertRaisesRegex(ValueError,"split or forged"):
            joint.evaluate(d)

    def test_generated_full_chain_never_certifies_native(self):
        z=joint.evaluate(complete_fixture())
        self.assertTrue(z["joined_actor0_pp_result_main_callback_candidate_UNVERIFIED"])
        self.assertFalse(z["original_outcome_byte_address_authenticated"])
        self.assertFalse(z["original_engine_one_use_actor0_request_certified"])
        self.assertFalse(z["original_move_target_legality_certified"])
        self.assertFalse(z["original_pp_execution_or_cancellation_certified"])
        self.assertFalse(z["original_outcome_decision_pc_certified"])
        self.assertFalse(z["original_overworld_callback_execution_certified"])
        self.assertEqual(z["original_native_acceptance_scenarios"],0)
        self.assertFalse(z["production_authorized"])
    def test_missing_any_key_actor_stage_fails_closed(self):
        for kind in (6,7,13,14,15,16,12,5):
            with self.subTest(kind=kind):
                d=complete_fixture()
                d["events"]=[e for e in d["events"] if e["kind"]!=kind]
                self.assertFalse(witness(d))
    def test_missing_terminal_transition_fails(self):
        for kind in (1,2,3,4):
            with self.subTest(kind=kind):
                d=complete_fixture()
                d["events"]=[e for e in d["events"] if e["kind"]!=kind]
                self.assertFalse(witness(d))
    def test_invalid_result_writer_opcode_fails(self):
        d=complete_fixture()
        next(e for e in d["events"] if e["kind"]==1)["opcode"]=0x780E
        self.assertFalse(witness(d))
    def test_result_before_pp_fails(self):
        d=complete_fixture()
        e=next(e for e in d["events"] if e["kind"]==1)
        e.update(step=10,frame=3980+10//4)
        d["events"].sort(key=lambda x:x["step"])
        self.assertFalse(witness(d))
    def test_result_after_main_exit_fails(self):
        d=complete_fixture()
        e=next(e for e in d["events"] if e["kind"]==1)
        e.update(step=22,frame=3980+22//4)
        d["events"].sort(key=lambda x:x["step"])
        self.assertFalse(witness(d))
    def test_callback_writer_unknown_source_fails(self):
        d=complete_fixture()
        next(e for e in d["events"] if e["kind"]==3)["r1"]^=4
        self.assertFalse(witness(d))
    def test_callback_wrong_kind_order_fails(self):
        d=complete_fixture()
        a=next(e for e in d["events"] if e["kind"]==3)
        b=next(e for e in d["events"] if e["kind"]==4)
        a["step"],b["step"]=b["step"],a["step"]
        a["frame"],b["frame"]=b["frame"],a["frame"]
        d["events"].sort(key=lambda x:x["step"])
        self.assertFalse(witness(d))
    def test_extra_result_transition_fails(self):
        d=complete_fixture()
        d["events"].append(row(1,19,0x08109990,ADDR,1,2,
                               r1=ADDR,r6=2,opcode=0x780E))
        d["events"].sort(key=lambda x:x["step"])
        self.assertFalse(witness(d))
    def test_manual_marker_before_terminal_fails(self):
        d=complete_fixture()
        d["events"].append(row(8,14,0x0806449C))
        d["events"].sort(key=lambda x:x["step"])
        self.assertFalse(witness(d))
    def test_second_emitter_not_laundered_as_one_action(self):
        d=complete_fixture()
        d["events"].append(row(6,13,0x0806BD80,r0=0,r2=10))
        d["events"].sort(key=lambda x:x["step"])
        self.assertFalse(witness(d))
    def test_genuine_pp_lack_stays_unclassified(self):
        d=complete_fixture()
        d["events"]=[e for e in d["events"] if e["kind"]!=5]
        self.assertFalse(witness(d))
        self.assertFalse(joint.evaluate(d)["original_pp_execution_or_cancellation_certified"])
    def test_original_private_identity_fields_fail_schema(self):
        for mutate in (lambda d:d.update(guest_writes=1),
                       lambda d:d["events"][0].update(opcode=True),
                       lambda d:d.update(production_authorized=True)):
            d=complete_fixture()
            mutate(d)
            with self.assertRaises((ValueError,TypeError)):
                joint.evaluate(d)

if __name__=="__main__":
    unittest.main()
