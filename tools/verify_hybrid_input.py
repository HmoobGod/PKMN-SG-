#!/usr/bin/env python3
"""Read-only exact-ROM identity barrier for a future disposable hybrid hook.

No patching, extraction of ROM bytes, save access, or automatic hook approval.
A hash match establishes byte identity, NOT legal engine ownership.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROM_SIZE = 32 * 1024 * 1024
CURRENT_SHA256 = "7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
MODIFIED_SHA256 = "4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
DIFFERENT_64K_BLOCKS = (1, 6, 9, 15, 497, 498, 499)
BLOCK_SIZE = 65536
# Addresses established in the original-ROM CPU witness, NOT source-build symbols.
WITNESS_ADDRESSES = {
    "player_dispatcher": 0x080619D4,
    "controller_completion": 0x080625F8,
    "buffer_a_copy_entry": 0x0806B370,
}
WINDOW_BYTES = 32


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require_rom(data, expected, label):
    if len(data) != ROM_SIZE:
        raise ValueError(f"{label}: expected 33554432 bytes, got {len(data)}")
    sha = digest(data)
    if sha != expected:
        raise ValueError(f"{label}: exact SHA256 mismatch ({sha}); no analysis authorized")
    return sha


def changed_blocks(a, b, block_size=BLOCK_SIZE):
    if len(a) != len(b) or not a or len(a) % block_size:
        raise ValueError("comparison size/alignment mismatch")
    return [i for i in range(len(a) // block_size)
            if a[i * block_size:(i + 1) * block_size] != b[i * block_size:(i + 1) * block_size]]


def anchor_report(current, modified, addresses=WITNESS_ADDRESSES, window=WINDOW_BYTES):
    out = {}
    for name, addr in addresses.items():
        offset = addr - 0x08000000
        if offset < 0 or offset + window > len(modified):
            raise ValueError(f"{name}: address outside ROM")
        old = current[offset:offset + window]
        new = modified[offset:offset + window]
        out[name] = {
            "guest_address": f"0x{addr:08X}",
            "size": window,
            "current_window_sha256": digest(old),
            "modified_window_sha256": digest(new),
            "window_equal": old == new,
            "instruction_parity_certified": False,
        }
    return out


def inspect(current, modified):
    old_sha = require_rom(current, CURRENT_SHA256, "protected Current (read only)")
    new_sha = require_rom(modified, MODIFIED_SHA256, "experimental modified (read only)")
    diffs = changed_blocks(current, modified)
    if tuple(diffs) != DIFFERENT_64K_BLOCKS:
        raise ValueError(f"unexpected block lineage: {diffs}; fail closed")
    return {
        "scope": "READ ONLY; identity and windows, no ROM/save emitted",
        "current_sha256": old_sha,
        "modified_sha256": new_sha,
        "changed_64k_block_indices": diffs,
        "same_64k_blocks": ROM_SIZE // BLOCK_SIZE - len(diffs),
        "anchors": anchor_report(current, modified),
        "compiled_source_is_not_target": True,
        "disassembly_followup_needed": True,
        "ownership_lease_certified": False,
        "move_target_legality_certified": False,
        "native_hook_authorized": False,
        "playable_rom_certified": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--current", required=True, type=Path, help="exact protected Current ROM; read-only")
    p.add_argument("--modified", required=True, type=Path, help="exact recovered modified ROM; read-only")
    args = p.parse_args()
    if args.current.resolve() == args.modified.resolve():
        p.error("Current and modified must be different input paths")
    if not args.current.is_file() or not args.modified.is_file():
        p.error("both ROM inputs must exist as regular files")
    if args.current.is_symlink() or args.modified.is_symlink():
        p.error("symlink inputs not accepted")
    try:
        report = inspect(args.current.read_bytes(), args.modified.read_bytes())
    except ValueError as exc:
        p.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
