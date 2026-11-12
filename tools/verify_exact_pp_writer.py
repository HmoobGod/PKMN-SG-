#!/usr/bin/env python3
"""Read-only exact native PP-write attribution; never a gameplay certificate.

A native move reply is not itself evidence of a PP-consuming attack.
Original 0x0809E6BA writes are differentiated from unrelated writes to the
same bytes (including 0x081FB8DA and original bulk-copy routines).
"""
import argparse
import hashlib
import json
from pathlib import Path

CURRENT_SHA="7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
MODIFIED_SHA="4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
SAVE_SHA="8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4"
PRIVATE_TRACE_SHA="3b8c9d582f09244435643017f0821dc6f84178216ae98e6636f30dfc63ec4aed"
WRITER_WINDOW_SHA="84ffa68c024412568ce64fdac3719cd460c40a55caf07a5549bd150a7fe50923"
WRITER="0x809e6ba"
OWN_PP=0x02001EF1
ALLOWED={"frame","pc","kind","slot","before","after","r0","r1","r2","r3","pending","flags"}
MOVE_IDS={0:325,1:157,2:92,3:269}

def require(value,msg):
    if not value: raise ValueError(msg)

def sha(data):return hashlib.sha256(data).hexdigest()

def summarize(events):
    require(isinstance(events,list) and 5<=len(events)<=500,"bounded CPU witness list required")
    for e in events:
        require(isinstance(e,dict) and set(e)==ALLOWED,"unrecognized or private CPU fields")
        require(all(type(e[k]) is int for k in ALLOWED-{"pc"})
                and isinstance(e["pc"],str) and e["pc"].startswith("0x")
                and e["flags"]==4,"untrusted event types or non-wild engine context")
    require(all(a["frame"]<=b["frame"] for a,b in zip(events,events[1:])),
            "guest instruction chronology reversed")
    require(not any(e["kind"]==7 for e in events),"manual move-menu visited")
    moves=[(i,e) for i,e in enumerate(events) if e["kind"]==1]
    require(bool(moves),"no native player automatic move emitted")
    debits=[]
    for n,(idx,em) in enumerate(moves):
        require(em["pc"]=="0x806bd80" and em["r0"]==0
                and em["r2"]==10 and 0<=em["r3"]<=0x3FF
                and (em["r3"]>>8)==1 and (em["r3"]&255)<4,
                "wrong actor, action, move slot or target")
        slot=em["r3"]&255
        end=moves[n+1][0] if n+1<len(moves) else len(events)
        segment=events[idx+1:end]
        def located(kind,predicate=lambda x:True):
            return [(j,q) for j,q in enumerate(segment)
                    if q["kind"]==kind and predicate(q)]
        reply=located(2,lambda x:x["pc"]=="0x806b370" and x["r0"]==0
                      and x["r1"]==1 and x["r3"]==6)
        complete=located(8,lambda x:x["pc"]=="0x806261c" and x["r0"]==0)
        valid=located(3,lambda x:x["pc"]=="0x8094330" and x["r0"]==0)
        own_slot=located(4,lambda x:x["pc"]=="0x809435c" and x["r0"]==slot)
        own_move=located(5,lambda x:x["pc"]=="0x8094374" and x["r0"]==MOVE_IDS[slot])
        target=located(6,lambda x:x["pc"]=="0x8094380" and x["r2"]==1)
        require(reply and complete and valid and own_slot and own_move and target,
                "original reply/complete/commit sequence incomplete")
        require(reply[0][0]<complete[0][0]<valid[0][0]<
                own_slot[0][0]<own_move[0][0]<target[0][0],
                "original engine action order invalid")
        writes=located(9,lambda x:x["pc"]==WRITER)
        require(len(writes)<=1,"duplicate native PP debit in one move epoch")
        if writes:
            j,w=writes[0]
            require(j>target[0][0] and w["slot"]==slot
                    and w["r1"]==OWN_PP+slot
                    and w["before"]-w["after"]==1
                    and 0<=w["after"]<=254
                    and em["frame"]<=w["frame"]<=em["frame"]+120,
                    "native PP write not owned by legal-looking player move")
            debits.append(dict(frame=w["frame"],slot=slot,writer=WRITER,
                               old_pp=w["before"],new_pp=w["after"]))
    allwrites=[e for e in events if e["kind"]==9]
    anchored=[e for e in allwrites if e["pc"]==WRITER]
    require(len(anchored)==len(debits),"unclaimed exact native PP writer")
    return {
        "native_player_move_submissions":len(moves),
        "original_native_pp_debit_events":len(debits),
        "source_copy_or_other_byte_changes_not_pp_certified":len(allwrites)-len(debits),
        "native_write_frames":[w["frame"] for w in debits],
        "unattributed_submissions":len(moves)-len(debits),
        "formal_gameplay_acceptance":0,
        "battle_terminal_certified":False,
        "dynamic_move_legality_certified":False,
        "engine_request_epoch_certified":False,
        "new_native_hook_installed":False,
        "production_promotion_authorized":False,
    }

def attest_exact(trace_bytes,current,modified,save):
    require(sha(trace_bytes)==PRIVATE_TRACE_SHA,"private CPU trace SHA mismatch")
    require(len(current)==len(modified)==33554432
            and len(save)==131072,"exact original ROM/save sizes required")
    require(sha(current)==CURRENT_SHA and sha(modified)==MODIFIED_SHA
            and sha(save)==SAVE_SHA,"protected Current / modified / save identity mismatch")
    pc=0x0809E6BA-0x08000000
    a=current[pc-16:pc+48];b=modified[pc-16:pc+48]
    require(a==b and sha(a)==WRITER_WINDOW_SHA,
            "original exact PP-write native Thumb instructions changed")
    events=json.loads(trace_bytes.decode("utf-8"))
    result=summarize(events)
    require(len(events)==99 and result["native_player_move_submissions"]==2
            and result["original_native_pp_debit_events"]==2
            and result["source_copy_or_other_byte_changes_not_pp_certified"]==35
            and result["native_write_frames"]==[5023,5195],
            "private original CPU fixture lineage disagrees")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("private_trace","current","modified","save"):
        p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    for name in ("private_trace","current","modified","save"):
        f=getattr(a,name)
        if not f.is_file() or f.is_symlink():p.error("regular non-symlink private inputs required")
    try:
        result=attest_exact(a.private_trace.read_bytes(),a.current.read_bytes(),
                            a.modified.read_bytes(),a.save.read_bytes())
    except (ValueError,UnicodeError,TypeError,KeyError) as e:p.error(str(e))
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":main()
