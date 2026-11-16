#!/usr/bin/env python3
"""Read-only original-ROM CPU-store chain candidate; NEVER a Smart Auto acceptance.

Input is private and stays local. The recorder observes mGBA guest CPU stores
from an existing unmodified game; this auditor does not authenticate an R7/R8
patch, manual fallback, original request ownership or dynamic move legality.
"""
import argparse
import json
from pathlib import Path

EMITTER_PC = '0x0806bd8e'
FIGHT_LR = '0x08017211'
MOVE_LR = '0x08065f2d'
SWITCH_LR = '0x0801723b'
PP_RAW_PC = '0x0809e6be'  # executing Thumb store at 0x0809e6ba
MAX_ROWS = 100_000


def _rows(records):
    if type(records) is not list or len(records) > MAX_ROWS:
        raise ValueError('bounded list of private CPU records required')
    if any(type(x) is not dict for x in records):
        raise ValueError('malformed CPU record')
    return records


def _event(e, kind):
    if e.get('pc') != EMITTER_PC:
        return False
    if type(e.get('f')) is not int or not 0 < e['f'] <= 12000:
        raise ValueError('bad emitter frame')
    regs = e.get('r')
    if type(regs) is not list or len(regs) != 8 or any(type(v) is not int for v in regs):
        raise ValueError('bad emitter registers')
    if type(e.get('width')) is not int or e['width'] != 1 or type(e.get('value')) is not int:
        raise ValueError('bad emitter store width/value')
    if regs[0] != 0:
        return False  # opponents/NPC partners cannot count as actor0 evidence
    return (e.get('lr'), e['value']) == kind


def evaluate(frames, owner, pp):
    frames = _rows(frames); owner = _rows(owner); pp = _rows(pp)
    summaries = [x for x in frames if x.get('event') == 'completed']
    saves = [x for x in frames if x.get('event') == 'save_load']
    installed = sum(x.get('event') == 'pp_hook_installed' for x in frames)
    if (len(summaries) != 1 or summaries[0].get('exit_code') != 0 or
            type(summaries[0].get('frames')) is not int or summaries[0]['frames'] < 3000 or
            len(saves) != 1 or saves[0].get('loaded') is not True or
            saves[0].get('full_128kb_match') is not True or installed != 1):
        raise ValueError('no complete SHA-guarded saved-game emulation witness')
    emitters = [x for x in owner if x.get('pc') == EMITTER_PC and
                type(x.get('r')) is list and len(x['r']) == 8 and x['r'][0] == 0]
    fights = [x for x in emitters if _event(x, (FIGHT_LR, 0))]
    moves = [x for x in emitters if _event(x, (MOVE_LR, 10))]
    switches = [x for x in emitters if _event(x, (SWITCH_LR, 2))]
    unknown = [x for x in emitters if not (_event(x, (FIGHT_LR, 0)) or
               _event(x, (MOVE_LR, 10)) or _event(x, (SWITCH_LR, 2)))]
    writes = []
    for x in pp:
        if x.get('raw_pc') != PP_RAW_PC:
            continue
        if (type(x.get('f')) is not int or type(x.get('before')) is not int or
            type(x.get('after')) is not int or type(x.get('value')) is not int or
            type(x.get('target')) is not int or type(x.get('width')) is not int or
            type(x.get('thumb_flag')) is not int or type(x.get('r')) is not list or
            len(x['r']) != 8 or any(type(v) is not int for v in x['r'])):
            raise ValueError('malformed original PP writer record')
        if x['r'][0] != 0:
            continue
        writes.append(x)
    credible_pp = (len(writes) == 1 and writes[0]['width'] == 1 and
                   writes[0]['thumb_flag'] == 1 and writes[0]['target'] == 0 and
                   0 < writes[0]['before'] <= 99 and
                   writes[0]['before'] == writes[0]['after'] + 1 and
                   writes[0]['value'] == writes[0]['after'])
    chronology = (len(fights) == 1 and len(moves) == 1 and credible_pp and
                  fights[0]['f'] <= moves[0]['f'] < writes[0]['f'])
    candidate = chronology and not switches and not unknown
    # Deliberately omit all private memory contents and CPU registers.
    return {
        'schema':'sg-r9-existing-rom-original-cpu-candidate-v1',
        'source':'unmodified user-supplied ROM, disposable save/mGBA only',
        'player0_fight_emitter_count':len(fights),
        'player0_move_emitter_count':len(moves),
        'player0_switch_emitter_count':len(switches),
        'player0_unclassified_emitter_count':len(unknown),
        'player0_compatible_original_pp_debit_writes':len(writes),
        'fight_frame':fights[0]['f'] if len(fights) == 1 else None,
        'move_frame':moves[0]['f'] if len(moves) == 1 else None,
        'pp_frame':writes[0]['f'] if credible_pp else None,
        'observed_pp_before':writes[0]['before'] if credible_pp else None,
        'observed_pp_after':writes[0]['after'] if credible_pp else None,
        'cpu_chain_candidate_UNVERIFIED':bool(candidate),
        'input_free_auto_battle_certified':False,
        'original_request_buffer_abi_certified':False,
        'player0_request_and_legality_certified':False,
        'original_manual_menu_fallback_certified':False,
        'no_forced_switch_safety_certified':False,
        'new_smart_auto_patch_executed':False,
        'formal_native_acceptance':0,
        'production_authorized':False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-frame-log', type=Path, required=True)
    p.add_argument('--private-owner-log', type=Path, required=True)
    p.add_argument('--private-pp-log', type=Path, required=True)
    a = p.parse_args()
    def load(f):
        if f.stat().st_size > 20_000_000:
            raise ValueError('private log too large')
        return [json.loads(x) for x in f.read_text().splitlines()]
    print(json.dumps(evaluate(load(a.private_frame_log),load(a.private_owner_log),load(a.private_pp_log)),indent=2,sort_keys=True))

if __name__ == '__main__': main()
