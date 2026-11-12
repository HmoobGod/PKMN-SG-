#!/usr/bin/env python3
"""Hash-locked, read-only Thumb halfword window; static bytes are NOT outcome proof."""
import argparse
import hashlib
import json
from pathlib import Path

EXACT = "4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
PROTECTED = "7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
ROM_BASE = 0x08000000
ROM_SIZE = 33554432
STORE_PC = 0x0808E336
STORE_OPCODE = b"\x62\x54"


def inspect(path, before=128, after=64):
    # Reading once ensures the bytes decoded are the same bytes being SHA-pinned.
    rom = Path(path).read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest == PROTECTED:
        raise ValueError("refuse protected Current ROM")
    if digest != EXACT:
        raise ValueError("wrong exact modified ROM identity")
    if len(rom) != ROM_SIZE:
        raise ValueError("wrong size")
    if not isinstance(before, int) or not isinstance(after, int) or min(before, after) < 0 or before % 2 or after % 2 or after < 2:
        raise ValueError("invalid halfword window")
    offset = STORE_PC - ROM_BASE
    start, end = offset - before, offset + after
    if offset < 0 or offset + 2 > len(rom) or start < 0 or end > len(rom):
        raise ValueError("code window outside ROM")
    if rom[offset:offset + 2] != STORE_OPCODE:
        raise ValueError("wrong store opcode")
    code = rom[start:end]
    return {
        "classification": "STATIC_ONLY_NOT_OUTCOME_BRANCH_EVIDENCE",
        "sha256": digest,
        "store_pc": hex(STORE_PC),
        "halfwords": [
            {"pc": hex(STORE_PC - before + i), "le": code[i:i + 2].hex()}
            for i in range(0, len(code), 2)
        ],
        "next": "same-replay GDB branch/flags/PC witness required",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom")
    parser.add_argument("--before", type=int, default=128)
    parser.add_argument("--after", type=int, default=64)
    args = parser.parse_args()
    print(json.dumps(inspect(args.rom, args.before, args.after), indent=2))
