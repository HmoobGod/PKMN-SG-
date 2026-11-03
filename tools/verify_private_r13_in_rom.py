#!/usr/bin/env python3
"""Fail-closed offline consistency check for a PRIVATE R13 original-engine trace.
Only reproducible emulator event ordering can support one fixture-specific
in-ROM LAB acceptance; forged JSON is not independently authenticated proof.
"""
import argparse
import json
from pathlib import Path

LAB_SHA='70b0f846f8685cc09719476a166621289a5e7d47707695b5de9dc7f3e1bfde05'
DENY_SHA='cf577232b6fc5ee5df9cfdbd112f65e37c11122f8654ba2cdfab486ec4f458f8'
SAVE_SHA='8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
STATES={
 '4157e7c910d9a55a1f19484c4a2daf6eae9707d52ecff3083b9adff3d08d9085',
 '534a4b71dec2c5adff9b6a76639ac426469645ef44a64268fd713a08f0546bf8',
}
class BadTrace(ValueError):pass

def require(condition,msg):
    if not condition:raise BadTrace(msg)

def events(j):
    rows=j.get('events')
    require(isinstance(rows,list) and 1<=len(rows)<300,'missing/out-of-bounds native timeline')
    require(all(isinstance(r,dict) and isinstance(r.get('pc'),str) and
                isinstance(r.get('frame'),int) and r.get('frame')>=0 for r in rows),
            'invalid event format')
    require([r['frame'] for r in rows]==sorted(r['frame'] for r in rows),'reordered frame timeline')
    return rows

def check_common(j,positive):
    require(isinstance(j,dict),'not a trace object')
    require(j.get('rom_sha256')==(LAB_SHA if positive else DENY_SHA),'unexpected ROM identity')
    require(j.get('save_sha256')==SAVE_SHA,'unexpected original user save identity')
    require(j.get('state_sha256') in STATES if positive else
            j.get('state_sha256')==next(iter(sorted(STATES))),'unexpected fixture identity')
    # On the original read-only report copy/pending were seen by stepping the
    # original engine; this is evidence quality, never complete legality.
    require(j.get('copy_complete_44') is True and j.get('pending_set_after_steps')==23,
            'native copy/late pending sequence absent')
    require(j.get('status')==1 and 10000<=j.get('steps',0)<=20000000,
            'incomplete guest execution')
    return events(j)

def hits(rows,pc,**kv):
    return [(i,r) for i,r in enumerate(rows) if r['pc']==pc and all(r.get(k)==v for k,v in kv.items())]

def single(rows,pc,**kw):
    h=hits(rows,pc,**kw)
    require(len(h)==1,f'expected exactly one {pc} {kw}; found {len(h)}')
    return h[0]

def verify_positive(j):
    rows=check_common(j,True)
    for key in ('original_player_installer_count','original_foe_installer_count',
                'lab_native_in_rom_auto_submission','lab_native_in_rom_auto_acceptance'):
        require(j.get(key)==1,f'{key} not witnessed once')
    require(j.get('host_move_menu_buttons_sent')==0,'host moved menu, not in-ROM auto')
    for key in ('general_owner_certified','complete_move_legality',
                'complete_target_legality','normal_playable_auto_enabled',
                'automatic_items_or_capture'):
        require(j.get(key) is False,f'unsupported positive authority claim: {key}')
    _,score=single(rows,'0x9f20012',r0=4)
    stage,_=single(rows,'0x9f2d000')
    guard,r=single(rows,'0x9f20022',r0=1)
    branch,_=single(rows,'0x9f20032')
    auto,_=single(rows,'0x8065eb4',r0=0)
    em_idx,em=single(rows,'0x806bd80',r0=0,r2=10,r3=257)
    rep_idx,rep=single(rows,'0x806b370',r0=0,r1=1,r3=6)
    check_idx,_=single(rows,'0x80e5e5c',r0=0,r6=0)
    ends=[(i,r) for i,r in hits(rows,'0x806261c',r4=0) if rep_idx<i<check_idx and (r.get('pending',1)&1)==0]
    require(len(ends)==1,'missing exactly one actor0 reply completion before consumer')
    end_idx,end=ends[0]
    valid_idx,v=single(rows,'0x8094330',r0=0,r6=0)
    slot_idx,sl=single(rows,'0x809435c',r0=1,r6=0)
    move_idx,m=single(rows,'0x8094374',r0=157,r6=0)
    targ_idx,tar=single(rows,'0x8094380',r2=1,r6=0)
    require(stage < guard < branch < auto < em_idx < rep_idx < end_idx < check_idx < valid_idx < slot_idx < move_idx < targ_idx,
            'native staging/auto/acceptance is not in exact original order')
    require(rep.get('reply_header')==0x0a20 and rep.get('reply_payload')==257 and rep.get('reply_valid')==1,
            'original six-byte player reply differs from automatic move')
    require((end.get('pending',1)&1)==0,'actor0 pending bit never cleared')
    require(em.get('auto_slot')==1 and sl.get('auto_slot')==1 and rep.get('auto_slot')==1,
            'selected native auto slot invalid')
    require(hits(rows,'0x806bd80',r0=1,r2=10),'original foe response absent from independent process')
    require(len(hits(rows,'0x806bd80',r0=0))==1,
            'duplicate player emitter or unsupported extra native submission')
    require(not any(r['pc']=='0x806449c' and i<targ_idx for i,r in enumerate(rows)),
            'manual move chooser was active before purported automatic commit')
    return {'mode':'positive fixture-lab only','slot':1,'move':157,'accepted':True,'auto_in_rom':True}

def verify_negative(j):
    rows=check_common(j,False)
    gate_idx,_=single(rows,'0x9f2d000')
    result_idx,_=single(rows,'0x9f20022',r0=0)
    require(gate_idx<result_idx,'negative guard observation reordered')
    require(len(hits(rows,'0x8065eb4'))==0,'denied request reached original native auto path')
    require(len(hits(rows,'0x806bd80',r0=0))==0,'denied request emitted player move')
    require(len(hits(rows,'0x806449c'))>=1,'denied request did not reach original manual chooser')
    require(len(hits(rows,'0x806bd80',r0=1,r2=10))>=1,'opponent original AI path absent')
    require(j.get('lab_native_in_rom_auto_acceptance',0)==0,'negative trace claims success')
    return {'mode':'negative request-mismatch','auto_in_rom':False,'manual_fallback':True}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--mode',choices=('positive','negative'),required=True)
    a=parser.parse_args()
    j=json.loads(a.report.read_text())
    out=verify_positive(j) if a.mode=='positive' else verify_negative(j)
    print('PASS',json.dumps(out,sort_keys=True))