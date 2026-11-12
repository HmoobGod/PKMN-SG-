#!/usr/bin/env python3
"""Synthetic negative tests for native Thumb parity; no private ROM in CI."""
import importlib.util
import hashlib
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

root = Path(__file__).parent
spec = importlib.util.spec_from_file_location("verify_native_anchor_parity", root / "verify_native_anchor_parity.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class NativeAnchorParityTests(unittest.TestCase):
    def test_original_windows_do_not_overlap(self):
        spans = sorted((x["address"], x["address"] + x["length"]) for x in mod.ANCHORS.values())
        self.assertTrue(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])))

    def test_unverified_original_bytes_rejected(self):
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            mod.audit_current(bytes(0x70000))

    def test_literal_change_rejected_after_window_hash_check(self):
        witness = mod.ANCHORS["player_dispatcher"]
        rom = bytearray(0x70000)
        start = witness["address"] - mod.ROM_BASE
        struct.pack_into("<I", rom, start + 0x34, 123)
        local = {**witness, "sha256": hashlib.sha256(rom[start:start + witness["length"]]).hexdigest()}
        with patch.dict(mod.ANCHORS, {"only": local}, clear=True):
            with self.assertRaisesRegex(ValueError, "literal mismatch"):
                mod.audit_current(rom)

    def test_anchor_out_of_range_and_unaligned_denied(self):
        for addr in (mod.ROM_BASE + 1, mod.ROM_BASE - 2, mod.ROM_BASE + 400):
            with self.subTest(addr=addr), self.assertRaises(ValueError):
                mod.window(bytes(256), {"address": addr, "length": 64})

    def test_input_identity_required_before_any_audit(self):
        with self.assertRaisesRegex(ValueError, "expected"):
            mod.audit(b"short")

    def test_identical_test_windows_still_do_not_authorize_hook(self):
        witness = mod.ANCHORS["player_dispatcher"]
        fake = bytes(0x70000)
        with patch.object(mod, "require_rom", side_effect=["current", "modified"]), \
             patch.object(mod, "audit_current", return_value={"player_dispatcher": {"address": hex(witness["address"])}}), \
             patch.object(mod, "changed_blocks", return_value=list(mod.DIFFERENT_64K_BLOCKS)), \
             patch.dict(mod.ANCHORS, {"player_dispatcher": witness}, clear=True):
            result = mod.audit(fake, fake)
        self.assertTrue(result["all_three_anchor_windows_byte_equal"])
        self.assertFalse(result["native_hook_authorized"])
        self.assertFalse(result["engine_owner_epoch_authorized"])
        self.assertFalse(result["playable_or_save_compatibility_certified"])

    def test_one_opcode_mutation_revokes_parity(self):
        witness = mod.ANCHORS["player_dispatcher"]
        fake = bytearray(0x70000)
        offset = witness["address"] - mod.ROM_BASE
        altered = fake.copy()
        altered[offset + 2] = 1
        with patch.object(mod, "require_rom", side_effect=["current", "modified"]), \
             patch.object(mod, "audit_current", return_value={"player_dispatcher": {"address": hex(witness["address"])}}), \
             patch.object(mod, "changed_blocks", return_value=list(mod.DIFFERENT_64K_BLOCKS)), \
             patch.dict(mod.ANCHORS, {"player_dispatcher": witness}, clear=True):
            result = mod.audit(bytes(fake), bytes(altered))
        self.assertFalse(result["all_three_anchor_windows_byte_equal"])
        self.assertFalse(result["native_hook_authorized"])

    def test_modified_rom_with_wrong_block_lineage_denied(self):
        with patch.object(mod, "require_rom", side_effect=["current", "modified"]), \
             patch.object(mod, "audit_current", return_value={}), \
             patch.object(mod, "changed_blocks", return_value=[]):
            with self.assertRaisesRegex(ValueError, "lineage"):
                mod.audit(bytes(100), bytes(100))


if __name__ == "__main__":
    unittest.main()
