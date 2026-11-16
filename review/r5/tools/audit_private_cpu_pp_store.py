#!/usr/bin/env python3
"""Fail-closed, read-only GBA PP byte-store CPU witness checker.

PUBLIC SOURCE ONLY. Never store, transmit or print ROM/save/trace bytes. The
trace and exact ROM are LOCAL PRIVATE INPUTS. Synthetic CI does not use them.
Neither a valid store nor a rendered move proves automatic engine ownership.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROM_BASE = 0x08000000
EWRAM_BEGIN = 0x02000000
EWRAM_END = 0x02040000
FORBIDDEN = frozenset(("guest_writes", "production_authorized", "native_accepted",
                      "original_engine_request_certified"))


def uint(value, label):
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"invalid {label}")
    return value


def hexuint(value, label):
    if type(value) is not str or not value.startswith('0x'):
        raise ValueError(f"invalid {label}")
    try:
        parsed = int(value, 16)
    except ValueError as exc:
        raise ValueError(f"invalid {label}") from exc
    return uint(parsed, label)


def decode_thumb_strb(opcode, registers):
    """Return original THUMB STRB immediate effective (address, byte source)."""
    if type(opcode) is not int or opcode < 0 or opcode > 0xFFFF:
        return None
    if opcode & 0xF800 != 0x7000:
        return None
    if type(registers) is not list or len(registers) != 8:
        return None
    try:
        r = [uint(x, 'register') for x in registers]
    except ValueError:
        return None
    rb = (opcode >> 3) & 7
    rt = opcode & 7
    offset = (opcode >> 6) & 31
    effective = r[rb] + offset
    if effective > 0xFFFFFFFF:
        return None
    return effective, r[rt] & 0xFF


def verify_store(event, rom, first_battle_frame):
    """Examine only strict direct one-byte, one-PP-value drops.

    The tested mGBA CPU pipeline stores r15 = executing Thumb PC + 4 at a
    store callback. The logged `op` is a separately-prefetched instruction,
    NOT proof of the store opcode. Fetch the actual original ROM halfword.
    """
    if type(event) is not dict or any(key in event for key in FORBIDDEN):
        return False
    try:
        f = uint(event['f'], 'frame')
        address = hexuint(event['address'], 'address')
        width = uint(event['width'], 'width')
        before = uint(event['before'], 'before')
        after = uint(event['after'], 'after')
        value = uint(event['value'], 'value')
        pc = hexuint(event['raw_pc'], 'PC')
        thumb = uint(event['thumb_flag'], 'CPU state')
        registers = event['r']
    except (ValueError, KeyError, TypeError):
        return False
    if (f <= first_battle_frame or width != 1 or thumb != 1 or
        not EWRAM_BEGIN <= address < EWRAM_END or
        not 1 <= before <= 255 or after != before-1 or value != after or
        not ROM_BASE+4 <= pc < ROM_BASE+len(rom)+4 or pc % 2):
        return False
    offset = pc - ROM_BASE - 4
    if offset < 0 or offset+2 > len(rom):
        return False
    opcode = int.from_bytes(rom[offset:offset+2], 'little')
    return decode_thumb_strb(opcode, registers) == (address, after)



def witness_pp_slot(row, prior_candidates):
    """Require a previously seen structural match, not merely any EWRAM byte."""
    try:
        address = hexuint(row['address'], 'address')
        frame = uint(row['f'], 'frame')
    except (ValueError, KeyError, TypeError):
        return None
    # A stale snapshot must not label a later unrelated byte write as PP.
    # The 300-frame horizon is a conservative research bound, NOT proof
    # of game ownership. Multiple matching bases fail closed.
    valid_by_base_slot = {}
    for candidate in prior_candidates:
        if type(candidate) is not dict or any(k in candidate for k in FORBIDDEN):
            continue
        try:
            seen_frame = uint(candidate['f'], 'candidate frame')
            base = hexuint(candidate['base'], 'candidate base')
            pp = candidate['pp']
            if type(pp) is not list or len(pp) != 4:
                continue
            for n in pp:
                if uint(n, 'candidate PP') > 64:
                    raise ValueError('bad PP value')
        except (ValueError, KeyError, TypeError):
            continue
        slot = address - (base + 0x25)
        if (seen_frame <= frame <= seen_frame + 300 and 0 <= slot < 4
                and pp[slot] >= row['before']):
            key = (base, slot)
            valid_by_base_slot[key] = max(seen_frame,
                                           valid_by_base_slot.get(key, -1))
    if len(valid_by_base_slot) != 1:
        return None
    (_, slot), seen_frame = next(iter(valid_by_base_slot.items()))
    return seen_frame, slot


def evaluate(rom, trace_rows, battle_start_frame):
    uint(battle_start_frame, 'battle start')
    if not isinstance(rom, (bytes,bytearray)) or len(rom) < 4:
        raise ValueError('invalid ROM')
    if not isinstance(trace_rows, list):
        raise ValueError('invalid trace')
    direct = []
    seen = set()
    prior_candidates = []
    rejected = 0
    for row in trace_rows:
        if isinstance(row, dict) and row.get('event') == 'pp_candidate':
            prior_candidates.append(row)  # heuristic; independent CPU store required
            continue
        slot_witness = witness_pp_slot(row, prior_candidates)
        if slot_witness is not None and verify_store(row, rom, battle_start_frame):
            key = (row['f'], row['address'], row['before'], row['after'])
            if key in seen:
                rejected += 1
                continue
            seen.add(key)
            direct.append({'frame': row['f'], 'slot_index': slot_witness[1], 'delta': -1,
                           'writer_pc': f"0x{int(row['raw_pc'],16)-4:08X}"})
        else:
            rejected += 1
    return {
        'schema': 'sg-private-cpu-pp-direct-strb-candidate-v1',
        'direct_cpu_pp_byte_debit_candidates_UNVERIFIED': len(direct),
        'rejected_or_non_pp_events': rejected,
        'candidates': direct,
        'original_request_owner_certified': False,
        'move_target_legality_certified': False,
        'pp_cancel_cause_certified': False,
        'manual_fallback_certified': False,
        'original_native_acceptance_scenarios': 0,
        'production_authorized': False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-rom', required=True, type=Path)
    p.add_argument('--private-trace', required=True, type=Path)
    p.add_argument('--expected-rom-sha256', required=True)
    p.add_argument('--battle-ui-frame', required=True, type=int)
    args = p.parse_args()
    rom = args.private_rom.read_bytes()
    if hashlib.sha256(rom).hexdigest().lower() != args.expected_rom_sha256.lower():
        raise SystemExit('ROM identity mismatch: refusing audit')
    rows = [json.loads(line) for line in args.private_trace.read_text().splitlines()]
    print(json.dumps(evaluate(rom, rows, args.battle_ui_frame), indent=2))


if __name__ == '__main__':
    main()
