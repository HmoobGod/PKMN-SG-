#!/usr/bin/env python3
"""Private exact-ROM native Main callback handoff attestation, source-only.

Original callback handoff and inBattle clearance are NOT a certified
victory/result outcome. Never authorize Current ROM/gameplay promotion.
"""
import argparse
import hashlib
import json
from pathlib import Path

CURRENT="7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
MODIFIED="4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
SAVE="8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4"
PRIVATE_TRACE="58c560303a2013c0fbfd250539bcf174d8275b56c71dad9019b8bfa08f15660a"
MAIN=0x030055D4
WINDOWS={0x0808E33C:"e92a2c689b0dc81c18664509bd52dfb00737b76d6c5b268ba952261301c21281",
         0x081AED58:"87a078714223450057d306b127deea90d6d8ef37173973216c103f72f95dc333"}
EXPECTED=[
 (3984,0x0808E33C,1,0x0808CBDD,0x081C7589),
 (3987,0x081AED58,2,0x0808F225,0x080C4265),
 (3988,0x081AED58,2,0x080C4265,0x081CA4B1),
 (3989,0x081AED58,2,0x081CA4B1,0x081C7F65),
 (3993,0x081C8060,4,0,1),
 (3996,0x081C7FAE,4,1,2),
 (3997,0x081C7FD4,4,2,3),
 (3998,0x081AED58,2,0x081C7F65,0x081C9FC5),
 (3998,0x081AED5A,4,3,0),
]
FIELDS={"frame","pc","kind","before","after","r0","r1","r2","r3","r4",
        "r5","r6","r7","flags","battlers","pending","main_state","inbattle"}
def deny(ok,reason):
    if not ok:raise ValueError(reason)
def sha(x):return hashlib.sha256(x).hexdigest()
def audit(events):
    deny(isinstance(events,list) and len(events)==9,"not the original nine-step callback transfer")
    for i,(e,expected) in enumerate(zip(events,EXPECTED)):
        deny(isinstance(e,dict) and set(e)==FIELDS,"untrusted original CPU event shape")
        deny(all(type(e[k]) is int for k in FIELDS),"untrusted CPU register/PC type")
        deny((e["frame"],e["pc"],e["kind"],e["before"],e["after"])==expected,
             "wrong original native instruction/callback chain at "+str(i))
        deny(e["flags"]==4 and e["battlers"]==2 and e["pending"]==0
             and e["inbattle"]==0,"original player wild-to-Main state mismatch")
        if e["kind"]==1:deny(e["r4"]==MAIN and e["r2"]==e["after"],
                           "callback1 original Main base / source value mismatch")
        if e["kind"]==2:deny(e["r3"]==MAIN and e["r0"]==e["after"],
                           "callback2 original setter/Main destination mismatch")
        if e["kind"]==4:deny(e["main_state"]==e["after"],
                           "Main phase reset/milestone not committed")
    return {
        "scope":"ORIGINAL exact modified wild-to-Main callback CPU evidence only",
        "exact_modified_rom_sha256":MODIFIED,
        "main_base":f"0x{MAIN:08X}",
        "callback2_ram_address":f"0x{MAIN+4:08X}",
        "inbattle_field_address":f"0x{MAIN+0x439:08X}",
        "native_callback1_store":"0x0808E33C",
        "native_callback2_store":"0x081AED58",
        "original_callback2_final":"0x081C9FC5",
        "main_inbattle_cleared_while_old_flags4":True,
        "original_callback_cpu_handoff_witness":True,
        "prior_battle_outcome_decision_certified":False,
        "full_unattended_battle_result_certified":False,
        "dynamic_legality_certified":False,
        "new_native_hook_installed":False,
        "formal_gameplay_acceptance":0,
        "production_promotion_authorized":False,
    }
def attest(private_bytes,current,modified,save):
    deny(sha(private_bytes)==PRIVATE_TRACE,"private original CPU trace not attested")
    deny(len(current)==len(modified)==33554432 and len(save)==131072,
         "wrong protected game/save size")
    deny(sha(current)==CURRENT and sha(modified)==MODIFIED and sha(save)==SAVE,
         "wrong protected / modified game/save identity")
    for pc,expected in WINDOWS.items():
        offset=pc-0x08000000
        a,b=current[offset-16:offset+48],modified[offset-16:offset+48]
        deny(a==b and sha(a)==expected,"original native callback Thumb parity missing")
    return audit(json.loads(private_bytes.decode("utf-8")))
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("private_trace","current","modified","save"):
        p.add_argument("--"+n.replace("_","-"),type=Path,required=True)
    args=p.parse_args()
    for n in ("private_trace","current","modified","save"):
        f=getattr(args,n)
        if not f.is_file() or f.is_symlink():p.error("existing regular private inputs required")
    try:
        result=attest(args.private_trace.read_bytes(),args.current.read_bytes(),
                      args.modified.read_bytes(),args.save.read_bytes())
    except (TypeError,ValueError,UnicodeError,KeyError) as e:p.error(str(e))
    print(json.dumps(result,sort_keys=True,indent=2))
if __name__=="__main__":main()
