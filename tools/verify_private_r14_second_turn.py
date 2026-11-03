#!/usr/bin/env python3
"""R14 fail-closed *offline* consistency of a fixture-only in-ROM first auto,
original second natural player request, manual fallback and manual acceptance.
Synthetic reports are never evidence of live behavior. This does not authorize
submissions or certify general engine-owned ownership/move/target legality.
"""
import argparse
import hashlib
import json
from pathlib import Path
from verify_private_r13_in_rom import verify_positive, BadTrace, LAB_SHA, SAVE_SHA, STATES

SECOND_SHA = 'b92746c4fe980c1d9b05da0eddbff8a6765524390a67fd6f97950b6a41b2cf24'
FIRST_SHA = '46a2425f06b61f66a71f361fa96241c01f73268933fbb0f6fa6264b99086adeb'


def demand(ok, msg):
    if not ok:
        raise BadTrace(msg)


def pos(rows, pc, **fields):
    return [(i, e) for i, e in enumerate(rows) if e.get('pc') == pc and
            all(e.get(k) == v for k, v in fields.items())]


def one(rows, pc, **fields):
    hits = pos(rows, pc, **fields)
    demand(len(hits) == 1, f'exactly one {pc} {fields} required; got {len(hits)}')
    return hits[0]


def ordered(rows):
    demand(isinstance(rows, list) and 1 <= len(rows) <= 300, 'bounded native event timeline required')
    demand(all(isinstance(r, dict) and isinstance(r.get('pc'), str)
               and isinstance(r.get('frame'), int) and r['frame'] >= 0 for r in rows),
           'ill-formed original trace')
    frames = [r['frame'] for r in rows]
    demand(frames == sorted(frames), 'reversed original frame order')
    return rows


def verify_r14(j, *, require_original_sha=True):
    demand(isinstance(j, dict) and j.get('schema') == 'sg16266-r14-second-live-request-manual-fallback-v1',
           'wrong R14 report/schema')
    demand(j.get('candidate_rom_sha256') == LAB_SHA and j.get('save_sha256') == SAVE_SHA
           and j.get('precontroller_state_sha256') in STATES, 'source identity mismatch')
    for key in ('general_owner_certified', 'complete_move_legality',
                'complete_target_legality', 'general_playable_auto'):
        demand(j.get(key) is False, 'forbidden authority claim: ' + key)
    demand(j.get('formal_auto_suite_passes') == 0, 'fixture lab falsely promoted into formal 20-scenario suite')
    demand(j.get('first_original_auto_accepted') is True and j.get('first_original_auto_move') == 157,
           'first native auto not positively observed')
    first = j.get('first_r13_witness')
    demand(isinstance(first, dict), 'first private native witness missing')
    # Reuse R13's independently tested strict original-emitter/reply/commit ordering.
    verify_positive(first)
    demand(first['rom_sha256'] == j['candidate_rom_sha256'] and
           first['save_sha256'] == j['save_sha256'] and
           first['state_sha256'] == j['precontroller_state_sha256'],
           'first/second fixtures not tied to the same exact process inputs')
    demand(j.get('second_copy_stores') == 44 and j.get('second_pending_steps') == 23,
           'second original 44-store / later pending sequence absent')
    demand(j.get('second_live_moves') == [325, 157, 92, 269] and
           j.get('second_live_request_moves') == [325, 157, 92, 269] and
           j.get('second_live_pp') == [20, 9, 10, 20],
           'own second request not drifted from initial PP')
    c = j.get('second_copy_witness')
    demand(isinstance(c, dict), 'native second-copy witness absent')
    demand(c.get('actor') == 0 and c.get('direction') == 0 and c.get('length') == 44
           and c.get('post_pc') == '0x806b3c6', 'wrong original native copy route')
    try:
        raw = [bytes.fromhex(c[k]) for k in ('source_before_hex','source_after_hex',
                                               'dest_after_hex','store_values_hex')]
    except (TypeError, ValueError, KeyError) as exc:
        raise BadTrace('bad native request hex') from exc
    demand(all(len(b) == 44 for b in raw) and all(b == raw[0] for b in raw),
           'second copy not completed byte-identically')
    demand(c.get('store_indices') == list(range(44)), 'original store instructions incomplete/reordered')
    digest = hashlib.sha256(raw[0]).hexdigest()
    demand(j.get('second_request_sha256') == digest and
           (digest == SECOND_SHA if require_original_sha else True), 'second request SHA mismatch')
    demand(j.get('first_request_sha256') == FIRST_SHA and digest != FIRST_SHA,
           'stale identical request not excluded from this test')
    demand(raw[0][:4] == b'\x13\x00\x00\x00' and
           [int.from_bytes(raw[0][4+2*i:6+2*i], 'little') for i in range(4)] == j['second_live_moves'] and
           list(raw[0][12:16]) == j['second_live_pp'], 'raw own request mismatch')
    windows = j.get('post_first_turn_windows')
    demand(isinstance(windows, list) and 1 <= len(windows) <= 18 and
           all(isinstance(w, dict) and w.get('kind') in (1,2) for w in windows) and
           windows[-1]['kind'] == 2 and all(w['kind'] == 1 for w in windows[:-1]),
           'original second request not naturally reached before actor0 action')
    pp_series=[w.get('pp') for w in windows]
    demand(all(w.get('steps',0) > 0 for w in windows) and
           all(p in ([20,10],[20,9]) for p in pp_series) and
           pp_series[-1] == [20,9] and
           all(pp_series[k][1] >= pp_series[k+1][1] for k in range(len(pp_series)-1)),
           'no monotonic native own PP transition after first automatic move')
    demand(windows[-1]['pending'] & 1 == 0 and
           windows[-1].get('pc') == '0x806b372' and
           windows[-1]['end'] == j.get('second_request_frame'),
           'second original copy cannot begin with actor0 already pending')
    demand(windows[0]['start'] > max(r['frame'] for r in first['events']) and
           all(windows[k]['end'] <= windows[k+1]['start'] for k in range(len(windows)-1)),
           'second request not after first original accepted native move')
    before = ordered(j.get('second_event_trace'))
    after = ordered(j.get('second_manual_events'))
    demand(before[0]['frame'] == j['second_request_frame'] and
           after[0]['frame'] >= before[-1]['frame'], 'native second-turn timeline not continuous')
    guard_idx, _ = one(before,'0x9f2d000')
    denied_idx, denied = one(before,'0x9f20022',r0=0)
    # Original manual chooser is commonly called once per frame; require at
    # least one, and its first call after the denied private C gate.
    manual_hits = pos(before,'0x806449c',r0=0)
    demand(manual_hits and guard_idx < denied_idx < manual_hits[0][0],
           'original manual fallback not after private gate denial')
    demand(len(pos(before,'0x8065eb4',r0=0)) == 0 and
           len(pos(before,'0x806bd80',r0=0)) == 0 and
           len(pos(before,'0x9f20022',r0=1)) == 0,
           'denied second request submitted an unauthorized automatic player command')
    demand(not any(e.get('pc') in ('0x8094330','0x809435c','0x8094374','0x8094380') and e.get('r6') == 0
                   for e in before) and not any(e.get('pc')=='0x80e5e5c' and e.get('r0')==0 for e in before),
           'second actor0 native restriction/commit happened before manual permission')
    demand(pos(before,'0x806bd80',r0=1,r2=10), 'original opponent emission absent')
    demand(j.get('second_auto_emissions') == 0 and j.get('second_original_manual_menu') is True,
           'second automatic/mode claim unsupported')
    demand(j.get('manual_button_inputs_before_fallback') == 0 and
           j.get('manual_button_confirm_after_fallback') == 1 and
           j.get('second_manual_accept_after_fallback') is True,
           'manual confirmation timing not separated from auto test')
    em_idx,em = one(after,'0x806bd80',r0=0,r2=10,r3=257)
    rep_idx,rep=one(after,'0x806b370',r0=0,r1=1,r3=6)
    # The original consumer can perform several unrelated completion events;
    # the relevant one must be between its reply and restriction result.
    native_idx,_ = one(after,'0x80e5e5c',r0=0,r6=0)
    completes=[(i,r) for i,r in pos(after,'0x806261c',r4=0,pending=0)
               if rep_idx<i<native_idx]
    demand(len(completes)==1, 'manual reply not followed by original completion')
    restriction_idx,_=one(after,'0x8094330',r0=0,r6=0)
    slot_idx,_=one(after,'0x809435c',r0=1,r6=0)
    move_idx,_=one(after,'0x8094374',r0=157,r6=0)
    target_idx,_=one(after,'0x8094380',r2=1,r6=0)
    demand(em_idx < rep_idx < completes[0][0] < native_idx < restriction_idx < slot_idx < move_idx < target_idx,
           'original manual accept/reply/restriction/commit order violated')
    demand(rep.get('reply_valid') == 1 and rep.get('reply_payload') == 257,
           'original manual reply invalid')
    demand(len(pos(after,'0x806bd80',r0=0)) == 1 and
           len(pos(after,'0x8065eb4',r0=0)) == 0 and
           len(pos(after,'0x9f20022',r0=1)) == 0,
           'manual second move mislabelled in-ROM auto or duplicated')
    return {'scope':'one fixed-R13 original wild fixture, two turns only',
            'first_turn':'in-ROM native accepted','second_turn':'native manual fallback and accepted human input',
            'in_rom_auto_submissions_total':1,'second_turn_auto_submissions':0,
            'formal_general_auto_acceptance':0}

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    print('PASS',json.dumps(verify_r14(json.loads(a.report.read_text())),sort_keys=True))