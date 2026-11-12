"""Synthetic-only Thumb-branch regression tests; never claims native execution."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import exact_rom_prestore_branch_scout as scout

BASE = 0x0808E200
SIZE = 512


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic"
        self.data = bytearray(SIZE)
        self.write_halfword(scout.STORE_PC, 0x5462)
        self.write_halfword(0x0808E31A, 0xD023)
        self.write_halfword(0x0808E322, 0xD11C)
        self.write_halfword(0x0808E324, 0xDE00)
        self.write_halfword(0x0808E326, 0xDF00)
        self.path.write_bytes(self.data)

    def write_halfword(self, pc, opcode):
        offset = pc - BASE
        self.data[offset:offset + 2] = opcode.to_bytes(2, "little")

    def fixture(self, changed=None):
        if changed is not None:
            self.path.write_bytes(changed)
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        return patch.multiple(scout, EXACT_ROM=digest, ROM_SIZE=SIZE, ROM_BASE=BASE)

    def test_forward_beq(self):
        self.assertEqual(scout.conditional_target(0x0808E31A, 0xD023), 0x0808E364)

    def test_forward_bne(self):
        self.assertEqual(scout.conditional_target(0x0808E322, 0xD11C), 0x0808E35E)

    def test_backward_branch(self):
        self.assertEqual(scout.conditional_target(0x0808E374, 0xD0D6), 0x0808E324)

    def test_conditional_exclusions_and_boundaries(self):
        for op in (0xDF00, 0xDE00, 0xE001, 0x5462, 0xF000):
            self.assertIsNone(scout.conditional_target(0x0808E31A, op))
        self.assertEqual(scout.conditional_target(0x0808E31A, 0xD07F), 0x0808E41C)
        self.assertEqual(scout.conditional_target(0x0808E31A, 0xD080), 0x0808E21E)

    def test_wrong_identity(self):
        with self.assertRaisesRegex(ValueError, "wrong exact"):
            scout.inspect(self.path)

    def test_protected_rom_refused(self):
        with patch.object(scout, "PROTECTED_ROM", hashlib.sha256(self.path.read_bytes()).hexdigest()):
            with self.assertRaisesRegex(ValueError, "protected"):
                scout.inspect(self.path)

    def test_success_branch_list_and_read_only(self):
        initial = self.path.read_bytes()
        with self.fixture():
            report = scout.inspect(self.path)
        self.assertEqual(self.path.read_bytes(), initial)
        self.assertEqual(report["classification"], "STATIC_BRANCH_BYTES_NOT_OUTCOME_DECISION")
        self.assertEqual(report["historical_pp_1"], "UNCLASSIFIED")
        self.assertIn("Thumb32", report["scan_caveat"])
        self.assertEqual(report["pre_store_branches"], [
            {"pc": "0x808e31a", "opcode": "0xd023", "static_target": "0x808e364"},
            {"pc": "0x808e322", "opcode": "0xd11c", "static_target": "0x808e35e"},
        ])
        self.assertNotIn("0xde00", str(report["pre_store_branches"]))
        self.assertNotIn("0xdf00", str(report["pre_store_branches"]))

    def test_store_opcode_mismatch(self):
        self.write_halfword(scout.STORE_PC, 0)
        with self.fixture(changed=self.data):
            with self.assertRaisesRegex(ValueError, "store opcode mismatch"):
                scout.inspect(self.path)

    def test_prestore_opcode_mismatch(self):
        self.write_halfword(0x0808E31A, 0)
        with self.fixture(changed=self.data):
            with self.assertRaisesRegex(ValueError, "pre-store instruction mismatch"):
                scout.inspect(self.path)

    def test_truncated_window_after_valid_hash(self):
        with self.fixture():
            with patch.object(scout, "WINDOW_END", BASE + SIZE + 2):
                with self.assertRaisesRegex(ValueError, "truncated code window"):
                    scout.inspect(self.path)

    def test_wrong_size_after_valid_hash(self):
        with self.fixture():
            with patch.object(scout, "ROM_SIZE", SIZE + 2):
                with self.assertRaisesRegex(ValueError, "wrong ROM size"):
                    scout.inspect(self.path)


if __name__ == "__main__":
    unittest.main()
