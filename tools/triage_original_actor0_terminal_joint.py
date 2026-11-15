#!/usr/bin/env python3
"""PUBLIC original actor0 marker->PP->candidate outcome->Main return triage.

A complete synthetic candidate does NOT certify actual original gameplay,
the outcome address, move/target legality, engine-issued requests, PP
cancellation or executing a real overworld callback.
"""
import argparse
import json
from pathlib import Path

from triage_original_actor0_marker_chain import evaluate as actor_chain
from verify_exact_outcome_pp_edges import (
    MAIN, observed_thumb_strb_address, observed_thumb_strb_source_byte,
    observed_thumb_str_word_store,
)
from decode_original_stmia_callback_word import original_thumb_stmia_word_at

def registers(event):
    return tuple(event["r"+str(i)] for i in range(8))

def result_byte_store(e, address):
    if not address or e["kind"]!=1 or e["address"]!=address or (
        e["before"]!=0 or e["after"]==0
    ):
        return False
    return (observed_thumb_strb_address(e["opcode"],registers(e))==address
            and observed_thumb_strb_source_byte(e["opcode"],registers(e))
            == e["after"])

def callback_str(e, kind):
    address=MAIN+4*(kind-3)
    ptr=e["after"]
    if e["kind"]!=kind or e["address"]!=address or not (
        0x08000001 <= ptr <= 0x09FFFFFF and ptr&1
    ):
        return False
    snapshot=registers(e)
    # The inherited PR92 STR witness is preserved; PR82 public STMIA
    # decoder can explain either callback word of one multiword store.
    return (observed_thumb_str_word_store(e["opcode"],snapshot)==(address,ptr)
            or original_thumb_stmia_word_at(e["opcode"],snapshot,address)==ptr)

def evaluate(data):
    actor=actor_chain(data)  # inherits strict original CPU schema audit
    ev=data["events"]
    complete=[w for w in actor["windows"]
              if w["full_marker_chain_candidate_UNVERIFIED"]]
    # No syntactic actor chain is itself a native success. A distinct
    # two-action trace cannot promote one unrelated result/field return.
    result_addr=data["candidate_outcome_byte_address"]
    results=[e for e in ev if e["kind"]==1]
    inbattle=[e for e in ev if e["kind"]==2]
    callback1=[e for e in ev if e["kind"]==3]
    callback2=[e for e in ev if e["kind"]==4]
    manual=[e["step"] for e in ev if e["kind"]==8]
    emitters=[e["step"] for e in ev if e["kind"]==6]
    no_result_transition_ambiguity=(len(results)==1 and
                                    result_byte_store(results[0],result_addr))
    no_main_transition_ambiguity=(len(inbattle)==1 and
                                  inbattle[0]["before"]!=0 and
                                  inbattle[0]["after"]==0)
    no_callback_ambiguity=(len(callback1)==len(callback2)==1 and
                           callback_str(callback1[0],3) and
                           callback_str(callback2[0],4))
    same_step_stmia_pair = (
        no_callback_ambiguity and
        callback1[0]["step"] == callback2[0]["step"] and
        original_thumb_stmia_word_at(callback1[0]["opcode"],
            registers(callback1[0]),MAIN)==callback1[0]["after"] and
        original_thumb_stmia_word_at(callback2[0]["opcode"],
            registers(callback2[0]),MAIN+4)==callback2[0]["after"]
    )
    # Both same-step watchers must be attributable to ONE Thumb STMIA.
    # Inherited original CPU audit checks identical PC/opcode/registers
    # for same-step watcher records; STR cannot write two callback words.
    callbacks_ordered = (
        no_callback_ambiguity and
        (callback1[0]["step"]<callback2[0]["step"] or
         bool(same_step_stmia_pair))
    )
    admissible=(len(complete)==1 and len(actor["windows"])==1 and
                actor["denied_original_emitters_not_promoted"]==0 and
                len(emitters)==1 and not manual and
                no_result_transition_ambiguity and
                no_main_transition_ambiguity and callbacks_ordered)
    if admissible:
        w=complete[0]
        # STR callbacks require separate CPU steps. One STMIA may write
        # both callback words during SAME original CPU step, and the
        # post-step watcher logs report two rows for that instruction.
        # All prior actor/result/Main transitions must remain distinct.
        order=[
            w["emitter_step"],w["candidate_reply_step_unverified"],
            w["candidate_target_step_unverified"],
            w["candidate_pp_step_unverified"],
            results[0]["step"],inbattle[0]["step"],
            callback1[0]["step"],
        ]
        admissible=(all(type(v) is int for v in order) and
                    all(earlier<later for earlier,later in zip(order,order[1:]))
                    and callbacks_ordered)
    return {
        "schema":"sg-public-original-actor0-terminal-joint-v1",
        "actor0_marker_chain_candidates_unverified":
            actor["candidate_complete_original_marker_chains_UNVERIFIED"],
        "exactly_one_result_thumb_strb_watcher_unverified":
            bool(no_result_transition_ambiguity),
        "exactly_one_main_battle_exit_watcher_unverified":
            bool(no_main_transition_ambiguity),
        "exactly_one_ordered_full32_callback_str_each_unverified":
            bool(no_callback_ambiguity and len(callback1)==1 and
                 len(callback2)==1 and
                 callback1[0]["step"] < callback2[0]["step"]),
        "exactly_one_ordered_full32_callback_wordstore_pair_UNVERIFIED":
            bool(callbacks_ordered),
        "same_original_cpu_step_stmia_callback_pair_UNVERIFIED":
            bool(same_step_stmia_pair),
        "joined_actor0_pp_result_main_callback_candidate_UNVERIFIED":
            bool(admissible),
        "missing_or_ambiguous_joint_witness":not admissible,
        "original_outcome_byte_address_authenticated":False,
        "original_engine_one_use_actor0_request_certified":False,
        "original_move_target_legality_certified":False,
        "original_pp_execution_or_cancellation_certified":False,
        "original_outcome_decision_pc_certified":False,
        "original_overworld_callback_execution_certified":False,
        "original_native_acceptance_scenarios":0,
        "production_authorized":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("public_event_json",type=Path)
    args=p.parse_args()
    print(json.dumps(evaluate(json.loads(args.public_event_json.read_text())),
                     sort_keys=True,indent=2))
if __name__=="__main__":
    main()
