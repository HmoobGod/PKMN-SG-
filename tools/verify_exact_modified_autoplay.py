#!/usr/bin/env python3
"""Fail-closed offline witness verifier for EXISTING exact modified-ROM auto moves.

Private trace, ROM, save, emulator, and savestates NEVER belong in public git.
The summarized result is observation, not engine authorization or ROM promotion.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROM_SHA = '4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44'
SAVE_SHA = '8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
STATE_SHA = '91503b1db0aae28a4c004d1af4f7e618d7aed4d291aa236950362a730763fab6'
PRECONSTRUCTOR_SHA = 'a4b8849ef8037c199d8ce04230a92f6e0c87903fbc348e735481ada5c3bf8e0d'
PRIVATE_REQUEST_SHA = '46a2425f06b61f66a71f361fa96241c01f73268933fbb0f6fa6264b99086adeb'
SCHEMA = 'sg-exact-modified-noinput-native-trace-v1'

def deny(ok, msg):
    if not ok:
        raise ValueError(msg)

def audit(report):
    deny(report.get('schema') == SCHEMA, 'unknown trace schema')
    deny(report.get('rom_sha256') == ROM_SHA and report.get('save_sha256') == SAVE_SHA,
         'private ROM/save identity mismatch')
    deny(report.get('state_sha256') == STATE_SHA, 'private player pending-state identity mismatch')
    deny(report.get('host_move_menu_buttons_sent') == 0, 'host sent move-menu buttons')
    deny(report.get('emulator_rom_writes') == 0 and report.get('installed_new_hook') is False,
         'forbidden game ROM mutation or fabricated new hook')
    pre = report.get('provenance', {})
    deny(pre.get('preconstructor_state_sha256') == PRECONSTRUCTOR_SHA
         and pre.get('request_copy_sha256') == PRIVATE_REQUEST_SHA
         and pre.get('actor0_installer') == 1
         and pre.get('opponent_installer') == 1
         and pre.get('request_copy_stores') == 44
         and pre.get('pending_set_guest_steps') == 23
         and pre.get('current_flags') == '0x4'
         and pre.get('actor0_controller_kind') == 1
         and pre.get('actor1_controller_kind') == 3
         and pre.get('player_move_request_same_as_own') is True,
         'untrusted original wild-single player request')
    deny(report.get('status') == 1 and report.get('trace_start_frame') == 4179
         and report.get('trace_end_frame') >= 4529
         and report.get('guest_steps', 0) > 0, 'incomplete observed guest trace')
    moves = report.get('player_moves_before')
    before, after = report.get('player_pp_before'), report.get('player_pp_after')
    deny(isinstance(moves, list) and len(moves) == 4
         and isinstance(before, list) and len(before) == 4
         and isinstance(after, list) and len(after) == 4
         and all(isinstance(x, int) and 0 <= x < 256 for x in before + after)
         and all(isinstance(x, int) and 0 < x < 936 for x in moves),
         'malformed player-owned move/PP snapshots')
    events = report.get('events')
    deny(isinstance(events, list) and 3 <= len(events) <= 500,
         'unbounded or missing original CPU events')
    allowed = {'pc', 'frame', 'r0', 'r1', 'r2', 'r3',
               'reply_valid', 'reply_header', 'reply_payload', 'pending'}
    deny(all(isinstance(e, dict) and allowed.issuperset(e.keys())
             and isinstance(e.get('pc'), str)
             and isinstance(e.get('frame'), int) and e['frame'] >= 4179
             for e in events), 'untrusted or private byte fields in event')
    deny(all(a['frame'] <= b['frame'] for a, b in zip(events, events[1:])),
         'native chronology regressed')
    deny(not any(e['pc'] == '0x806449e' for e in events),
         'manual move menu reached; no-input automatic sequence uncertified')

    def hits(pc, **kwargs):
        return [(i, e) for i, e in enumerate(events) if e['pc'] == pc and
                all(e.get(k) == v for k, v in kwargs.items())]

    emit = hits('0x806bd80', r0=0, r2=10)
    deny(len(emit) == 3 and len(hits('0x9f1f000')) == 3
         and len(hits('0x8065eb4')) == 3,
         'incorrect original actor0 callback or move emitter count')
    deny(len(hits('0x806261c', r0=0)) >= 3,
         'missing original player controller completions')
    slots, committed_moves, last_commit = [], [], -1
    for n, (idx, e) in enumerate(emit):
        payload = e.get('r3')
        deny(isinstance(payload, int) and 0 <= payload < 1024,
             'invalid native automatic move payload')
        slot, target = payload & 255, payload >> 8
        deny(slot < 4 and target == 1, 'wrong player move slot or opponent target')
        prior = events[last_commit + 1:idx]
        callbacks = [i for i, x in enumerate(prior) if x['pc'] == '0x9f1f000']
        preflights = [i for i, x in enumerate(prior) if x['pc'] == '0x8065eb4']
        deny(len(callbacks) == len(preflights) == 1 and callbacks[0] < preflights[0],
             'original auto callback/preflight not owned by this request')
        stop = emit[n + 1][0] if n + 1 < len(emit) else len(events)
        tail = events[idx + 1:stop]
        replies = [(i, x) for i, x in enumerate(tail)
                   if x['pc'] == '0x806b370' and x.get('r0') == 0
                   and x.get('r1') == 1 and x.get('r3') == 6
                   and x.get('reply_valid') == 1
                   and x.get('reply_header') == 0x0A20
                   and x.get('reply_payload') == payload]
        deny(len(replies) == 1, 'missing or duplicated original actor0 buffer-B reply')
        def find(pc, after, pred=lambda x: True):
            items = [(i, x) for i, x in enumerate(tail)
                     if i > after and x['pc'] == pc and pred(x)]
            deny(bool(items), 'missing ordered original native marker ' + pc)
            return items[0]
        ci, _ = find('0x806261c', replies[0][0], lambda x: x.get('r0') == 0)
        vi, _ = find('0x8094330', ci, lambda x: x.get('r0') == 0)
        si, sc = find('0x809435c', vi)
        mi, mc = find('0x8094374', si)
        ti, tc = find('0x8094380', mi)
        deny(sc.get('r0') == slot and mc.get('r0') == moves[slot]
             and tc.get('r2') == target,
             'original slot/move/target commit mismatch')
        deny(idx + 1 + ti > last_commit, 'old native action commit reused')
        last_commit = idx + 1 + ti
        slots.append(slot)
        committed_moves.append(mc['r0'])
    decrements = [sum(slot == i for slot in slots) for i in range(4)]
    deny([a - b for a, b in zip(before, after)] == decrements,
         'PP did not decrement exactly once per native player move')
    deny(slots == [3, 1, 1] and committed_moves == [269, 157, 157],
         'exact private wild fixture changed')
    return {
        'scope': 'EXISTING exact-ROM native wild-single no-input observation only',
        'modified_rom_sha256': ROM_SHA,
        'source_preconstructor_request_verified': True,
        'original_player_native_reply_accept_commit': 3,
        'player_owned_pp_decrements': sum(decrements),
        'manual_move_menu_visits': 0,
        'host_move_menu_buttons_sent': 0,
        'general_move_legality_certified': False,
        'engine_one_use_epoch_certified': False,
        'new_hybrid_hook_installed': False,
        'whole_battle_completed': False,
        'protected_current_modified': False,
        'formal_gameplay_acceptance_passes': 0,
        'production_rom_promotion_authorized': False,
    }

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--private-trace', type=Path, required=True)
    args = ap.parse_args()
    if not args.private_trace.is_file() or args.private_trace.is_symlink():
        ap.error('existing regular private report file required')
    try:
        result = audit(json.loads(args.private_trace.read_text(encoding='utf-8')))
    except (ValueError, KeyError, TypeError) as e:
        ap.error(str(e))
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
