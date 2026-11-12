#!/usr/bin/env python3
"""Read-only, SHA-locked static halfword sweep; never an outcome decision witness.

Linear halfword scanning may label literal-pool data as a branch and may split
Thumb-2 32-bit instructions. Only live same-ROM CPU PC/flags/branch proof can
establish executed control flow. Status fields are constants, not derived data.
"""
import argparse
import hashlib
import json
from pathlib import Path

EXACT_ROM = "4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
PROTECTED_ROM = "7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
ROM_SIZE = 33554432
ROM_BASE = 0x08000000
STORE_PC = 0x0808E336
WINDOW_START, WINDOW_END = 0x0808E310, 0x0808E378
EXPECTED_PRESTORE = ((0x0808E31A, 0xD023), (0x0808E322, 0xD11C))


def conditional_target(pc, opcode):
    # Thumb16 conditional B; condition 0xE is UDF and 0xF is SWI, not branches.
    if (opcode & 0xF000) != 0xD000 or ((opcode >> 8) & 15) >= 14:
        return None
    imm = opcode & 255
    return (pc + 4 + (((imm ^ 128) - 128) * 2)) & 0xFFFFFFFF


def inspect(path):
    # One immutable in-memory snapshot is both SHA-checked and decoded.
    rom = Path(path).read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest == PROTECTED_ROM:
        raise ValueError("protected Current ROM refused")
    if digest != EXACT_ROM:
        raise ValueError("wrong exact modified-ROM identity")
    if len(rom) != ROM_SIZE:
        raise ValueError("wrong ROM size")
    start, stop = WINDOW_START - ROM_BASE, WINDOW_END - ROM_BASE
    if start < 0 or stop > len(rom) or stop <= start or (stop - start) % 2:
        raise ValueError("truncated code window")
    code = rom[start:stop]
    if len(code) != stop - start:
        raise ValueError("truncated code window")

    def opcode(pc):
        i = pc - WINDOW_START
        if i < 0 or i + 2 > len(code) or i % 2:
            raise ValueError("instruction outside scanned window")
        return int.from_bytes(code[i:i + 2], "little")

    if opcode(STORE_PC) != 0x5462:
        raise ValueError("store opcode mismatch")
    for pc, word in EXPECTED_PRESTORE:
        if opcode(pc) != word:
            raise ValueError("pre-store instruction mismatch")
    branches = []
    for pc in range(WINDOW_START, STORE_PC, 2):
        op = opcode(pc)
        target = conditional_target(pc, op)
        if target is not None:
            branches.append({"pc": hex(pc), "opcode": hex(op), "static_target": hex(target)})
    return {
        "classification": "STATIC_BRANCH_BYTES_NOT_OUTCOME_DECISION",
        "rom_sha256": digest,
        "verified_prior_store_pc": hex(STORE_PC),
        "pre_store_branches": branches,
        "scan_caveat": "linear halfword sweep; literal data and Thumb32 instruction splits can look like Thumb16 branches",
        "historical_pp_1": "UNCLASSIFIED",  # fixed labels; NOT inferred from ROM
        "historical_pp_2": "UNCLASSIFIED",
        "formal_native_acceptance": "0/20",  # externally tracked; NOT ROM-derived
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom")
    args = parser.parse_args()
    print(json.dumps(inspect(args.rom), indent=2))
