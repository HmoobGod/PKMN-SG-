#!/usr/bin/env python3
"""Synthetic negative tests only; they cannot authorize an actual hook."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

here = Path(__file__).parent
spec = importlib.util.spec_from_file_location("verify_hybrid_input", here / "verify_hybrid_input.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class HybridInputTests(unittest.TestCase):
    def test_size_mismatch_is_denied(self):
        with self.assertRaisesRegex(ValueError, "expected"):
            mod.require_rom(b"short", mod.CURRENT_SHA256, "Current")

    def test_wrong_sha_is_denied(self):
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            mod.require_rom(b"\0" * mod.ROM_SIZE, mod.CURRENT_SHA256, "Current")

    def test_block_differences_are_exact_indices(self):
        a = bytes(256)
        b = bytearray(a)
        b[15] = 1
        b[150] = 2
        self.assertEqual(mod.changed_blocks(a, b, 64), [0, 2])

    def test_malformed_comparison_is_denied(self):
        with self.assertRaises(ValueError):
            mod.changed_blocks(b"x", b"yy")
        with self.assertRaises(ValueError):
            mod.changed_blocks(b"abc", b"abc", 2)

    def test_anchor_windows_bounded_and_hash_only(self):
        a = bytes(128)
        b = bytearray(a)
        b[40] = 3
        report = mod.anchor_report(a, b, {"witness": 0x08000020}, 32)
        self.assertEqual(report["witness"]["window_equal"], False)
        self.assertFalse(report["witness"]["instruction_parity_certified"])
        self.assertNotIn("bytes", report["witness"])

    def test_anchor_out_of_range_is_denied(self):
        with self.assertRaises(ValueError):
            mod.anchor_report(b"abc", b"abc", {"outside": 0x09000000}, 32)

    def test_modified_identity_is_independent(self):
        self.assertNotEqual(mod.CURRENT_SHA256, mod.MODIFIED_SHA256)
        self.assertEqual(len(mod.DIFFERENT_64K_BLOCKS), 7)
        self.assertEqual(len(mod.WITNESS_ADDRESSES), 3)

    def test_any_lineage_difference_denied_even_if_hashes_mocked(self):
        with patch.object(mod, "require_rom", side_effect=["old", "new"]):
            with self.assertRaisesRegex(ValueError, "unexpected block lineage"):
                mod.inspect(bytes(mod.BLOCK_SIZE), bytes(mod.BLOCK_SIZE))


if __name__ == "__main__":
    unittest.main()
