"""Safe public synthetic tests; no private ROM or save is used."""
import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import exact_rom_prestore_branch_scout as scout
class Tests(unittest.TestCase):
    def test_forward_beq(self):
        self.assertEqual(scout.conditional_target(0x0808e31a,0xd023),0x0808e364)
    def test_forward_bne(self):
        self.assertEqual(scout.conditional_target(0x0808e322,0xd11c),0x0808e35e)
    def test_backward_branch(self):
        self.assertEqual(scout.conditional_target(0x0808e374,0xd0d6),0x0808e324)
    def test_non_conditional_opcode(self):
        for v in (0xdf00,0xde00,0xe001,0x5462,0xf000):
            self.assertIsNone(scout.conditional_target(0x0808e31a,v))
    def test_wrong_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"synthetic";p.write_bytes(b"synthetic")
            with self.assertRaisesRegex(ValueError,"wrong exact"):scout.inspect(p)
    def test_protected_rom_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"synthetic";p.write_bytes(b"synthetic")
            with patch.object(scout,"PROTECTED_ROM",hashlib.sha256(b"synthetic").hexdigest()):
                with self.assertRaisesRegex(ValueError,"protected"):scout.inspect(p)
if __name__=="__main__":unittest.main()
