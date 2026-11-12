#!/usr/bin/env python3
"""Attest second independent exact modified-ROM no-button wild replay.
ROM/save/host/savestates and private CPU trace never enter public git.
Eight submitted commands do NOT prove eight PP-consuming attacks or a terminal.
"""
import argparse
import json
from pathlib import Path

ROM_SHA='4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44'
SAVE_SHA='8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
FIRST_PENDING_SHA='91503b1db0aae28a4c004d1af4f7e618d7aed4d291aa236950362a730763fab6'
PRE_SHA='0a6237c1f660ad1263e5c6b735ae9d0d7ddb4d12808431f8d05830c6c615944b'
PENDING_SHA='8d9bbaf818ab24cf5d645b65b967997420bcf5751b856d9df109fa5c44f48d98'
REQUEST_SHA='46a2425f06b61f66a71f361fa96241c01f73268933fbb0f6fa6264b99086adeb'
SCHEMA='sg-exact-modified-independent-wild-metadata-v1'
SLOTS=[3,1,1,1,3,2,1,1]
MOVE_IDS=[325,157,92,269]

def must(value, message):
    if not value: raise ValueError(message)

def attest(r):
    must(isinstance(r,dict) and r.get('schema')==SCHEMA,'unknown research schema')
    must(r.get('rom_sha256')==ROM_SHA and r.get('save_sha256')==SAVE_SHA,
         'exact ROM/save SHA mismatch')
    must(r.get('preconstructor_sha256')==PRE_SHA and r.get('pending_state_sha256')==PENDING_SHA
         and PENDING_SHA!=FIRST_PENDING_SHA,'not independent exact original battle')
    must(r.get('request_sha256')==REQUEST_SHA and r.get('request_copy_stores')==44
         and r.get('pending_after_copy_steps')==23,'unverified original player request')
    must(r.get('actor0_installer')==r.get('foe_installer')==1
         and r.get('player_kind')==1 and r.get('foe_kind')==3
         and r.get('battle_flags')==4 and r.get('battlers')==2,
         'unverified original player ownership or wild single')
    must(r.get('host_move_menu_inputs')==0 and r.get('guest_memory_writes')==0
         and r.get('new_native_hook_installed') is False,
         'unexpected host input, mutation or hook claim')
    chunks=r.get('samples')
    must(isinstance(chunks,list) and len(chunks)==6,'unbounded frame capture')
    for i,c in enumerate(chunks):
        must(c.get('chunk')==i and c.get('begin')==4692+i*350
             and c.get('end')==4692+(i+1)*350 and c.get('steps',0)>0
             and c.get('flags')=='0x4' and c.get('pending')=='0x0'
             and c.get('manual_menu')==0 and isinstance(c.get('auto'),list)
             and isinstance(c.get('events'),int) and c['events']>=0,
             'incorrect contiguous original CPU trace / menu')
    must(chunks[-1]['auto']==chunks[-2]['auto']==[]
         and chunks[-1]['events']==chunks[-2]['events']==0,
         'no two-chunk quiet tail demonstrated')
    must(chunks[0]['pp']==[20,9,10,19] and chunks[-1]['pp']==[20,7,9,18],
         'player PP time-series mismatch')
    ev=r.get('events')
    must(isinstance(ev,list) and 70<=len(ev)<=700,'missing/oversized CPU witness')
    allowed={'pc','frame','r0','r1','r2','r3','pending','reply_valid',
             'reply_header','reply_payload'}
    for e in ev:
        must(isinstance(e,dict) and set(e).issubset(allowed)
             and isinstance(e.get('pc'),str) and isinstance(e.get('frame'),int)
             and 4692<=e['frame']<=6792,
             'invalid or private extra event data')
    must(all(a['frame']<=b['frame'] for a,b in zip(ev,ev[1:])),
         'out-of-order native instructions')
    must(all(e['pc']!='0x806449e' for e in ev),'manual move menu visited')
    own_emit=[e for e in ev if e['pc']=='0x806bd80' and e.get('r0')==0]
    must(len(own_emit)==15 and sum(e.get('r2')==0 for e in own_emit)==7
         and all((e.get('r2')==0 and e.get('r3')==256)
             or (e.get('r2')==10 and e.get('r3') in (257,258,259))
             for e in own_emit),
         'player auto emitted unknown item/capture/switch/run action')
    emitted=[(i,e) for i,e in enumerate(ev) if e['pc']=='0x806bd80'
             and e.get('r0')==0 and e.get('r2')==10]
    must(len(emitted)==8 and
         [e['r3'] for _,e in emitted]==[256|slot for slot in SLOTS],
         'unexpected original player move+target submissions')
    must(sum(e['pc']=='0x9f1f000' for e in ev)==8
         and sum(e['pc']=='0x8065eb4' for e in ev)==8,
         'original in-ROM scorer/preflight count mismatch')
    for n,(start,em) in enumerate(emitted):
        end=emitted[n+1][0] if n+1<len(emitted) else len(ev)
        tail=ev[start+1:end]
        def first(pc, after=-1, pred=lambda x:True):
            rows=[(i,x) for i,x in enumerate(tail)
                  if i>after and x['pc']==pc and pred(x)]
            must(bool(rows),'missing original ordered player '+pc)
            return rows[0]
        payload=em['r3'];slot=SLOTS[n]
        ri,_=first('0x806b370',pred=lambda x:x.get('r0')==0
                   and x.get('r1')==1 and x.get('r3')==6
                   and x.get('reply_valid')==1 and x.get('reply_header')==0x0a20
                   and x.get('reply_payload')==payload)
        ci,_=first('0x806261c',ri,lambda x:x.get('r0')==0)
        vi,_=first('0x8094330',ci,lambda x:x.get('r0')==0)
        si,_=first('0x809435c',vi,lambda x:x.get('r0')==slot)
        mi,_=first('0x8094374',si,lambda x:x.get('r0')==MOVE_IDS[slot])
        ti,_=first('0x8094380',mi,lambda x:x.get('r2')==1)
        must(ri<ci<vi<si<mi<ti,'native completion/commit order')
    decrements=[a-b for a,b in zip([20,10,10,20],chunks[-1]['pp'])]
    must(decrements==[0,3,1,2] and sum(decrements)==6
         and all(0<=n<=SLOTS.count(i) for i,n in enumerate(decrements)),
         'PP delta not proven; submissions are not execution')
    return {'schema':'sg-second-wild-attested-public-summary-v1',
            'modified_rom_sha256':ROM_SHA,
            'independent_natural_wild_encounters_authenticated':2,
            'second_wild_player_native_move_submissions':8,
            'second_wild_original_reply_commit_pairs':8,
            'second_wild_observed_player_PP_decrements':6,
            'host_move_menu_inputs':0,'manual_move_menu_entries':0,
            'zero_command_quiet_tail_frames':700,
            'whole_battle_terminal_certified':False,
            'dynamic_move_legality_certified':False,
            'one_use_engine_epoch_certified':False,
            'new_hybrid_hook_installed':False,
            'formal_gameplay_acceptance':0,
            'production_promotion_authorized':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--private-report',type=Path,required=True)
    args=ap.parse_args()
    if not args.private_report.is_file() or args.private_report.is_symlink():
        ap.error('expected existing regular private metadata report')
    try: result=attest(json.loads(args.private_report.read_text(encoding='utf-8')))
    except (ValueError,KeyError,TypeError) as e: ap.error(str(e))
    print(json.dumps(result,sort_keys=True,indent=2))
if __name__=='__main__':main()
