#!/usr/bin/env python3
"""Strict exact-ROM *same replay* actor0/PP/Main callback evidence triage.

Only privately replayed, byte-pinned original ROM evidence can be considered.
An observed original reply, PP writer, Main clear, or callback is never an
engine outcome decision, dynamic legality, cancellation or production proof.
"""
import argparse
import hashlib
import json
from pathlib import Path

CURRENT = "7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
MODIFIED = "4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
SAVE = "8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4"
SCHEMA = "sg-exact-original-joint-player-terminal-v1"
MAIN = 0x03005A0D
PP = 0x02001EF1
CB1 = 0x030055D4
CB2 = CB1 + 4
PHASE = CB1 + 0x438
WRITER = 0x0809E6BA
# Exact original CPU markers; their instruction addresses, not inferred offsets.
MARKERS = {1:0x0806BD80,2:0x0806B370,3:0x0806261C,
           4:0x08094330,5:0x0809435C,6:0x08094374,
           7:0x08094380,8:0x0806449C}
ADDRESS = {10:MAIN,11:CB1,12:CB2,13:PHASE}
MOVES = (325,157,92,269) # Only historical user's first wild test party.
TOP = {"schema","current_sha256","modified_sha256","save_sha256",
       "new_hook_installed","guest_writes","host_move_menu_inputs",
       "status","start_frame","end_frame","window_frames","steps",
       "initial_main","final_main","initial_cb1","final_cb1",
       "initial_cb2","final_cb2","initial_pp","final_pp","events"}
FIELDS = {"frame","step","pc","opcode","stage","kind","address",
          "before","after","slot","r0","r1","r2","r3","r4",
          "flags","battlers","pending","inbattle","callback1","callback2"}

def require(ok,why):
    if not ok: raise ValueError(why)

def u32(value):return type(value) is int and 0<=value<=0xFFFFFFFF

def u32seq(v,n):return type(v) is list and len(v)==n and all(u32(x) for x in v)

def audit(d):
    require(type(d) is dict and set(d)==TOP and d["schema"]==SCHEMA,
            "unrecognized one-run CPU schema")
    require(d["current_sha256"]==CURRENT and d["modified_sha256"]==MODIFIED
            and d["save_sha256"]==SAVE,"wrong private ROM/save identity labels")
    require(d["new_hook_installed"] is False and type(d["guest_writes"]) is int
            and d["guest_writes"]==0 and type(d["host_move_menu_inputs"]) is int
            and d["host_move_menu_inputs"]==0,"not the unmodified no-input replay")
    require(type(d["status"]) is int and d["status"]==1,
            "trace incomplete, invalid, overfull or time-rolled-back")
    require(all(u32(d[k]) for k in ("start_frame","end_frame","window_frames",
             "steps","initial_main","final_main","initial_cb1","final_cb1",
             "initial_cb2","final_cb2")),"invalid run metadata")
    require(0<d["window_frames"]<=10000 and
            d["start_frame"]+d["window_frames"]<=d["end_frame"] and
            0<d["steps"]<=0xFFFFFFFF,"unfinished frame/CPU trace")
    require(d["initial_main"]<=255 and d["final_main"]<=255,
            "invalid original Main byte")
    require(u32seq(d["initial_pp"],4) and u32seq(d["final_pp"],4) and
            all(x<=255 for x in d["initial_pp"]+d["final_pp"]),
            "invalid original own PP byte snapshot")
    rows=d["events"]
    require(type(rows) is list and len(rows)<=1024,"event overflow or malformed CPU trace")
    old_main=d["initial_main"]&2
    cb1=d["initial_cb1"]
    cb2=d["initial_cb2"]
    pp=d["initial_pp"][:]
    last_step=-1
    last_stage=-1
    last_frame=d["start_frame"]
    emits=[]
    active=None
    writer_count=0
    non_writer_changes=0
    clear_edges=[]
    callbacks=[]
    manual=0
    for i,e in enumerate(rows):
        require(type(e) is dict and set(e)==FIELDS and
                all(u32(e[k]) for k in FIELDS),"forged or malformed guest CPU event")
        require(e["kind"] in range(1,14) and e["stage"] in (0,1)
                and d["start_frame"]<=e["frame"]<d["end_frame"]
                and e["step"]<d["steps"] and e["frame"]>=last_frame,
                "invalid original guest event chronology")
        require(e["step"]>last_step or
                (e["step"]==last_step and e["stage"]>=last_stage and
                 (last_stage==1 or e["stage"]==1)),
                "reordered event step or pre/post stage")
        require(e["pc"]==0 and e["opcode"]==0 or
                (0x08000000<=e["pc"]<=0x09FFFFFE and e["pc"]%2==0
                 and e["opcode"]<=0xFFFF),"unknown original ROM PC or opcode")
        require(e["flags"] in (0,4) and e["battlers"] in (0,2)
                and e["inbattle"]<=255,"non-wild/native context mismatch")
        kind=e["kind"]
        if kind in MARKERS:
            require(e["stage"]==0 and e["pc"]==MARKERS[kind] and
                    e["address"]==0 and e["slot"]==255,
                    "original action marker CPU identity mismatch")
            if kind==8:
                manual+=1
            elif kind==1:
                # Never promote a stale original actor0 emitter AFTER the
                # recorded Main.inBattle clear; flags/pending can remain stale.
                require(old_main==2,
                        "actor0 emission after original Main.inBattle cleared")
                require(e["r0"]==0 and e["r2"]==10 and e["r3"]>>8==1
                        and e["r3"]&255<4 and (e["inbattle"]&2)
                        and e["flags"]==4 and e["battlers"]==2,"not original player move/target action")
                if active is not None:
                    emits.append(active)
                active={"slot":e["r3"]&255,"frame":e["frame"],"marker_order":0,
                        "pp_writes":0,"writer_frames":[]}
            elif active is not None:
                nxt=active["marker_order"]+2
                # Expected 2 reply, 3 complete, 4 validate, 5 slot,
                # 6 move, 7 target. No automatic PP attribution if incomplete.
                if kind==nxt and (e["inbattle"]&2) and e["flags"]==4:
                    if kind==4:require(e["r0"]==0,"validator owner mismatch")
                    if kind==5:require(e["r0"]==active["slot"],"slot mismatch")
                    if kind==6:require(e["r0"]==MOVES[active["slot"]],"move mismatch")
                    if kind==7:require(e["r2"]==1,"target mismatch")
                    active["marker_order"]+=1
                elif kind in range(2,8):
                    # PC markers may belong to another actor/engine path.
                    # No promotion or positive player ownership in that case.
                    active["marker_order"]=-100
        else:
            require(e["stage"]==1,"native field mutation at wrong CPU stage")
            address=PP+e["slot"] if kind==9 and e["slot"]<4 else ADDRESS.get(kind)
            require(address is not None and e["address"]==address and
                    e["before"]!=e["after"],"unmatched native RAM write")
            if kind==9:
                slot=e["slot"]
                require(slot<4 and e["before"]<=255 and e["after"]<=255
                        and pp[slot]==e["before"],"invalid or missing PP byte mutation")
                pp[slot]=e["after"]
                authentic=(e["pc"]==WRITER and e["r1"]==address and
                           e["before"]==e["after"]+1)
                if authentic:
                    # A PP mutation at the real writer PC must not be
                    # attributed to an active player move after Main exit,
                    # even when stale battle flags still claim wild-single.
                    require(old_main==2 and (e["inbattle"]&2) and
                            e["flags"]==4 and e["battlers"]==2,
                            "original PP writer outside active Main wild-single")
                    writer_count+=1
                    if (active is not None and active["marker_order"]==6 and
                            active["slot"]==slot and (e["inbattle"]&2) and
                            e["flags"]==4):
                        active["pp_writes"]+=1
                        active["writer_frames"].append(e["frame"])
                else:non_writer_changes+=1
            elif kind==10:
                require(e["before"]<=255 and e["after"]<=255 and
                        (e["before"]&2)==old_main and
                        ((e["before"]^e["after"])&2),
                        "not the original gMain.inBattle bit edge")
                old_main=e["after"]&2
                if not old_main:clear_edges.append((e["step"],e["pc"]))
            elif kind==11:
                require(e["before"]==cb1,"missing or repeated callback1 mutation")
                cb1=e["after"]
                callbacks.append((e["step"],e["pc"],1))
            elif kind==12:
                require(e["before"]==cb2,"missing or repeated callback2 mutation")
                cb2=e["after"]
                callbacks.append((e["step"],e["pc"],2))
            elif kind==13:
                require(e["before"]<=255 and e["after"]<=255,
                        "invalid Main phase transition")
        last_step=e["step"]
        last_stage=e["stage"]
        last_frame=e["frame"]
    if active is not None:emits.append(active)
    require(old_main==(d["final_main"]&2) and cb1==d["final_cb1"] and
            cb2==d["final_cb2"] and pp==d["final_pp"],
            "missing original Main/callback/PP mutations from same replay")
    require(manual==0,"manual move-menu entered; not unattended automatic replay")
    require(all(x["pp_writes"]<=1 for x in emits),"duplicate writer in one move candidate")
    # Counts are descriptive and do not claim execution, outcome, or safety.
    joined=sum(1 for s,_ in clear_edges if any(c[0]>s for c in callbacks))
    return {
        "source_scope":"ONE exact original modified-ROM replay; CPU markers/PP/Main only",
        "original_actor0_emitter_candidates":len(emits),
        "full_marker_sequence_candidates":sum(e["marker_order"]==6 for e in emits),
        "original_native_pp_writer_events":writer_count,
        "attributed_original_pp_writer_candidates":sum(e["pp_writes"] for e in emits),
        "original_emissions_without_attributed_pp_writer":sum(e["pp_writes"]==0 for e in emits),
        "non_writer_pp_byte_mutations":non_writer_changes,
        "main_clear_edges":len(clear_edges),
        "main_clear_precedes_later_callback_in_same_run":joined,
        "main_clear_cpu_pc_candidates":[f"0x{pc:08X}" if pc else "UNKNOWN" for _,pc in clear_edges],
        "callback_mutations":len(callbacks),
        "original_outcome_writer_pc_certified":False,
        "victory_loss_or_cancellation_certified":False,
        "full_native_terminal_certified":False,
        "unmatched_pp_cause_certified":False,
        "dynamic_move_legality_and_one_use_certified":False,
        "manual_fallback_certified":False,
        "formal_native_gameplay_acceptance":0,
        "production_promotion_authorized":False,
    }

def digest(b):return hashlib.sha256(b).hexdigest()

def attest(raw,current,modified,save):
    require(len(current)==len(modified)==33554432 and len(save)==131072,
            "missing original game/save bytes")
    require(digest(current)==CURRENT and digest(modified)==MODIFIED and
            digest(save)==SAVE,"private immutable input hashes do not match")
    data=json.loads(raw.decode("utf-8"))
    result=audit(data)
    for e in data["events"]:
        if not e["pc"]:continue
        off=e["pc"]-0x08000000
        require(int.from_bytes(modified[off:off+2],"little")==e["opcode"],
                "original modified-ROM opcode mismatch")
    result["private_cpu_trace_sha256"]=digest(raw)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("trace","current","modified","save"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    paths=[getattr(a,n) for n in ("trace","current","modified","save")]
    for f in paths:
        if not f.is_file() or f.is_symlink():p.error("private regular non-symlink inputs required")
    try:ans=attest(*(f.read_bytes() for f in paths))
    except (ValueError,TypeError,KeyError,UnicodeError) as e:p.error(str(e))
    print(json.dumps(ans,sort_keys=True,indent=2))

if __name__=="__main__":main()
