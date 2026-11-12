"""Fail-closed synthetic regressions; never use real save/ROM as test fixture."""
import hashlib, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import exact_rom_outcome_window as w
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"synthetic.bin"
        offset=w.STORE_PC-0x08000000
        with self.path.open("wb") as f: f.truncate(offset+256)
        with self.path.open("r+b") as f:
            f.seek(offset); f.write(bytes.fromhex("6254"))
        self.hash=hashlib.sha256(self.path.read_bytes()).hexdigest()
    def test_wrong_identity(self):
        with self.assertRaisesRegex(ValueError,"wrong exact"): w.inspect(self.path)
    def test_protected_identity(self):
        with patch.object(w,"PROTECTED",self.hash):
            with self.assertRaisesRegex(ValueError,"protected"): w.inspect(self.path)
    def test_static_only_and_read_only(self):
        before=self.path.read_bytes()
        with patch.object(w,"EXACT",self.hash), patch.object(w,"Path",Path):
            with patch.object(w,"hashlib",hashlib):
                # synthetic bytes are small; size refusal is intentional
                with self.assertRaisesRegex(ValueError,"wrong size"): w.inspect(self.path)
        self.assertEqual(before,self.path.read_bytes())
    def test_alignment(self):
        with patch.object(w,"EXACT",self.hash):
            with self.assertRaisesRegex(ValueError,"wrong size"): w.inspect(self.path,before=127)
    def test_opcode_mismatch(self):
        with self.path.open("r+b") as f:
            f.seek(w.STORE_PC-0x08000000); f.write(b"\\x00\\x00")
        with self.assertRaisesRegex(ValueError,"wrong exact"): w.inspect(self.path)
if __name__=="__main__": unittest.main()
