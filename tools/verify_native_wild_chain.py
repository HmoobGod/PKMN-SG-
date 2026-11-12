#!/usr/bin/env python3
"""Read-only same-process exact-ROM CPU wild-battle chain validator.

Does NOT prove engine request/reply ownership, source-LAB patch execution, move
legality, a unique outcome enum, or any of the 20 production acceptance cases.
Original controller bytes, SRAM, or savestates are not required or exported.
"""
import argparse
import json
from pathlib import Path

EXACT_ROM_SHA256 = '4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44'
PP = '0x809e6ba'
FIRST_GATE = '0x808e31a'
STATE_LOAD = '0x808e370'
TERMINAL_GATE = '0x808e374'
MAIN_CLEAR = '0x808e336'


def verify_capture(capture, console=None, require_terminal_gate=True, require_state_word=True):
    if capture.get('rom_sha256') != EXACT_ROM_SHA256:
        raise ValueError('exact modified-ROM hash not established')
    events = capture.get('original_cpu_events')
    if not isinstance(events, list) or not events:
        raise ValueError('empty CPU event log')
    episodes, current, previous_time = [], [], -1.0
    allowed = {PP, FIRST_GATE, STATE_LOAD, TERMINAL_GATE, MAIN_CLEAR}
    for e in events:
        if not isinstance(e, dict) or e.get('pc') not in allowed:
            raise ValueError('unexpected original CPU event')
        timestamp = e.get('t')
        if not isinstance(timestamp, (float, int)) or timestamp <= previous_time:
            raise ValueError('non-monotonic CPU chronology')
        previous_time = timestamp
        if e.get('main') != 2:
            raise ValueError('CPU event not scoped to active Main battle bit')
        pc = e['pc']
        if pc == PP:
            if e.get('r0') not in ('0x0', '0x1') or e.get('after_pc') != '0x809e6bc':
                raise ValueError('PP CPU ownership/step mismatch')
            if not isinstance(e.get('before'), int) or e['before'] - 1 != e.get('after'):
                raise ValueError('PP is not one-byte decrement witness')
            if not isinstance(e.get('pp_addr'), str) or not (0x02000000 <= int(e['pp_addr'], 16) < 0x02040000):
                raise ValueError('PP RAM address scope mismatch')
        if pc == STATE_LOAD:
            if (e.get('r5'), e.get('state_word'), e.get('after_r3'), e.get('after_pc')) != ('0x2001ab4', '0x4', '0x4', '0x808e372'):
                raise ValueError('state-load CPU memory witness mismatch')
        if pc in (FIRST_GATE, TERMINAL_GATE):
            expected = '0x808e364' if pc == FIRST_GATE else '0x808e324'
            if e.get('Z') != 1 or e.get('branch_observed_taken') is not True or e.get('after_pc') != expected:
                raise ValueError('original taken branch CPU witness missing')
        if pc == TERMINAL_GATE and require_state_word:
            if (e.get('r5'), e.get('state_word'), e.get('r3')) != ('0x2001ab4', '0x4', '0x4'):
                raise ValueError('terminal gate state-word CPU mismatch')
        current.append(e)
        if pc == MAIN_CLEAR:
            if (e.get('store_addr'), e.get('before'), e.get('after'), e.get('after_pc'), e.get('r2')) != ('0x3005a0d', 2, 0, '0x808e338', '0x0'):
                raise ValueError('original Main byte-clear store not witnessed')
            pp = [x for x in current if x['pc'] == PP]
            actors = {x['r0'] for x in pp}
            if actors != {'0x0', '0x1'} or not any(x['pc'] == FIRST_GATE for x in current):
                raise ValueError('no player+foe PP and first gate before clear')
            if require_terminal_gate and not any(x['pc'] == TERMINAL_GATE for x in current):
                raise ValueError('no terminal gate preceding Main clear')
            if require_state_word and not any(x['pc'] == STATE_LOAD for x in current):
                raise ValueError('no live state-load before terminal clear')
            episodes.append({
                'first_pp_t': pp[0]['t'], 'clear_t': e['t'],
                'player_pp_writes': sum(x['r0'] == '0x0' for x in pp),
                'foe_pp_writes': sum(x['r0'] == '0x1' for x in pp),
                'first_gate_taken': True,
                'terminal_gate_taken': any(x['pc'] == TERMINAL_GATE for x in current),
                'state_word_0x02001AB4': '0x4' if any(x['pc'] == STATE_LOAD for x in current) else 'NOT_OBSERVED'
            })
            current = []
    if len(episodes) < 2:
        raise ValueError('needs at least two complete consecutive CPU battle episodes')
    if console is not None:
        movement_seen = False
        for line in console.splitlines():
            if not line.startswith('KEY '):
                continue
            k = line.split()[1]
            if k in {'Left', 'Right', 'Up', 'Down'}:
                movement_seen = True
            elif k == 'x' and not movement_seen:
                continue  # only prior menu confirm
            else:
                raise ValueError('host battle input may contaminate native witness')
        if not movement_seen:
            raise ValueError('no verified movement inputs')
    return {
        'classification': 'ORIGINAL_EXACT_ROM_NATIVE_CPU_MULTI_ENCOUNTER_RESEARCH',
        'complete_cpu_episodes': len(episodes),
        'episodes': episodes,
        'trailing_incomplete_events': len(current),
        'same_emulator_process_log': True,
        'original_outcome_semantics': 'UNCLASSIFIED',
        'engine_request_ownership': 'NOT_PROVEN',
        'source_lab_auto_execution': 'NOT_PROVEN',
        'fixed_status_labels': {'historical_unmatched_pp_1': 'UNCLASSIFIED', 'historical_unmatched_pp_2': 'UNCLASSIFIED', 'formal_native_acceptance': '0/20'},
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('cpu_events_json')
    parser.add_argument('--console')
    a = parser.parse_args()
    events = json.loads(Path(a.cpu_events_json).read_text())
    console = Path(a.console).read_text() if a.console else None
    print(json.dumps(verify_capture(events, console), indent=2))
