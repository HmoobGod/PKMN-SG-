#!/usr/bin/env python3
"""Conservative PUBLIC original actor0 marker-chain / PP provenance join.

Original CPU marker presence never proves executable move/target legality,
request ownership, PP execution intent, cancellation or gameplay readiness.
"""
import argparse
import json
from pathlib import Path
from triage_original_pp_marker_windows import (
    triage as pp_windows, is_original_byte_writer_candidate,
)

# Original C observer's pinned original-PC markers. The parent verifier
# checks their PCs and actor0-specific r0/r1/r2/r3 constraints first.
STAGES = ((7, "original_reply"), (13, "validator"),
          (14, "move_slot"), (15, "move_id"), (16, "target"))
COMPLETION = 12
PP = 5
BLOCKER_KINDS = (8,)

def evaluate(data):
    parent = pp_windows(data)  # all original v3 CPU schema/step invariants
    rows = data["events"]
    emitter_steps = sorted(e["step"] for e in rows if e["kind"] == 6)
    blockers = sorted({e["step"] for e in rows
                       if e["kind"] in BLOCKER_KINDS or
                       (e["kind"] == 2 and e["after"] == 0) or
                       (e["kind"] == 2 and e["before"] == 0 and
                        e["after"] != 0)})
    out = []
    for win in parent["windows"]:
        first = win["emitter_step"]
        # An overlapping or denied next emitter truncates ownership of
        # the previous marker interval even if it never starts a new
        # admitted parent window.
        next_emit = next((n for n in emitter_steps if n > first), data["steps"])
        next_barrier = next((n for n in blockers if n >= first), data["steps"])
        end = min(next_emit, next_barrier)
        events = [e for e in rows if first < e["step"] < end]
        group = {key: [e for e in events if e["kind"] == kind]
                 for kind, key in STAGES}
        completion = [e for e in events if e["kind"] == COMPLETION]
        pp_changes = [e for e in events if e["kind"] == PP]
        pp_candidates = [e for e in pp_changes
                         if is_original_byte_writer_candidate(e)]
        stage_names = [name for _, name in STAGES]
        single_stages = all(len(group[k]) == 1 for k in stage_names)
        stages_ordered = (single_stages and
                          all(group[stage_names[i]][0]["step"] <
                              group[stage_names[i+1]][0]["step"]
                              for i in range(len(stage_names)-1)))
        # A PP debit can occur before OR after controller completion.
        # It still needs a pinned original Thumb STRB byte-store candidate
        # and must not predate the candidate target-commit instruction.
        pp_possible = (len(pp_changes) == len(pp_candidates) == 1 and
                       stages_ordered and
                       pp_candidates[0]["step"] > group["target"][0]["step"])
        single_completion = len(completion) == 1
        completion_possible = (single_completion and len(group["original_reply"])==1
                               and completion[0]["step"] >
                               group["original_reply"][0]["step"])
        # Parent's summary can be positive even without commit markers.
        # This child never calls such a summary native ownership.
        syntactic_candidate = (
            not win["ambiguous_overlap"] and
            win["syntactic_pp_candidate_count"] == 1 and
            win["other_pp_changes"] == 0 and
            stages_ordered and pp_possible and completion_possible and
            win["reply_count"] == 1 and win["completion_count"] == 1
        )
        out.append({
            "emitter_step": first,
            "window_end_exclusive": end,
            "has_all_five_single_original_stage_markers": bool(single_stages),
            "five_stage_order_unverified": bool(stages_ordered),
            "completion_after_reply_unverified": bool(completion_possible),
            "one_post_target_thumb_pp_byte_debit_candidate_unverified":
                bool(pp_possible),
            "overlap_ambiguous": bool(win["ambiguous_overlap"]),
            "full_marker_chain_candidate_UNVERIFIED": bool(syntactic_candidate),
            "original_marker_counts": {k: len(group[k]) for k in stage_names},
            "completion_count": len(completion),
            "pp_change_count": len(pp_changes),
            "pp_byte_store_candidate_count": len(pp_candidates),
        })
    return {
        "schema": "sg-public-original-actor0-marker-chain-v1",
        "parent_window_schema": parent["schema"],
        "candidate_complete_original_marker_chains_UNVERIFIED":
            sum(x["full_marker_chain_candidate_UNVERIFIED"] for x in out),
        "missing_or_ambiguous_original_marker_chains":
            sum(not x["full_marker_chain_candidate_UNVERIFIED"] for x in out),
        "denied_original_emitters_not_promoted":
            parent["emitter_markers_denied_for_owner_epoch"],
        "windows": out,
        "source_only_marker_order_not_move_or_target_legality": True,
        "actual_engine_issued_one_use_request_certified": False,
        "actual_original_dynamic_legality_certified": False,
        "original_pp_execution_or_cancellation_certified": False,
        "historical_two_missing_pp_causes_classified": False,
        "original_native_gameplay_accepted": 0,
        "production_authorized": False,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("public_event_json", type=Path)
    a = parser.parse_args()
    print(json.dumps(evaluate(json.loads(a.public_event_json.read_text())),
                     indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
