#!/usr/bin/env python3
"""Read-only original actor0 controller-lifecycle ambiguity: PUBLIC evidence.

This is a conservative filter on the PR92 synthetic joined CPU witness. A
positive does not prove that an original request is engine-owned or one-use;
a negative does not prove an in-game request was illegal or cancelled.
"""
import argparse
import json
from pathlib import Path
from triage_original_actor0_terminal_joint import evaluate as terminal_candidate

def evaluate(data):
    upstream=terminal_candidate(data)  # inherited strict v3 CPU audit
    events=data["events"]
    emit=[e for e in events if e["kind"]==6]
    pp=[e for e in events if e["kind"]==5]
    outcome=[e for e in events if e["kind"]==1]
    completed=[e for e in events if e["kind"]==12]
    # The base's joint witness already requires exactly one actor chain,
    # one PP store and one result. This code deliberately does not build
    # an alternative permissive chain when that witness failed.
    base=upstream["joined_actor0_pp_result_main_callback_candidate_UNVERIFIED"]
    complete_before_result=bool(base and len(completed)==1 and
                                completed[0]["step"]<outcome[0]["step"])
    if base:
        start=emit[0]["step"]
        pp_step=pp[0]["step"]
        # Mark every mask or pending watcher at start, at PP step, and in
        # between as ambiguous regardless of JSON ordering (same original
        # CPU step emits pre-markers and post-step watched changes).
        ownership_watch=[e for e in events if e["kind"] in (9,10) and
                         start<=e["step"]<=pp_step]
        flags=[e["step"] for e in ownership_watch if e["kind"]==9]
        pending=[e["step"] for e in ownership_watch if e["kind"]==10]
    else:
        flags=[]
        pending=[]
    candidate=bool(base and complete_before_result and
                   not flags and not pending)
    return {
        "schema":"sg-public-original-actor0-lifecycle-barrier-v1",
        "upstream_original_joint_candidate_unverified":bool(base),
        "completion_before_candidate_result_unverified":
            complete_before_result,
        "controller_exec_mask_transition_steps_in_action_window":flags,
        "original_pending_transition_steps_in_action_window":pending,
        "uninterrupted_owner_window_candidate_UNVERIFIED":candidate,
        "ambiguous_or_missing_owner_lifecycle_evidence":not candidate,
        "original_controller_mask_owner_bit_attested":False,
        "original_one_use_request_ownership_certified":False,
        "original_target_and_move_semantics_certified":False,
        "pp_debit_or_cancellation_reason_certified":False,
        "original_outcome_decision_pc_certified":False,
        "original_overworld_return_certified":False,
        "native_gameplay_accepted":0,
        "production_authorized":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("public_event_json",type=Path)
    args=p.parse_args()
    print(json.dumps(evaluate(json.loads(args.public_event_json.read_text())),
                     indent=2,sort_keys=True))
if __name__=="__main__":
    main()
