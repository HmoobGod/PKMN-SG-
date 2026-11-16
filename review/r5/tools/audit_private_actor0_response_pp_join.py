#!/usr/bin/env python3
"""Conservative local-only original CPU player0 response-to-PP candidate join.

PUBLIC SOURCE ONLY; never bundle/print private ROM, save, CPU traces, RAM, or game
screenshots. Only raw inputs in a private directory. No guest writes. A joined
candidate proves neither Smart Auto ownership nor move legality/manual fallback.
"""
import argparse
import hashlib
import json
from pathlib import Path

from audit_private_cpu_pp_store import (
    ROM_BASE, hexuint, uint, verify_store, witness_pp_slot,
)

EMITTER_ADDR = 0x0806BD80
EMITTER_STORES = (0x0806BD8A, 0x0806BD8E, 0x0806BD92,
                  0x0806BD98, 0x0806BD9E)
PLAYER_CHOOSE_MOVE_RETURN = 0x08065F2D
DECISION_STORE = 0x0809435A
COMPLETION_STORE = 0x0806261A
DIRECT_PP_STORE = 0x0809E6BA
MAX_JOIN_FRAMES = 300
FORBIDDEN = {'guest_writes', 'native_accepted', 'production_authorized',
             'original_engine_request_certified'}


def thumb_bl_target(rom, return_address):
    """Decode a Thumb-1 32-bit BL at (LR & ~1) - 4 from exact ROM bytes."""
    try:
        lr = hexuint(return_address, 'return address')
        if lr & 1 != 1:
            return None
        pc = (lr & ~1) - 4
        off = pc - ROM_BASE
        if off < 0 or off + 4 > len(rom):
            return None
        a = int.from_bytes(rom[off:off + 2], 'little')
        b = int.from_bytes(rom[off + 2:off + 4], 'little')
        if a & 0xF800 != 0xF000 or b & 0xF800 != 0xF800:
            return None
        displacement = ((a & 0x7FF) << 12) | ((b & 0x7FF) << 1)
        if displacement & 0x400000:
            displacement -= 0x800000
        return (pc + 4 + displacement) & 0xFFFFFFFF
    except (TypeError, ValueError):
        return None


def response_rows_valid(rows, rom):
    """Five same-frame emitter stores, player battler0, chosen script slot."""
    if type(rows) is not list or len(rows) != 5 or any(type(r) is not dict for r in rows):
        return None
    try:
        first = rows[0]
        f = uint(first['f'], 'frame')
        dest = hexuint(first['dst'], 'response destination')
        lr = first['lr']
        regs = first['r']
        if type(regs) is not list or len(regs) != 8:
            return None
        if any(type(x) is not int or x < 0 or x > 0xFFFFFFFF for x in regs):
            return None
        actor, transfer_direction, action, packed_move_target = regs[:4]
        if (actor != 0 or transfer_direction != 1 or action != 10
                or packed_move_target & ~0xFFFF
                or packed_move_target & 0xFF > 3
                or (packed_move_target >> 8) & 0xFF > 3
                or lr != f'0x{PLAYER_CHOOSE_MOVE_RETURN:08x}'
                or thumb_bl_target(rom, lr) != EMITTER_ADDR):
            return None
        values = [32, 10, packed_move_target & 0xFFFF,
                  packed_move_target >> 16 & 255, packed_move_target >> 24 & 255]
        widths = (1, 1, 2, 1, 1)
        offsets = (0, 1, 2, 4, 5)
        for i, row in enumerate(rows):
            r = row['r']
            if (any(k in row for k in FORBIDDEN) or
                uint(row['f'], 'frame') != f or
                hexuint(row['pc'], 'PC') != EMITTER_STORES[i] or
                hexuint(row['raw_pc'], 'raw PC') != EMITTER_STORES[i] + 4 or
                hexuint(row['dst'], 'destination') != dest + offsets[i] or
                uint(row['width'], 'width') != widths[i] or
                uint(row['value'], 'value') != values[i] or
                row['lr'] != lr or
                type(r) is not list or len(r) != 8 or
                any(type(x) is not int or x < 0 or x > 0xFFFFFFFF for x in r) or
                r[0] != 0):
                return None
        return {'frame': f, 'slot': packed_move_target & 255,
                'target': packed_move_target >> 8 & 255}
    except (KeyError, TypeError, ValueError):
        return None


def candidate_player_responses(rows, rom):
    """Refuse mixed/duplicate/missing same-frame packets; keep foe separate."""
    out = []
    for i, row in enumerate(rows):
        if type(row) is not dict or row.get('pc') != f'0x{EMITTER_STORES[0]:08x}':
            continue
        r = row.get('r')
        if type(r) is not list or len(r) != 8 or r[0] != 0 or r[2] != 10:
            continue
        # Look forward for exactly four contiguous writes from same LR and actor,
        # excluding interleaved foe packets. Missing/misordered writes fail closed.
        packet = rows[i:i + 5]
        candidate = response_rows_valid(packet, rom)
        if candidate is not None:
            out.append(candidate)
    return out


def evaluate(rom, original_stores, pp_events, battle_frame):
    uint(battle_frame, 'battle frame')
    if not isinstance(rom, (bytes, bytearray, memoryview)):
        # Synthetic test ROMs may expose just __getitem__ and __len__.
        if not hasattr(rom, '__len__') or not hasattr(rom, '__getitem__'):
            raise ValueError('invalid ROM')
    if type(original_stores) is not list or type(pp_events) is not list:
        raise ValueError('invalid trace collections')
    responses = candidate_player_responses(original_stores, rom)
    admitted = []
    rejected = 0
    # Only grant a weak, explicitly unverified join to one player response.
    # Other result/action emitters within the same interval are an ambiguity.
    for i, response in enumerate(responses):
        first = response['frame']
        if first <= battle_frame:
            rejected += 1
            continue
        # Bound each request epoch by the NEXT player0 move response. A later
        # legitimate turn must not retroactively invalidate the previous one.
        following = [r['frame'] for j,r in enumerate(responses) if j != i and
                     r['frame'] >= first]
        next_response_frame = min(following) if following else first + MAX_JOIN_FRAMES + 1
        exclusive_end = min(first + MAX_JOIN_FRAMES + 1, next_response_frame)
        follow = [r for r in original_stores if type(r) is dict
                  and type(r.get('f')) is int and first <= r['f'] < exclusive_end]
        other_player_responses = [r for r in follow if r.get('pc') == f'0x{EMITTER_STORES[0]:08x}'
                                  and type(r.get('r')) is list and len(r['r']) >= 3
                                  and r['r'][0] == 0 and r['r'][2] == 10]
        if len(other_player_responses) != 1:
            rejected += 1
            continue
        results = []
        for pp_index, pp in enumerate(pp_events):
            if type(pp) is not dict or pp.get('event') == 'pp_candidate':
                continue
            f = pp.get('f')
            if type(f) is not int or not first < f < exclusive_end:
                continue
            if pp.get('raw_pc') != f'0x{DIRECT_PP_STORE + 4:08x}':
                continue
            if not verify_store(pp, rom, battle_frame):
                continue
            prior = [p for p in pp_events[:pp_index] if type(p) is dict and
                     p.get('event') == 'pp_candidate' and type(p.get('f')) is int and
                     p['f'] <= f]
            slot = witness_pp_slot(pp, prior)
            if slot is not None and slot[1] == response['slot']:
                results.append(pp)
        # The original validator PC is meaningful, but its live r0 holds
        # temporary decision data, NOT necessarily a battler identifier.
        # Never silently assume r0==player0 at this decision store.
        decision = any(r.get('pc') == f'0x{DECISION_STORE:08x}'
                       and type(r.get('r')) is list and len(r['r']) == 8
                       and first < r.get('f', -1) < results[0]['f']
                       for r in follow) if results else False
        completion = any(r.get('pc') == f'0x{COMPLETION_STORE:08x}'
                         and type(r.get('r')) is list and len(r['r']) == 8 and r['r'][0] == 0
                         and first <= r.get('f', -1) < results[0]['f']
                         for r in follow) if results else False
        if len(results) != 1 or not decision or not completion:
            rejected += 1
            continue
        admitted.append({'response_frame': first, 'pp_frame': results[0]['f'],
                         'slot_index': response['slot'], 'target_candidate': response['target'],
                         'player0_response_payload_stores': 5,
                         'original_player0_decision_store_observed': True,
                         'original_controller_completion_store_observed': True,
                         'pp_writer_pc': f'0x{DIRECT_PP_STORE:08X}', 'pp_delta': -1})
    return {
        'schema': 'sg-original-player0-cpu-response-pp-join-UNVERIFIED-v1',
        'joined_player0_response_pp_candidates_UNVERIFIED': len(admitted),
        'rejected_or_ambiguous_response_candidates': rejected,
        'candidates': admitted,
        'engine_owned_one_use_request_certified': False,
        'dynamic_move_target_legality_certified': False,
        'manual_fallback_certified': False,
        'unmodified_rom_automatic_move_origin_certified': False,
        'original_native_acceptance_scenarios': 0,
        'production_authorized': False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-rom', required=True, type=Path)
    p.add_argument('--private-owner-stores', required=True, type=Path)
    p.add_argument('--private-pp-trace', required=True, type=Path)
    p.add_argument('--expected-rom-sha256', required=True)
    p.add_argument('--battle-ui-frame', type=int, required=True)
    a = p.parse_args()
    rom = a.private_rom.read_bytes()
    if hashlib.sha256(rom).hexdigest().lower() != a.expected_rom_sha256.lower():
        raise SystemExit('private ROM identity mismatch')
    source = lambda path: [json.loads(x) for x in path.read_text().splitlines()]
    print(json.dumps(evaluate(rom, source(a.private_owner_stores),
                              source(a.private_pp_trace), a.battle_ui_frame), indent=2))


if __name__ == '__main__':
    main()
