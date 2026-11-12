"""Synthetic-only behavioral regressions for hash-locked static code window."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import exact_rom_outcome_window as w

BASE = 0x0808E200
SIZE = 512
OFFSET = w.STORE_PC - BASE


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic.bin"
        data = bytearray(SIZE)
        data[OFFSET:OFFSET + 2] = b"\x62\x54"
        self.path.write_bytes(data)

    def fixture(self, *, data=None):
        if data is not None:
            self.path.write_bytes(data)
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        return patch.multiple(w, EXACT=digest, ROM_BASE=BASE, ROM_SIZE=SIZE)

    def test_wrong_identity(self):
        with self.assertRaisesRegex(ValueError, "wrong exact"):
            w.inspect(self.path)

    def test_protected_identity(self):
        with patch.object(w, "PROTECTED", hashlib.sha256(self.path.read_bytes()).hexdigest()):
            with self.assertRaisesRegex(ValueError, "protected"):
                w.inspect(self.path)

    def test_static_only_success_and_read_only(self):
        initial = self.path.read_bytes()
        with self.fixture():
            result = w.inspect(self.path)
        self.assertEqual(self.path.read_bytes(), initial)
        self.assertEqual(result["classification"], "STATIC_ONLY_NOT_OUTCOME_BRANCH_EVIDENCE")
        self.assertEqual(result["store_pc"], hex(w.STORE_PC))
        self.assertEqual(len(result["halfwords"]), 96)
        self.assertEqual(result["halfwords"][64]["le"], "6254")

    def test_alignment_rejects_odd_before_and_after(self):
        with self.fixture():
            for kwargs in ({"before": 127}, {"after": 63}, {"after": 0}):
                with self.subTest(kwargs=kwargs):
                    with self.assertRaisesRegex(ValueError, "invalid halfword window"):
                        w.inspect(self.path, **kwargs)

    def test_opcode_mismatch_after_valid_hash(self):
        data = bytearray(self.path.read_bytes())
        data[OFFSET:OFFSET + 2] = b"\x00\x00"
        with self.fixture(data=data):
            with self.assertRaisesRegex(ValueError, "wrong store opcode"):
                w.inspect(self.path)

    def test_wrong_size_after_valid_hash(self):
        with self.fixture():
            with patch.object(w, "ROM_SIZE", SIZE + 2):
                with self.assertRaisesRegex(ValueError, "wrong size"):
                    w.inspect(self.path)

    def test_window_outside_file_after_valid_hash(self):
        with self.fixture():
            with self.assertRaisesRegex(ValueError, "code window outside ROM"):
                w.inspect(self.path, after=400)


if __name__ == "__main__":
    unittest.main()
