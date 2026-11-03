"""Synthetic Thumb branch decoder tests; no private ROM bytes needed."""
import tempfile
import unittest
from pathlib import Path
from check_copy_postloop import (
    ShapeError, sign_extend, conditional_target, unconditional_target,
    literal_target, verify_native_window, check_rom, END, ENTRY,
)


def enc_cond(pc, target, condition):
    step = (target - pc - 4) // 2
    assert -128 <= step <= 127 and (target-pc) % 2 == 0
    return 0xD000 | (condition << 8) | (step & 255)


def enc_uncond(pc, target):
    step = (target - pc - 4) // 2
    assert -1024 <= step <= 1023 and (target-pc) % 2 == 0
    return 0xE000 | (step & 0x7FF)


class ThumbPaths(unittest.TestCase):
    def test_legacy_conditional_paths(self):
        for pc, dest, cond in [(0x806b37c, 0x806b3c8, 4),
                               (0x806b380, 0x806b3ac, 0),
                               (0x806b3a4, 0x806b39c, 11),
                               (0x806b3c4, 0x806b3bc, 12)]:
            self.assertEqual(conditional_target(enc_cond(pc, dest, cond), pc),
                             (cond, dest))

    def test_signed_conditional_edges(self):
        for displacement in (-128, -1, 0, 127):
            pc = 0x08010000
            dest = pc + 4 + displacement * 2
            self.assertEqual(conditional_target(enc_cond(pc, dest, 1), pc),
                             (1, dest))

    def test_reject_swi_or_nonbranch(self):
        for value in (0xDF00, 0xDE00, 0x4800, 0xE000):
            with self.assertRaises(ShapeError):
                conditional_target(value, 0x08010000)

    def test_unconditional_edges(self):
        for displacement in (-1024, -200, 0, 100, 1023):
            pc = 0x08010000
            dest = pc + 4 + displacement * 2
            self.assertEqual(unconditional_target(enc_uncond(pc, dest), pc),
                             dest)

    def test_reject_wrong_unconditional_opcode(self):
        for value in (0xD000, 0xB500, 0xF000, 0x4700):
            with self.assertRaises(ShapeError):
                unconditional_target(value, 0x08010000)

    def test_literal_target_alignment(self):
        for pc, offset in ((0x806b376, 0x16), (0x806b3b2, 8),
                           (0x08000002, 0), (0x08000100, 255)):
            hw = 0x4800 | (3 << 8) | offset
            self.assertEqual(literal_target(hw, pc),
                             ((pc + 4) & ~3) + 4 * offset)

    def test_reject_nonliteral(self):
        for hw in (0xE001, 0xD001, 0xB510):
            with self.assertRaises(ShapeError):
                literal_target(hw, 0x08010000)

    def test_unavailable_game_bytes_never_certify(self):
        with self.assertRaises(ShapeError):
            verify_native_window(b'\0' * (END-ENTRY))
        with self.assertRaises(ShapeError):
            verify_native_window(b'\0')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'not-a-game.gba'
            path.write_bytes(b'\0' * 100)
            with self.assertRaises(ShapeError):
                check_rom(path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
