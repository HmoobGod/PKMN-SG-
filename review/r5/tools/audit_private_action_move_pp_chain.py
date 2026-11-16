#!/usr/bin/env python3
"""Extra conservative host-only player0 Fight->Move->PP join.

Input traces and exact ROM stay local/private; output contains only redacted
frame/slot evidence. A positive result is NOT engine auto-planner provenance,
full legality, manual fallback, native acceptance or a deployable patch.
"""
import argparse
import hashlib
import json
from pathlib import Path

from audit_private_actor0_response_pp_join import (
    EMITTER_ADDR, EMITTER_STORES, thumb_bl_target,
    evaluate as evaluate_move_pp,
)
from audit_private_rom_controller_lineage import assess

FIGHT_LR = '0x08017211'
FIGHT_ACTION = 0
MAX_FIGHT_TO_MOVE_FRAMES = 5


def action_zero_packets(stores, rom):
    """Read full five-store original emitter packet; no snapshot/actor promotion."""
    if thumb_bl_target(rom, FIGHT_LR) != EMITTER_ADDR:
        return []
    good=[]
    for i, first in enumerate(stores):
        if not isinstance(first, dict) or first.get('pc') != f'0x{EMITTER_STORES[0]:08x}':
            continue
        r=first.get('r')
        if not isinstance(r,list) or len(r)!=8 or r[0]!=0 or r[1]!=1 or r[2]!=FIGHT_ACTION:
            continue
        if first.get('lr')!=FIGHT_LR:
            continue
        arg=r[3]
        if type(arg) is not int or not 0<=arg<=0xFFFF:
            continue
        candidate=stores[i:i+5]
        if len(candidate)!=5:
            continue
        f=first.get('f')
        addr=first.get('dst')
        try:
            start=int(addr,16)
            if start<0x02000000 or start>0x0203FFFA:
                continue
        except (TypeError,ValueError):
            continue
        expected_values=(32,0,arg,arg>>16 & 255,arg>>24 & 255)
        expected_widths=(1,1,2,1,1)
        expected_offsets=(0,1,2,4,5)
        valid=True
        for j,row in enumerate(candidate):
            try:
                regs=row['r']
                valid &= (isinstance(regs,list) and len(regs)==8 and
                          regs[0]==0 and row['lr']==FIGHT_LR and
                          type(row['f']) is int and row['f']==f and
                          row['pc']==f'0x{EMITTER_STORES[j]:08x}' and
                          row['raw_pc']==f'0x{EMITTER_STORES[j]+4:08x}' and
                          int(row['dst'],16)==start+expected_offsets[j] and
                          type(row['width']) is int and row['width']==expected_widths[j] and
                          type(row['value']) is int and row['value']==expected_values[j] and
                          not any(t in row for t in ('guest_writes','native_accepted',
                                                      'production_authorized')))
            except (KeyError,ValueError,TypeError):
                valid=False
            if not valid:
                break
        if valid:
            good.append({'f':f, 'arg':arg})
    return good


def evaluate(rom, stores, pp, battle_frame):
    basic = evaluate_move_pp(rom,stores,pp,battle_frame)
    # The ROM checker independently covers original action handler dispatch,
    # normal player response emitter, and action helper call edges.
    static = assess(rom)
    fight = action_zero_packets(stores,rom) if static['bounded_original_rom_dispatch_candidate'] else []
    response = basic['candidates']
    admitted=[]
    rejected=0
    used=set()
    for m in response:
        frame=m['response_frame']
        matches=[(j,z) for j,z in enumerate(fight)
                 if 0 < frame-z['f'] <= MAX_FIGHT_TO_MOVE_FRAMES]
        if len(matches)!=1 or matches[0][0] in used:
            rejected+=1
            continue
        j,z=matches[0]
        used.add(j)
        admitted.append({'fight_frame':z['f'], 'move_frame':frame,
                         'pp_frame':m['pp_frame'], 'slot_index':m['slot_index'],
                         'original_cpu_player0_fight_move_pp_candidate_UNVERIFIED':True})
    return {'schema':'sg-original-player0-fight-move-pp-UNVERIFIED-v1',
            'bounded_original_rom_dispatch':static['bounded_original_rom_dispatch_candidate'],
            'joined_fight_move_pp_candidates_UNVERIFIED':len(admitted),
            'rejected_or_missing_fight_for_move_candidates':rejected,
            'candidates':admitted,
            'smart_auto_planner_identity_certified':False,
            'original_move_target_legality_certified':False,
            'original_manual_fallback_certified':False,
            'no_automatic_forced_switch_certified':False,
            'native_acceptance_scenarios':0,
            'production_authorized':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-rom',required=True,type=Path)
    p.add_argument('--private-owner-stores',required=True,type=Path)
    p.add_argument('--private-pp-trace',required=True,type=Path)
    p.add_argument('--expected-rom-sha256',required=True)
    p.add_argument('--battle-ui-frame',type=int,required=True)
    args=p.parse_args()
    rom=args.private_rom.read_bytes()
    if hashlib.sha256(rom).hexdigest().lower()!=args.expected_rom_sha256.lower():
        raise SystemExit('private ROM identity mismatch')
    loads=lambda path:[json.loads(x) for x in path.read_text().splitlines()]
    z=evaluate(rom,loads(args.private_owner_stores),loads(args.private_pp_trace),args.battle_ui_frame)
    print(json.dumps(z,sort_keys=True,indent=2))


if __name__=='__main__': main()
