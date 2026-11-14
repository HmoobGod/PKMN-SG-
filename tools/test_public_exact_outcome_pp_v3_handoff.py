#!/usr/bin/env python3
"""PUBLIC FAKE original PP C->Python edge handoff, no protected game access.

Compiles the real read-only C observer inside a fake CPU adapter and passes
the emitted 23-field JSON edges through the strict Python v3 auditor and a
separately frozen fake 2 MiB instruction image. No owner ROM/save/emulator.
"""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import verify_exact_outcome_pp_edges as v

ROOT=Path(__file__).resolve().parent
FAKE=ROOT/"public_exact_outcome_pp_v3_fake_json.c"
FIELDS=(
    "frame","step","pc","opcode","kind","address","before","after","slot",
    "r0","r1","r2","r3","r4","r5","r6","r7",
    "flags","battlers","pending","inbattle","callback1","callback2",
)


def public_c_events():
    with tempfile.TemporaryDirectory(prefix="sg-public-fake-v3-") as tmp:
        exe=Path(tmp)/"fake_observer"
        subprocess.run(["cc","-std=c11","-O0","-Wall","-Wextra","-Werror",
                        "-UNDEBUG",str(FAKE),"-o",str(exe)],
                       check=True,cwd=ROOT,capture_output=True,text=True)
        completed=subprocess.run([str(exe)],check=True,cwd=ROOT,
                                 capture_output=True,text=True)
        raw=completed.stdout
        result=json.loads(raw)
        if type(result) is not dict or set(result)!={"status","steps","events"}:
            raise ValueError("wrong PUBLIC fake C envelope")
        return result


def read_only_audit_envelope(fake):
    # These exact-identity LABELS are drawn from the source verifier's
    # constants solely to exercise the strict source-only schema; they are
    # NOT computed from, or attested to, any owner original ROM or save.
    return {
        "schema":v.SCHEMA,
        "current_sha256":v.CURRENT,
        "modified_sha256":v.MODIFIED,
        "save_sha256":v.SAVE,
        "guest_writes":0,
        "host_move_menu_inputs":0,
        "new_hook_installed":False,
        "candidate_outcome_byte_address":0,
        "status":fake["status"],
        "steps":fake["steps"],
        "events":copy.deepcopy(fake["events"]),
    }


def frozen_public_fake_image(events):
    # Test bytes are constructed only from the initial, immutable C rows.
    # Altering a subsequent event cannot alter this frozen comparison image.
    image=bytearray(0x200000)
    seen={}
    for e in events:
        off=e["pc"]-0x08000000
        if not 0<=off<len(image)-1:
            raise ValueError("public fake event lies outside fake ROM image")
        halfword=e["opcode"]
        if off in seen and seen[off]!=halfword:
            raise ValueError("C fake same PC supplied contradictory halfwords")
        seen[off]=halfword
        image[off:off+2]=halfword.to_bytes(2,"little")
    return bytes(image)


class OriginalOutcomePublicCToPythonHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake=public_c_events()
        cls.record=read_only_audit_envelope(cls.fake)
        cls.image=frozen_public_fake_image(cls.record["events"])

    def test_c_v3_schema_and_cpu_pre_step_snapshots(self):
        self.assertEqual(self.fake["status"],1)
        self.assertEqual(self.fake["steps"],3)
        rows=self.fake["events"]
        self.assertEqual(len(rows),3)
        for e in rows:
            self.assertEqual(set(e),set(FIELDS))
            self.assertEqual(set(e),v.FIELDS)
        self.assertEqual([(e["kind"],e["step"],e["opcode"]) for e in rows],
                         [(6,0,0x1234),(5,0,0x1234),(2,1,0x700E)])
        self.assertEqual(rows[0]["r5"],0x87654321)
        self.assertEqual(rows[1]["r5"],0x87654321)
        self.assertEqual(rows[2]["r5"],0x87654322)
        self.assertEqual(rows[0]["r6"],19)
        self.assertEqual(rows[2]["r6"],21)
        self.assertEqual(rows[0]["r7"],0xBAD5CAFE)
        self.assertEqual(rows[2]["r7"],0xBAD5CA01)

    def test_live_c_rows_pass_strict_python_and_fake_opcode_image(self):
        v.verify_original_event_opcodes(self.record["events"],self.image)
        report=v.audit(self.record)
        self.assertEqual(report["original_player_emit_markers"],1)
        self.assertEqual(report["original_pp_writer_single_byte_debits_seen"],0)
        self.assertEqual(report["other_player_pp_byte_changes_not_certified"],1)
        for key in ("one_use_request_ownership_certified",
                    "previous_two_pp_unmatched_submissions_classified",
                    "original_battle_outcome_decision_pc_certified",
                    "full_native_terminal_certified",
                    "production_promotion_authorized"):
            self.assertFalse(report[key],key)

    def test_same_cpu_step_opcodes_and_registers_cannot_split(self):
        for field,value in (("opcode",0x9999),("r6",42),("r7",0),
                            ("frame",1),("pc",0x08060000)):
            with self.subTest(field=field):
                d=copy.deepcopy(self.record)
                d["events"][1][field]=value
                with self.assertRaises(ValueError):
                    v.audit(d)

    def test_byte_attestation_uses_frozen_image_not_injected_trace(self):
        d=copy.deepcopy(self.record)
        d["events"][2]["opcode"]^=1
        with self.assertRaisesRegex(ValueError,"CPU opcode parity"):
            v.verify_original_event_opcodes(d["events"],self.image)
        changed=bytearray(self.image)
        changed[d["events"][0]["pc"]-0x08000000]^=0xFF
        with self.assertRaisesRegex(ValueError,"CPU opcode parity"):
            v.verify_original_event_opcodes(self.record["events"],changed)

    def test_fake_trace_has_no_privilege_or_native_promotion(self):
        for mutation in (lambda d:d.update(guest_writes=1),
                         lambda d:d.update(host_move_menu_inputs=1),
                         lambda d:d.update(new_hook_installed=True),
                         lambda d:d.update(production_promotion_authorized=True),
                         lambda d:d.update(status=2),
                         lambda d:d.update(schema="sg-original-outcome-pp-instruction-edges-v2"),
                         lambda d:d["events"][0].pop("r7")):
            d=copy.deepcopy(self.record)
            mutation(d)
            with self.assertRaises(ValueError):
                v.audit(d)


if __name__=="__main__":
    unittest.main()
