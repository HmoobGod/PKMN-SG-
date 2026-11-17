#!/usr/bin/env python3
"""R5 isolated source-only literal regression; never opens private ROM/save."""
from __future__ import annotations
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / 'player_taunt_recovery_choice_gorilla_r4.s'
CANDIDATE = ROOT / 'player_taunt_recovery_choice_gorilla_r5_review_only.s'
R4_SOURCE = 'ce8d38b718939243a99eed560d250ed30e15b29255a0b4f0c21f3cd3ced12333'
R5_SOURCE = '1f3fc5570adeabbbdc2dcbddf4a0b86334aececd074a77b4ce29e7276e2f6daf'
R4_CODE = 'd588d77c7096afcf9130b445d184ef06842f7599da92649c65ae73d637abc584'
R5_CODE = '8a923d145a8718ded7b8e32b33aaa1de88a85c2c314cdeb34c79135821cc6d89'


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class ChoiceLiteralTests(unittest.TestCase):
    def test_pinned_original_untouched(self):
        self.assertEqual(sha(ORIGINAL.read_bytes()), R4_SOURCE)
        self.assertEqual(ORIGINAL.read_bytes().count(b'.Lchoiced_offset:  .word 364'), 1)

    def test_only_one_source_line_changes(self):
        old, new = ORIGINAL.read_bytes(), CANDIDATE.read_bytes()
        self.assertEqual(sha(new), R5_SOURCE)
        self.assertEqual(new, old.replace(b'.Lchoiced_offset:  .word 364', b'.Lchoiced_offset:  .word 380'))
        self.assertEqual(new.count(b'.Lchoiced_offset:  .word 380'), 1)

    def test_compiled_only_one_literal_byte_differs(self):
        with tempfile.TemporaryDirectory(prefix='sg_r5_sourceonly_') as d:
            data=[]
            for n,source in enumerate((ORIGINAL,CANDIDATE)):
                obj, binfile=Path(d)/f'{n}.o',Path(d)/f'{n}.bin'
                subprocess.run(['clang','--target=armv4t-none-eabi','-mthumb','-c',str(source),'-o',str(obj)],check=True,capture_output=True)
                subprocess.run(['llvm-objcopy','-O','binary','-j','.text.r4guard',str(obj),str(binfile)],check=True,capture_output=True)
                data.append(binfile.read_bytes())
        old,new=data
        self.assertEqual(len(old),252)
        self.assertEqual(len(new),252)
        self.assertEqual(sha(old),R4_CODE)
        self.assertEqual(sha(new),R5_CODE)
        self.assertEqual([(i,a,b) for i,(a,b) in enumerate(zip(old,new)) if a!=b],[(236,0x6c,0x7c)])
        self.assertEqual(old[236:240],(364).to_bytes(4,'little'))
        self.assertEqual(new[236:240],(380).to_bytes(4,'little'))
        self.assertEqual(old[:236]+old[240:],new[:236]+new[240:])

    def test_safety_gate_not_replaced(self):
        src=CANDIDATE.read_text()
        for marker in ('cmp     r4, #0','cmp     r6, #3','ldr     r2, .Lchoiced_offset','cmp     r1, #255','movs    r6, #1','.Lkeep:'):
            self.assertIn(marker,src)
        self.assertNotIn('.word 364',src)


if __name__=='__main__':
    unittest.main(verbosity=2)
