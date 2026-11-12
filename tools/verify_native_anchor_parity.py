#!/usr/bin/env python3
"""Read-only Thumb anchor parity audit for SoulGold HYBRID (never installs a hook).

Matches known locally disassembled native controller windows to an exact private
Current ROM and optionally compares them with the exact recovered modified ROM.
Outputs only hashes and flags. Window parity does NOT prove engine ownership,
safe relocation, move/target legality, or save compatibility.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from verify_hybrid_input import (
    CURRENT_SHA256, MODIFIED_SHA256, DIFFERENT_64K_BLOCKS,
    changed_blocks, require_rom,
)

ROM_BASE = 0x08000000
# Current ROM 7b9ac66d...: locally checked by Thumb disassembly and literals.
# These ARE NOT source-build symbol addresses and are NOT a modified-ROM proof.
ANCHORS = {
    "player_dispatcher": {
        "address": 0x080619D4, "length": 64,
        "sha256": "13a58a442a94de1cc14edf482471764ff641e88020923e8b219b4ea11ba0313b",
        "literals": {0x34: 0x02001D2C, 0x38: 0x02001C6C, 0x3C: 0x084443EC},
    },
    "controller_completion": {
        "address": 0x080625F8, "length": 104,
        "sha256": "f0ba8d22e052fbc4a4b97ec4391e024418d77f50ba33c645e404e6beae80e789",
        "literals": {
            0x50: 0x03002E58, 0x54: 0x080619D5,
            0x58: 0x02001AB4, 0x5C: 0x02001D2C, 0x60: 0x02001C6C,
        },
    },
    "buffer_a_copy_entry": {
        "address": 0x0806B370, "length": 112,
        "sha256": "5cf46d216c6be3492e7f033a8fe67e2bef4ae0ae7aeaa6aa53840ca889506410",
        "literals": {0x60: 0x02001AB4, 0x64: 0x02001C6C},
    },
}


def window(rom, entry):
    address, length = entry["address"], entry["length"]
    offset = address - ROM_BASE
    if address & 1 or offset < 0 or offset + length > len(rom):
        raise ValueError("Thumb anchor outside aligned ROM window")
    return rom[offset:offset + length]


def audit_current(current):
    """Caller must have pinned Current's full-ROM SHA before invoking."""
    out = {}
    for name, spec in ANCHORS.items():
        data = window(current, spec)
        actual = hashlib.sha256(data).hexdigest()
        if actual != spec["sha256"]:
            raise ValueError(f"{name}: original native Thumb window SHA mismatch")
        for offset, expected in spec["literals"].items():
            if offset % 4 != 0 or offset < 0 or offset + 4 > len(data):
                raise ValueError(f"{name}: malformed literal offset")
            if struct.unpack_from("<I", data, offset)[0] != expected:
                raise ValueError(f"{name}: original native literal mismatch at +{offset:#x}")
        out[name] = {
            "address": f"0x{spec['address']:08X}",
            "length": spec["length"],
            "current_sha256": actual,
            "current_code_window_attested": True,
            "pc_relative_literal_count": len(spec["literals"]),
        }
    return out


def audit(current, modified=None):
    current_sha = require_rom(current, CURRENT_SHA256, "protected Current (read-only)")
    anchors = audit_current(current)
    result = {
        "scope": "native Thumb byte/literal parity audit; read-only and no installed hook",
        "current_sha256": current_sha,
        "current_anchor_windows": anchors,
        "modified_rom_verified": False,
        "native_hook_authorized": False,
        "engine_owner_epoch_authorized": False,
        "move_or_target_legality_authorized": False,
        "manual_fallback_required": True,
        "playable_or_save_compatibility_certified": False,
    }
    if modified is None:
        result["next_gate"] = "separately SHA-pinned modified ROM required for binary parity"
        return result
    modified_sha = require_rom(modified, MODIFIED_SHA256, "modified experimental (read-only)")
    differences = changed_blocks(current, modified)
    if tuple(differences) != DIFFERENT_64K_BLOCKS:
        raise ValueError("modified ROM has unexpected lineage; refuse comparison")
    parity = {}
    for name, spec in ANCHORS.items():
        old, new = window(current, spec), window(modified, spec)
        identical = old == new
        parity[name] = {
            "address": anchors[name]["address"],
            "length": spec["length"],
            "modified_sha256": hashlib.sha256(new).hexdigest(),
            "original_thumb_window_byte_equal": identical,
            "original_literally_identical_instructions_and_literals": identical,
            "safe_relocatable_hook_proven": False,
        }
    result.update({
        "modified_sha256": modified_sha,
        "modified_rom_verified": True,
        "modified_64k_changed_indices": differences,
        "modified_vs_current_native_anchors": parity,
        "all_three_anchor_windows_byte_equal": all(
            v["original_thumb_window_byte_equal"] for v in parity.values()
        ),
        "next_gate": "native owner/epoch + instruction boundary + relocation/reply/legality proof",
    })
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--current", type=Path, required=True)
    ap.add_argument("--modified", type=Path, help="optional exact recovered modified ROM")
    args = ap.parse_args()
    if args.modified is not None and args.current.resolve() == args.modified.resolve():
        ap.error("same source cannot count as distinct modified ROM")
    for p in (args.current, args.modified):
        if p is not None and (not p.is_file() or p.is_symlink()):
            ap.error("only existing regular non-symlink ROM inputs accepted")
    try:
        report = audit(args.current.read_bytes(), args.modified.read_bytes() if args.modified else None)
    except ValueError as exc:
        ap.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
