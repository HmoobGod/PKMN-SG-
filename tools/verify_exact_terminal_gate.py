#!/usr/bin/env python3
"""Exact-ROM battle-terminal safety barrier.

No amount of idle frames, zero pending, or missing auto markers alone proves a
battle won, cancelled, exited, or returned to overworld. Original engine
terminal PC and callback identity MUST be separately independently established.
This source-only verifier cannot authorize a new hybrid hook or ROM promotion.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROM_SHA="4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
SAVE_SHA="8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4"
SCHEMA="sg-exact-modified-terminal-observation-v1"

def require(value,message):
    if not value:raise ValueError(message)

def audit(r):
    require(isinstance(r,dict) and r.get("schema")==SCHEMA,"unrecognized terminal trace")
    require(r.get("rom_sha256")==ROM_SHA and r.get("save_sha256")==SAVE_SHA,
            "exact input identity mismatch")
    require(r.get("host_move_menu_inputs")==0 and r.get("guest_writes")==0
            and r.get("new_hook_installed") is False,"not a passive no-input original-ROM witness")
    rows=r.get("samples")
    require(isinstance(rows,list) and 4<=len(rows)<=32,"missing/beyond-budget sample windows")
    for i,row in enumerate(rows):
        require(isinstance(row,dict)
                and set(row)=={"frame","flags","battlers","pending","events","auto","pp","manual"}
                and type(row["frame"]) is int
                and type(row["flags"]) is int
                and type(row["battlers"]) is int
                and type(row["pending"]) is int
                and type(row["events"]) is int and row["events"]>=0
                and type(row["auto"]) is int and row["auto"]>=0
                and type(row["manual"]) is int and row["manual"]>=0
                and isinstance(row["pp"],list) and len(row["pp"])==4
                and all(type(n) is int and 0<=n<=255 for n in row["pp"])
                and row["manual"]==0,
                "inconsistent sample, manual input or private bytes")
        if i:
            require(row["frame"]-rows[i-1]["frame"]==350,
                    "gapped/overlapping frame windows")
    first,last=rows[0],rows[-1]
    require(first["flags"]==4 and first["battlers"]==2,"not a witnessed wild-single start")
    require(all(row["flags"] in (0,4) and row["battlers"] in (0,2) for row in rows),
            "unexpected battle engine state transition")
    quiet=0
    for x in reversed(rows):
        if x["events"]!=0 or x["auto"]!=0:
            break
        quiet+=1
    require(quiet>=3,"insufficient no-event tail; cannot assess")
    unresolved=(last["flags"]==4 and last["battlers"]==2 and last["pending"]==0)
    # A cleared flag alone still does NOT show a trusted original battle
    # terminal instruction and original overworld callback restoration.
    return {
        "source":"exact modified ROM, private read-only emulator observations",
        "input_sha256":ROM_SHA,
        "consecutive_quiet_windows":quiet,
        "quiet_frames_at_least":quiet*350,
        "battle_flags_at_end":last["flags"],
        "battlers_at_end":last["battlers"],
        "pending_at_end":last["pending"],
        "no_input_original_battle_state_still_active":unresolved,
        "terminal_outcome_original_cpu_witness":False,
        "overworld_callback_original_cpu_witness":False,
        "terminal_or_cancellation_certified":False,
        "whole_battle_playable_certified":False,
        "production_promotion_authorized":False,
        "next_probe":"locate authentic terminal instruction/outcome and callback, then replay",
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--private-summary",required=True,type=Path)
    args=ap.parse_args()
    p=args.private_summary
    if not p.is_file() or p.is_symlink():ap.error("regular private summary required")
    try:answer=audit(json.loads(p.read_text(encoding="utf-8")))
    except (ValueError,KeyError,TypeError) as e:ap.error(str(e))
    print(json.dumps(answer,sort_keys=True,indent=2))
if __name__=="__main__":main()
