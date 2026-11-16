#!/usr/bin/env python3
"""Generated fake bytes only; never loads the private game."""
import unittest
import audit_private_rom_controller_lineage as a


def put(rom, address, number, size=2):
    off=address-a.ROM_START
    rom[off:off+size]=number.to_bytes(size,'little')


def encode_bl(rom, pc, target):
    delta = target-(pc+4)
    if delta % 2 or not -(1 << 22) <= delta < (1 << 22):
        raise ValueError('out of BL range')
    value=delta & 0x7FFFFF
    put(rom,pc,0xF000 | ((value >> 12) & 0x7FF))
    put(rom,pc+2,0xF800 | ((value >> 1) & 0x7FF))


def fixture():
    r=bytearray(0x2000000)
    put(r,a.COMMAND_TABLE+17*4,a.PLAYER_ACTION_HANDLER|1,4)
    put(r,a.COMMAND_TABLE+19*4,a.PLAYER_MOVE_HANDLER|1,4)
    for pc,val in ((a.PLAYER_ACTION_HANDLER,0xB510),
                   (a.PLAYER_MOVE_HANDLER,0xB5F0),
                   (0x08065ECC,0x780E),(0x08017204,0x2200),
                   (0x08017230,0x2202),
                   (0x08065F20,0x220A),(0x08065F22,0x2101)):
        put(r,pc,val)
    for pc,target in ((a.ACTION_HELPER_CALL,0x080171B8),
                      (a.ACTION_COMPLETE_CALL,a.EXPECTED_COMPLETE),
                      (a.PLAYER_MOVE_WRAPPER_CALL,a.PLAYER_MOVE_HANDLER),
                      (a.MOVE_EMIT_CALL,a.EXPECTED_EMITTER),
                      (a.AUTO_ACTION_FIGHT_EMIT_CALL,a.EXPECTED_EMITTER),
                      (a.AUTO_ACTION_SWITCH_EMIT_CALL,a.EXPECTED_EMITTER),
                      (a.MOVE_COMPLETE_CALL,a.EXPECTED_COMPLETE)):
        encode_bl(r,pc,target)
    return r

class ControllerLineageTests(unittest.TestCase):
    def test_positive_bounded_not_certified(self):
        z=a.assess(fixture())
        self.assertTrue(z['bounded_original_rom_dispatch_candidate'])
        for flag in ('absolute_source_symbol_identity_certified',
                     'automatic_planner_source_identity_certified',
                     'dynamic_legality_certified','manual_fallback_certified',
                     'no_automatic_forced_switch_certified',
                     'production_authorized'):
            self.assertIs(z[flag],False)
        self.assertEqual(z['native_acceptance_scenarios'],0)

    def test_each_opcode_gate_rejects_mutation(self):
        mutation_sites=[(a.PLAYER_ACTION_HANDLER,2),(a.PLAYER_MOVE_HANDLER,2),
                        (0x08065ECC,2),(0x08017204,2),(0x08017230,2),
                        (a.AUTO_ACTION_FIGHT_EMIT_CALL,2),
                        (a.AUTO_ACTION_SWITCH_EMIT_CALL,2),(0x08065F20,2),(0x08065F22,2),
                        (a.ACTION_HELPER_CALL,2),(a.ACTION_COMPLETE_CALL,2),
                        (a.PLAYER_MOVE_WRAPPER_CALL,2),(a.MOVE_EMIT_CALL,2),
                        (a.MOVE_COMPLETE_CALL,2)]
        for pc,width in mutation_sites:
            with self.subTest(pc=hex(pc)):
                rom=fixture();rom[pc-a.ROM_START] ^= 0x10
                self.assertFalse(a.assess(rom)['bounded_original_rom_dispatch_candidate'])

    def test_wrong_dispatch_target_fails(self):
        for cmd in (17,19):
            rom=fixture();put(rom,a.COMMAND_TABLE+4*cmd,0x08000001,4)
            self.assertFalse(a.assess(rom)['bounded_original_rom_dispatch_candidate'])

    def test_nonthumb_pointer_fails(self):
        for cmd in (17,19):
            rom=fixture()
            addr=a.PLAYER_ACTION_HANDLER if cmd==17 else a.PLAYER_MOVE_HANDLER
            put(rom,a.COMMAND_TABLE+4*cmd,addr,4)
            self.assertFalse(a.assess(rom)['bounded_original_rom_dispatch_candidate'])

    def test_bad_bl_second_halfword_fails(self):
        rom=fixture();put(rom,a.MOVE_EMIT_CALL+2,0xD001)
        self.assertIsNone(a.thumb_bl(rom,a.MOVE_EMIT_CALL))
        self.assertFalse(a.assess(rom)['bounded_original_rom_dispatch_candidate'])

    def test_negative_branch_round_trip(self):
        rom=fixture();self.assertEqual(a.thumb_bl(rom,a.ACTION_HELPER_CALL),0x080171B8)
        self.assertEqual(a.thumb_bl(rom,a.MOVE_EMIT_CALL),a.EXPECTED_EMITTER)

    def test_invalid_rom_dimensions_fail_closed(self):
        with self.assertRaises(ValueError):a.assess(b'')
        with self.assertRaises(ValueError):a.assess('not-a-rom')

if __name__=='__main__':
    unittest.main()
