#!/usr/bin/env python3
"""Source-only real-C-observer -> strict Python-audit negative integration.

Synthetic public FAKE core generated inside C tests. Hash values in the
Python audit envelope are placeholders for TEST SCHEMA compatibility only:
this test calls audit(), NEVER attest(), never opens protected ROM/save, and
does not claim the event sequence came from the original game.
"""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import verify_exact_joint_player_terminal as v

TOOLS = Path(__file__).resolve().parent
SRC = TOOLS / "test_exact_joint_c_to_python_bridge.c"
MODES = ("baseline", "flags0", "battlers0", "main0",
         "no_pp", "slot1_delta3", "main_bit0")
BRIDGE_SCHEMA = "sg-public-synthetic-joint-c-v1"


class RealCToPythonAuditBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix="public-sg-joint-c-audit-")
        cls.exe = Path(cls.work.name) / "fake-joint-c"
        subprocess.run(("cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-pedantic", "-O2", str(SRC), "-o", str(cls.exe)),
                       check=True, capture_output=True, text=True)
        cls.output = {}
        for mode in MODES:
            result = subprocess.run((str(cls.exe), mode), check=True,
                                    capture_output=True, text=True, timeout=5)
            cls.output[mode] = json.loads(result.stdout)

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def c_output(self, mode):
        raw = copy.deepcopy(self.output[mode])
        self.assertEqual(raw["schema"], BRIDGE_SCHEMA)
        self.assertEqual(raw["mode"], mode)
        self.assertEqual(set(raw), {"schema", "mode", "run", "events"})
        self.assertEqual(set(raw["run"]), {
            "status", "start_frame", "end_frame", "window_frames", "steps",
            "initial_main", "final_main", "initial_cb1", "final_cb1",
            "initial_cb2", "final_cb2", "initial_pp", "final_pp"})
        for row in raw["events"]:
            self.assertEqual(set(row), v.FIELDS)
        return raw

    def audit_input(self, mode):
        public = self.c_output(mode)
        # Only synthetic test schema labels: no ROM file, no original opcode
        # attestation and no claim that private image hashes were witnessed.
        record = dict(public["run"])
        record.update(
            schema=v.SCHEMA, current_sha256=v.CURRENT,
            modified_sha256=v.MODIFIED, save_sha256=v.SAVE,
            new_hook_installed=False, guest_writes=0,
            host_move_menu_inputs=0, events=public["events"])
        self.assertEqual(set(record), v.TOP)
        return record

    def test_c_observer_baseline_round_trip_descriptive_only(self):
        result = v.audit(self.audit_input("baseline"))
        self.assertEqual(result["original_actor0_emitter_candidates"], 1)
        self.assertEqual(result["full_marker_sequence_candidates"], 1)
        self.assertEqual(result["attributed_original_pp_writer_candidates"], 1)
        self.assertEqual(result["main_clear_precedes_later_callback_in_same_run"], 1)
        self.assertFalse(result["original_outcome_writer_pc_certified"])
        self.assertFalse(result["manual_fallback_certified"])
        self.assertFalse(result["production_promotion_authorized"])
        self.assertEqual(result["formal_native_gameplay_acceptance"], 0)

    def test_wrong_flags_battlers_and_main_are_rejected_from_actual_c(self):
        for mode in ("flags0", "battlers0", "main0"):
            with self.subTest(mode=mode):
                record = self.audit_input(mode)
                with self.assertRaises(ValueError):
                    v.audit(record)

    def test_actual_c_no_debit_cannot_create_pp_attribution(self):
        record = self.audit_input("no_pp")
        self.assertEqual(record["initial_pp"][0], record["final_pp"][0])
        self.assertFalse(any(e["kind"]==9 for e in record["events"]))
        result = v.audit(record)
        self.assertEqual(result["original_native_pp_writer_events"], 0)
        self.assertEqual(result["attributed_original_pp_writer_candidates"], 0)
        self.assertEqual(result["original_emissions_without_attributed_pp_writer"], 1)
        self.assertFalse(result["unmatched_pp_cause_certified"])

    def test_actual_c_slot1_nonunit_delta_not_authenticated_debit(self):
        record = self.audit_input("slot1_delta3")
        writer = [e for e in record["events"] if e["kind"]==9]
        self.assertEqual(len(writer),1)
        self.assertEqual(writer[0]["pc"],v.WRITER)
        self.assertEqual(writer[0]["slot"],1)
        self.assertEqual(writer[0]["address"],v.PP+1)
        self.assertEqual((writer[0]["before"],writer[0]["after"]),(10,7))
        self.assertEqual(writer[0]["r1"],v.PP+1)
        result = v.audit(record)
        self.assertEqual(result["original_native_pp_writer_events"],0)
        self.assertEqual(result["non_writer_pp_byte_mutations"],1)
        self.assertEqual(result["attributed_original_pp_writer_candidates"],0)
        self.assertFalse(result["unmatched_pp_cause_certified"])

    def test_actual_c_main_bit0_only_does_not_make_terminal(self):
        record = self.audit_input("main_bit0")
        self.assertEqual((record["initial_main"],record["final_main"]),(2,3))
        self.assertFalse(any(e["kind"]==10 for e in record["events"]))
        result = v.audit(record)
        self.assertEqual(result["main_clear_edges"],0)
        self.assertEqual(result["main_clear_precedes_later_callback_in_same_run"],0)
        self.assertFalse(result["full_native_terminal_certified"])

    def test_tampering_c_events_does_not_pass_audit(self):
        for mode, mutate in (
            ("baseline", lambda d:d["events"].reverse()),
            ("baseline", lambda d:d["events"][7].update(address=v.PP+2)),
            ("baseline", lambda d:d.update(final_pp=[20,10,10,20])),
            ("baseline", lambda d:d["events"][0].update(pc=0x08000000)),
            ("no_pp", lambda d:d["events"].append({"raw_private_bytes":"forbidden"})),
        ):
            with self.subTest(mode=mode,mutation=str(mutate)):
                d=self.audit_input(mode)
                mutate(d)
                with self.assertRaises((ValueError,TypeError,KeyError)):
                    v.audit(d)

    def test_subprocess_mode_whitelist_and_ndebug_guard(self):
        bad = subprocess.run((str(self.exe),"private-rom.sav"),
                             capture_output=True, text=True, timeout=5)
        self.assertEqual(bad.returncode,2)
        no_assert = subprocess.run(
            ("cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
             "-DNDEBUG", "-fsyntax-only", str(SRC)),
            capture_output=True,text=True,timeout=10)
        self.assertNotEqual(no_assert.returncode,0)
        self.assertIn("requires enabled assertions",no_assert.stderr)


if __name__ == "__main__":
    unittest.main()
