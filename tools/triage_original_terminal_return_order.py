#!/usr/bin/env python3
"""Strict PUBLIC original outcome-to-overworld sequence candidate triage.

No guessed RAM byte is gBattleOutcome; no CPU trace is original-ROM authenticated
by this standalone tool. All reported orders are UNVERIFIED and non-promoting.
"""
import argparse
import json
from pathlib import Path
from verify_exact_outcome_pp_edges import (
    audit, MAIN, observed_thumb_strb_address,
    observed_thumb_strb_source_byte, observed_thumb_str_word_store,
    observed_thumb_stmia_word_at,
)

def candidate_result_writer(e, address):
    if not address or e["kind"]!=1 or e["address"]!=address or (
        e["before"]!=0 or e["after"]==0
    ):
        return False
    regs=tuple(e["r"+str(i)] for i in range(8))
    return (observed_thumb_strb_address(e["opcode"],regs)==address and
            observed_thumb_strb_source_byte(e["opcode"],regs)==e["after"])

def candidate_callback_word_writer(e):
    if e["kind"] not in (3,4) or e["address"]!=MAIN+4*(e["kind"]-3):
        return False
    # The source-LAB only supports Thumb callback pointers in cart ROM.
    # RAM callbacks or callbacks of unknown instruction origin are left
    # UNATTRIBUTED, not guessed from watched pointer changes.
    ptr=e["after"]
    if not (0x08000001<=ptr<=0x09FFFFFF and ptr&1):
        return False
    regs=tuple(e["r"+str(i)] for i in range(8))
    return (observed_thumb_str_word_store(e["opcode"],regs)==
            (e["address"],ptr) or
            observed_thumb_stmia_word_at(
                e["opcode"],regs,e["address"])==ptr)

def triage(raw):
    source=audit(raw) # Reuse full exact-schema and same-step CPU assertions.
    result_address=raw["candidate_outcome_byte_address"]
    result_writes=[]
    exits=[]
    active=None
    for e in raw["events"]:
        kind=e["kind"]
        if kind==1 and candidate_result_writer(e,result_address):
            result_writes.append(e["step"])
        if kind==2:
            if e["after"]==0 and e["before"]!=0:
                if active:
                    active["closed_by"]="later_main_transition"
                prior=[s for s in result_writes if s<e["step"]]
                active={"main_clear_step":e["step"],"prior_result_steps":prior,
                        "callback1":[],"callback2":[],
                        "closed_by":"end_of_observation"}
                exits.append(active)
                result_writes=[]
            elif e["after"]!=0:
                if active:
                    active["closed_by"]="battle_resumed"
                    active=None
                result_writes=[]
        elif kind==8 and active is not None:
            active["closed_by"]="manual_menu"
            active=None
        elif kind in (3,4) and active is not None:
            key="callback1" if kind==3 else "callback2"
            active[key].append({
                "step":e["step"],
                "word_writer_candidate_unverified":candidate_callback_word_writer(e)
            })
    ordered=0
    for seg in exits:
        c1,c2=seg["callback1"],seg["callback2"]
        valid=(seg["closed_by"]=="end_of_observation" and
               len(seg["prior_result_steps"])==1 and
               len(c1)==len(c2)==1 and
               c1[0]["word_writer_candidate_unverified"] and
               c2[0]["word_writer_candidate_unverified"] and
               seg["prior_result_steps"][0]<seg["main_clear_step"]<
               c1[0]["step"]<c2[0]["step"])
        seg["ordered_strict_candidate_unverified"]=bool(valid)
        ordered+=bool(valid)
    return {
        "schema":"sg-public-original-terminal-return-order-v1",
        "main_inbattle_clear_segments_unverified":len(exits),
        "ordered_result_main_callback1_callback2_sequences_unverified":ordered,
        "missing_ambiguous_or_out_of_order_segments":len(exits)-ordered,
        "prior_result_byte_writers_are_unverified":source[
            "candidate_outcome_strb_writer_matches_unverified"],
        "callback_word_str_writers_are_unverified":source[
            "original_callback_word_str_writer_matches_unverified"],
        "callback_stmia_writers_are_unverified":source[
            "original_callback_stmia_word_matches_unverified"],
        "segments":exits,
        "original_battle_outcome_address_identified":False,
        "original_outcome_decision_pc_certified":False,
        "original_overworld_callback_return_certified":False,
        "authentic_actor0_one_use_request_certified":False,
        "full_original_native_terminal_certified":False,
        "original_gameplay_acceptance_scenarios":0,
        "production_authorized":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("public_event_json",type=Path)
    args=p.parse_args()
    print(json.dumps(triage(json.loads(args.public_event_json.read_text())),
                     sort_keys=True,indent=2))
if __name__=="__main__":
    main()
