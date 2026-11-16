#!/usr/bin/env python3
"""Read-only PRIVATE EWRAM snapshot timeline, never prints raw contents.

ROM handler 0x08065EB4 loads a move-slot byte via a pointer at 0x02001E90,
plus 0x106 for battler 0. This is a narrow runtime inference only. No source
symbol identity, move-scoring algorithm, legality, or manual fallback claim.
"""
import argparse
import json
import re
from pathlib import Path

EWRAM_BASE=0x02000000
EWRAM_SIZE=0x40000
POINTER_LOCATION=0x02001E90
MOVE_SLOT_OFFSET=0x106
TARGET_OFFSET=0x10A


def decode_snapshot(memory):
    if not isinstance(memory,(bytes,bytearray,memoryview)) or len(memory)!=EWRAM_SIZE:
        return None
    i=POINTER_LOCATION-EWRAM_BASE
    ptr=int.from_bytes(memory[i:i+4],'little')
    if not EWRAM_BASE<=ptr<EWRAM_BASE+EWRAM_SIZE:
        return None
    base=ptr-EWRAM_BASE
    if base+max(MOVE_SLOT_OFFSET,TARGET_OFFSET)>=len(memory):
        return None
    slot=memory[base+MOVE_SLOT_OFFSET]
    target=memory[base+TARGET_OFFSET]
    if not 0<=slot<=3 or not 0<=target<=3:
        return None
    return {'move_slot':int(slot),'target_cursor_candidate':int(target)}


def summarize(frames):
    if not isinstance(frames,list) or any(type(x) is not tuple or len(x)!=2 for x in frames):
        raise ValueError('invalid private snapshot list')
    distinct=set()
    timeline=[]
    rejected=0
    for frame,blob in sorted(frames,key=lambda x:x[0]):
        if type(frame) is not int or frame<0 or frame in distinct:
            raise ValueError('missing/duplicate frame identifier')
        distinct.add(frame)
        parsed=decode_snapshot(blob)
        if parsed is None:
            rejected+=1
            continue
        timeline.append((frame,parsed['move_slot'],parsed['target_cursor_candidate']))
    grouped=[]
    for f,s,t in timeline:
        if grouped and grouped[-1]['move_slot']==s and grouped[-1]['target_cursor_candidate']==t:
            grouped[-1]['last_sampled_frame']=f
            grouped[-1]['sample_count']+=1
        else:
            grouped.append({'first_sampled_frame':f,'last_sampled_frame':f,
                            'move_slot':s,'target_cursor_candidate':t,
                            'sample_count':1})
    return {'schema':'sg-private-original-battle-cursor-timeline-UNVERIFIED-v1',
            'accepted_snapshots':len(timeline),
            'rejected_snapshots':rejected,
            'cursor_segments':grouped,
            'cursor_is_confirmed_move_planner_output':False,
            'move_legality_certified':False,
            'manual_fallback_certified':False,
            'original_native_acceptance_scenarios':0,
            'production_authorized':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-ewram-dir',required=True,type=Path)
    parser.add_argument('--prefix',default='s_ewram_')
    args=parser.parse_args()
    files=sorted(args.private_ewram_dir.glob(args.prefix+'*.bin'))
    if not files:
        raise SystemExit('no private memory snapshots')
    frames=[]
    for f in files:
        m=re.fullmatch(re.escape(args.prefix)+r'(\d+)\.bin',f.name)
        if not m:
            continue
        frames.append((int(m.group(1)),f.read_bytes()))
    print(json.dumps(summarize(frames),sort_keys=True,indent=2))

if __name__=='__main__':main()
