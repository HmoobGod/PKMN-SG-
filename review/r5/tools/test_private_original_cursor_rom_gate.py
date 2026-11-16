#!/usr/bin/env python3
"""Fake 32-MiB ROM instruction fixtures, never a user game image."""
import unittest
from audit_private_original_cursor_writer import check_rom, ROM_START, ROM_SIZE

HALFWORDS={0x08018620:0xf7ff,0x08018622:0xfee6,
 0x08018624:0x4b35,0x08018626:0x681a,0x08018628:0x1913,
 0x0801862a:0x3307,0x0801862c:0x33ff,0x0801862e:0x7018,
 0x08016fb6:0x7018}

def fake():
    b=bytearray(ROM_SIZE)
    for a,v in HALFWORDS.items():b[a-ROM_START:a-ROM_START+2]=v.to_bytes(2,'little')
    return b

class StaticROMGateTests(unittest.TestCase):
    def test_exact_expected_bl_and_stores(self):
        self.assertTrue(check_rom(fake()))
    def test_slot_writer_mutation_fails(self):
        b=fake();b[0x0801862e-ROM_START]^=1
        self.assertFalse(check_rom(b))
    def test_bl_target_mutation_fails(self):
        b=fake();b[0x08018622-ROM_START]^=1
        self.assertFalse(check_rom(b))
    def test_non_rom_or_truncated_fails(self):
        self.assertFalse(check_rom(b'none'))
    def test_invalid_target_strb_fails(self):
        b=fake();b[0x08016fb6-ROM_START]=0
        self.assertFalse(check_rom(b))

if __name__=='__main__':unittest.main()
