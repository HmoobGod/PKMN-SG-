#!/usr/bin/env python3
"""Use ACTUAL read-only 44-byte C recorder output to drive a Python gate.

Every C fixture contains FAKE CPU state; this is never authentic private
ROM/save execution, instruction attestation, gameplay or native acceptance.
"""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import verify_public_player0_request_copy as v

TOOLS = Path(__file__).resolve().parent
C_FIXTURE = TOOLS / "test_player0_request_copy_json_fixture.c"
MODES = ("valid", "skipped_store", "bad_opcode", "wrapped_buffer",
         "wrong_register", "frame_rollback", "short_budget", "missing_callback",
         "preexisting_equal", "opcode_drift", "transient_dest",
         "transient_source")


class OriginalCopyProofRoundTrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix="public-sg-request-copy-")
        cls.binary = str(Path(cls.work.name) / "request-copy-fake")
        subprocess.run(("cc", "-std=c11", "-Wall", "-Wextra",
                        "-Werror", "-pedantic", "-O2", str(C_FIXTURE),
                        "-o", cls.binary), check=True,
                       capture_output=True, text=True)
        cls.records = {}
        for mode in MODES:
            x = subprocess.run((cls.binary, mode), capture_output=True,
                               text=True, timeout=5, check=True)
            cls.records[mode] = json.loads(x.stdout)

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def test_full_real_c_recorder_public_round_trip(self):
        rec = self.records["valid"]
        result = v.audit_public_fixture(rec)
        self.assertTrue(result["internally_consistent_44_byte_player0_copy_candidate"])
        self.assertFalse(result["original_modified_rom_instruction_pc_attested"])
        self.assertFalse(result["engine_owned_one_use_request_epoch_certified"])
        self.assertFalse(result["effective_move_target_legality_certified"])
        self.assertFalse(result["real_player0_auto_move_or_pp_debit_certified"])
        self.assertFalse(result["native_battle_outcome_or_overworld_return_certified"])
        self.assertFalse(result["manual_fallback_certified"])
        self.assertFalse(result["production_promotion_authorized"])
        self.assertEqual(result["native_acceptance_scenarios"], 0)
        p = rec["proof"]
        self.assertEqual((p["stores"], p["total_steps"], p["length"]), (44, 45, 44))
        self.assertEqual(p["source_before"][0], 19)
        self.assertTrue(result["all_44_poststep_destination_changes_witnessed_in_fixture"])
        self.assertTrue(result["public_fake_cpu_opcode_triplet_recorded"])
        self.assertEqual((p["entry_insn"],p["store_insn"],p["post_insn"]),
                         (0x2101,0x7003,0x4718))
        self.assertTrue(all(before != after for before, after in
                            zip(p["dest_before"], p["store_values"])))

    def test_all_real_c_error_modes_refused_by_python_gate(self):
        for mode in MODES[1:]:
            with self.subTest(mode=mode):
                rec = self.records[mode]
                self.assertNotEqual((rec["proof"]["state"], rec["proof"]["error"]),
                                    (2, 0))
                with self.assertRaises(ValueError):
                    v.audit_public_fixture(rec)

    def test_intermediate_corruption_detected_before_postloop(self):
        for mode, code in (("transient_dest",12),("transient_source",13)):
            with self.subTest(mode=mode):
                p=self.records[mode]["proof"]
                self.assertEqual(p["stores"],7)
                self.assertEqual(p["error"],code)
                self.assertNotEqual(p["state"],2)
                with self.assertRaises(ValueError):
                    v.audit_public_fixture(self.records[mode])

    def test_unrecognized_mode_binary_and_python_denied(self):
        p = subprocess.run((self.binary, "private-rom.sav"),
                           capture_output=True, text=True, timeout=5)
        self.assertEqual(p.returncode, 2)
        rec = copy.deepcopy(self.records["valid"])
        rec["mode"] = "real_game"
        with self.assertRaises(ValueError):
            v.audit_public_fixture(rec)
        rec["mode"] = "valid"
        rec["bridge_schema"] = "sg-native-player0-certified"
        with self.assertRaises(ValueError):
            v.audit_public_fixture(rec)

    def test_mutated_successful_c_proof_rejected(self):
        mutants = (
            lambda p: p.update(state=1),
            lambda p: p.update(error=7),
            lambda p: p.update(actor=1),
            lambda p: p.update(direction=1),
            lambda p: p.update(length=43),
            lambda p: p.update(stores=43),
            lambda p: p.update(total_steps=46),
            lambda p: p.update(opcode_post=0),
            lambda p: p.update(source=0),
            lambda p: p.update(dest=0x01FFFFF0),
            lambda p: p.update(dest=p["source"]+1),
            lambda p: p.update(entry_frame=p["post_frame"]+1),
            lambda p: p.update(end_frame=p["begin_frame"]-1),
            lambda p: p.update(post_sp=p["entry_sp"]),
            lambda p: p.update(post_lr=p["entry_lr"]+1),
            lambda p: p.update(tag=0),
            lambda p: p.update(entry_insn=0),
            lambda p: p.update(store_insn=65536),
            lambda p: p.update(post_insn=True),
            lambda p: p.update(actor=True),
            lambda p: p["source_before"].__setitem__(0, 18),
            lambda p: p["source_after"].__setitem__(9, 71),
            lambda p: p["dest_after"].__setitem__(7, 71),
            lambda p: p["store_values"].__setitem__(15, 71),
            lambda p: p["store_indices"].__setitem__(8, 7),
            lambda p: p["store_indices"].reverse(),
            lambda p: p["store_indices"].pop(),
            lambda p: p["dest_before"].__setitem__(7,p["store_values"][7]),
            lambda p: p["dest_before"].pop(),
            lambda p: p["source_before"].pop(),
            lambda p: p.update(extra_private_bytes="forbidden"),
        )
        for i, mutate in enumerate(mutants):
            with self.subTest(mutant=i):
                rec = copy.deepcopy(self.records["valid"])
                mutate(rec["proof"])
                with self.assertRaises(ValueError):
                    v.audit_public_fixture(rec)

    def test_public_fake_opcode_image_parity_is_not_game_attestation(self):
        p = self.records["valid"]["proof"]
        fake_image = bytearray(0x200000)
        for key,pc in (("entry_insn",v.ORIGINAL_ENTRY_PC),
                       ("store_insn",v.ORIGINAL_STORE_PC),
                       ("post_insn",v.ORIGINAL_POST_PC)):
            off=pc-0x08000000
            fake_image[off:off+2]=p[key].to_bytes(2,"little")
        self.assertTrue(v.verify_public_opcode_triplet_against_image(p, fake_image))
        self.assertFalse(v.audit_public_fixture(self.records["valid"])[
            "original_modified_rom_instruction_pc_attested"])
        for key,pc in (("entry_insn",v.ORIGINAL_ENTRY_PC),
                       ("store_insn",v.ORIGINAL_STORE_PC),
                       ("post_insn",v.ORIGINAL_POST_PC)):
            with self.subTest(key=key):
                off=pc-0x08000000
                fake_image[off]^=1
                with self.assertRaisesRegex(ValueError,"CPU opcode triplet"):
                    v.verify_public_opcode_triplet_against_image(p,fake_image)
                fake_image[off]^=1
        with self.assertRaisesRegex(ValueError,"image missing"):
            v.verify_public_opcode_triplet_against_image(p,bytearray(100))

    def test_ndebug_and_private_cli_fail_closed(self):
        bad = subprocess.run(("cc", "-std=c11", "-Wall", "-Wextra",
                              "-Werror", "-pedantic", "-DNDEBUG",
                              "-fsyntax-only", str(C_FIXTURE)),
                             capture_output=True, text=True, timeout=10)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("requires assertions", bad.stderr)
        cli = subprocess.run(("python3",
                              str(TOOLS/"verify_public_player0_request_copy.py"),
                              "--private", "/tmp/none"),
                             capture_output=True, text=True, timeout=5)
        self.assertNotEqual(cli.returncode, 0)
        self.assertIn("no private input", cli.stderr)


if __name__ == "__main__":
    unittest.main()
