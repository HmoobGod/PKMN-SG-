#!/usr/bin/env python3
"""Public STMIA decoder negative mutation and address/source parity tests."""
import unittest
from decode_original_stmia_callback_word import original_thumb_stmia_word_at as word

class StmiaCallbackTests(unittest.TestCase):
    def test_two_words_from_one_stmia_instruction(self):
        regs=(0x030055D4,0x081C7589,0x080C4265,0,0,0,0,0)
        self.assertEqual(word(0xC006,regs,0x030055D4),regs[1])
        self.assertEqual(word(0xC006,regs,0x030055D8),regs[2])
        self.assertIsNone(word(0xC006,regs,0x030055DC))
    def test_ldmia_not_store(self):
        regs=(0x030055D4,1,2,0,0,0,0,0)
        self.assertIsNone(word(0xC806,regs,regs[0]))
    def test_mask_empty_and_unpredictable_base_in_list(self):
        regs=(0x030055D4,1,2,0,0,0,0,0)
        self.assertIsNone(word(0xC000,regs,regs[0]))
        self.assertIsNone(word(0xC007,regs,regs[0]))
    def test_alignment_and_overflow_denied(self):
        regs=(0x030055D5,1,2,0,0,0,0,0)
        self.assertIsNone(word(0xC006,regs,regs[0]))
        regs=(0xFFFFFFFC,1,2,0,0,0,0,0)
        self.assertIsNone(word(0xC006,regs,regs[0]))
    def test_invalid_original_cpu_register_type_denied(self):
        for regs in ((1,2,3), tuple([0]*7+[True]),tuple([0]*7+[-1])):
            with self.assertRaises(ValueError):
                word(0xC006,regs,0)
    def test_random_non_stmia_thumb_opcode_denied(self):
        regs=(0x030055D4,1,2,0,0,0,0,0)
        for op in (0x6001,0x700E,0xC800,0xBDF0,0x780E):
            self.assertIsNone(word(op,regs,regs[0]))
if __name__=="__main__":
    unittest.main()
