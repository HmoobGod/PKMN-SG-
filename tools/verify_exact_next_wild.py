#!/usr/bin/env python3
"""Strict exact-ROM field-to-next-wild witness, NOT a prior outcome certificate.

The first auto wild's quiet flags remain 4. Directional overworld inputs
later reach the original second wild constructor. Observed CPU writes
4 -> 0 -> 4 happen in the NEW encounter setup; they are NOT sufficient
to identify the preceding battle's native outcome/return callback PC.
"""
import argparse
import hashlib
import json
from pathlib import Path

CURRENT_SHA="7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
MODIFIED_SHA="4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
SAVE_SHA="8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4"
PRIVATE_TRACE_SHA="6776c99fb4509873da12e12af0a114d2409deb6edce7f015431cf465ab2cdd33"
WINDOWS={
  0x080C501E:"b10cb1738322db3aff54fa02c2e47c626628441fb23d63b5c4012f15d79ca392",
  0x0808D71A:"2ccced6028b620b8ca2685a911c06fe6c41079e92d6c624f2e03efdd8fdcbb92",
  0x0806AD46:"5bbd5d0fcdb2c0b458258cee28f93709e70ac73746a20f651f24d26ef847df34"
}
EDGE_FIELDS={"frame","pc","before","after","r0","r1","r2","r3","kind0","kind1"}
ROW_FIELDS={"trial","step","direction","frame","result","flags","pc","flag_changes"}
DIRECTIONS=("right","down","left","up")
def must(ok,msg):
    if not ok:raise ValueError(msg)
def sha(x):return hashlib.sha256(x).hexdigest()

def summarize(rows):
    must(isinstance(rows,list) and len(rows)==14,"expected bounded original field route")
    flat=[]
    for i,r in enumerate(rows):
        must(isinstance(r,dict) and set(r)==ROW_FIELDS,"unsupported/private route fields")
        must(type(r["trial"]) is int and r["trial"]==0 and type(r["step"]) is int
             and r["step"]==i and r["direction"]==DIRECTIONS[i%4],
             "manual battle/menu input or wrong field direction sequence")
        must(type(r["frame"]) is int and type(r["flags"]) is int
             and isinstance(r["pc"],str)
             and type(r["result"]) is int and isinstance(r["flag_changes"],list),
             "malformed CPU/route metadata")
        must(r["frame"]==(6755+260*i if i<13 else 9994),
             "unexpected guest emulator route timing")
        must(r["flags"]==4,"missing exact original 4-flag encounter context")
        must(r["result"]==(1 if i<13 else 2)
             and r["pc"]==("0x188" if i<13 else "0x806ad48"),
             "no authenticated original next-wild constructor")
        if i<13:must(not r["flag_changes"],"unexpected earlier flag mutation")
        for e in r["flag_changes"]:
            must(isinstance(e,dict) and set(e)==EDGE_FIELDS,
                 "untrusted/extra original CPU payload")
            must(all(type(e[k]) is int for k in EDGE_FIELDS-{"pc"})
                 and isinstance(e["pc"],str),"malformed native PC/register witness")
            flat.append(e)
    must(len(flat)==2,"original native next-encounter writes not unique")
    a,b=flat
    must(a["frame"]==9957 and a["pc"]=="0x80c501e" and
         a["before"]==4 and a["after"]==0 and
         b["frame"]==9993 and b["pc"]=="0x808d71a" and
         b["before"]==0 and b["after"]==4 and
         a["kind0"]==b["kind0"]==0 and a["kind1"]==b["kind1"]==0,
         "original native 4->0->4 guest PC order or owner mismatch")
    must(b["frame"]<rows[-1]["frame"],"new flags must precede original constructor")
    return {
        "private_replay_scope":"after earlier no-button original wild",
        "ordinary_field_directional_inputs_after_quiet":14,
        "move_menu_inputs_after_quiet":0,
        "battle_flags_before_movement":4,
        "observed_new_encounter_reset_pc":"0x080C501E",
        "observed_new_encounter_set_pc":"0x0808D71A",
        "new_original_wild_constructor_pc":"0x0806AD46",
        "new_original_wild_constructor_frame":9994,
        "original_field_to_second_wild_roundtrip_observed":True,
        "previous_battle_outcome_writer_pc_certified":False,
        "previous_overworld_main_callback_pc_certified":False,
        "formal_gameplay_acceptance":0,
        "new_hybrid_hook_installed":False,
        "production_promotion_authorized":False,
    }

def attest(trace,current,modified,save):
    must(sha(trace)==PRIVATE_TRACE_SHA,"private field replay trace SHA mismatch")
    must(len(current)==len(modified)==33554432 and len(save)==131072,
         "incorrect game or save sizes")
    must(sha(current)==CURRENT_SHA and sha(modified)==MODIFIED_SHA
         and sha(save)==SAVE_SHA,"exact input ROM/save lineage mismatch")
    for pc,expected in WINDOWS.items():
        i=pc-0x08000000
        a=current[i-16:i+48];b=modified[i-16:i+48]
        must(a==b and sha(a)==expected,
             "original native constructor or flag-store Thumb parity mismatch")
    return summarize(json.loads(trace.decode("utf-8")))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("private_trace","current","modified","save"):
        p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    args=p.parse_args()
    for name in ("private_trace","current","modified","save"):
        f=getattr(args,name)
        if not f.is_file() or f.is_symlink():p.error("regular private input required")
    try:
        out=attest(args.private_trace.read_bytes(),args.current.read_bytes(),
                   args.modified.read_bytes(),args.save.read_bytes())
    except (ValueError,UnicodeError,TypeError,KeyError) as e:p.error(str(e))
    print(json.dumps(out,sort_keys=True,indent=2))
if __name__=="__main__":main()
