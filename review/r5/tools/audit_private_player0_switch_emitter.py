#!/usr/bin/env python3
"""Conservative source-only runtime observation of player0 action-2 emission.

No action-2 emission in a bounded trace is NOT proof that forced switch is
unreachable. This tool never certifies safety or modified-ROM acceptance.
"""
import argparse
import json
from pathlib import Path

EMITTER_STORE='0x0806bd8e'
ACTION_CALLER='0x08017211'
SWITCH_CALLER='0x0801723b'
MOVE_CALLER='0x08065f2d'


def evaluate(rows):
    if type(rows) is not list or len(rows)>100000:
        raise ValueError('bounded trace required')
    fight=switch=unknown=move=0
    for e in rows:
        if type(e) is not dict:raise ValueError('not a CPU store row')
        if e.get('pc')!=EMITTER_STORE:continue
        r=e.get('r'); lr=e.get('lr');value=e.get('value');width=e.get('width');f=e.get('f')
        if type(r) is not list or len(r)!=8 or any(type(q) is not int or not 0<=q<=0xffffffff for q in r) or type(value) is not int or type(width) is not int or width!=1 or type(f) is not int or f<0:
            raise ValueError('malformed emitter CPU snapshot')
        if r[0]!=0:continue # enemy/non-player record never player evidence
        if lr==ACTION_CALLER and value==0:fight+=1
        elif lr==SWITCH_CALLER and value==2:switch+=1
        elif lr==MOVE_CALLER and value==10:move+=1
        else:unknown+=1
    return {'schema':'sg-source-only-player0-action-switch-risk-r4',
            'player0_fight_action0_emitter_rows':fight,
            'player0_switch_action2_emitter_rows':switch,
            'player0_move_action10_emitter_rows':move,
            'player0_unclassified_emitter_rows':unknown,
            'no_player0_action2_observed_in_this_bounded_trace':bool(fight>0 and switch==0 and unknown==0),
            'no_forced_switch_execution_or_reachability_certified':False,
            'manual_fallback_certified':False,
            'native_acceptance_scenarios':0,'production_authorized':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--private-owner-log',type=Path,required=True)
    rows=[json.loads(line) for line in ap.parse_args().private_owner_log.read_text().splitlines()]
    print(json.dumps(evaluate(rows),indent=2,sort_keys=True))

if __name__=='__main__':main()
