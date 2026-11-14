#!/usr/bin/env python3
"""Conservatively correlate original actor0 move/PP *candidates*.

Accept ONLY a completed exact-ROM observer transcript that has passed
verify_exact_outcome_pp_edges.audit. This is research and cannot certify a
result, a cancellation, game safety or an engine-owned one-use lease.
"""
import argparse
import json
from pathlib import Path
import verify_exact_outcome_pp_edges as base

MOVE_IDS = (325, 157, 92, 269)  # Historical original user party only.
ORDER = (7, 12, 13, 14, 15, 16)


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def correlate(trace):
    base.audit(trace)  # Validate ROM/save ID claims, source/read-only scope, PC and shape.
    results = []
    active = None
    orphan_pp = 0
    non_writer_pp = 0
    after_battle_clear = False
    for e in trace["events"]:
        kind = e["kind"]
        if kind == 2:
            # C watcher may report Main bit0-only noise. Only an original
            # battle-bit1 edge changes the lifetime of an actor0 candidate.
            if (e["before"] ^ e["after"]) & 2:
                # A genuine Main clear irrevocably closes the candidate.
                # A later Main set does NOT resume the old submission;
                # only a fresh actor0 emitter can start a new one.
                after_battle_clear = not bool(e["after"] & 2)
                if after_battle_clear and active is not None:
                    results.append(active)
                    active = None
        if kind == 6:
            # A fresh original actor0 emitter is a boundary, NOT a guaranteed
            # new engine-owned request epoch. No double attribution across it.
            packed = e["r3"]
            slot, foe = packed & 255, packed >> 8
            require(not after_battle_clear and (e["inbattle"] & 2)
                    and e["flags"] == 4 and e["battlers"] == 2
                    and foe == 1 and 0 <= slot < 4,
                    "emitter not authenticated player wild-single target context")
            if active is not None:
                results.append(active)
            active = dict(frame=e["frame"], slot=slot, expected_move=MOVE_IDS[slot],
                          reply=0, complete=0, validator=0, slot_commit=0,
                          move_commit=0, target_commit=0,
                          native_pp_debits=0, last_order=0, writer_frames=[])
            continue
        if kind in (7, 12, 13, 14, 15, 16):
            # An original engine PC can still be reached by other actors;
            # only an in-sequence player0 context can be correlated.
            if active is None:
                continue
            if kind == 13 and e["r0"] != 0:
                continue
            require(not after_battle_clear and (e["inbattle"] & 2)
                    and e["flags"] == 4 and e["battlers"] == 2,
                    "original commit/complete after exit or outside active wild battle")
            rank = ORDER.index(kind) + 1
            require(rank == active["last_order"] + 1,
                    "duplicate/missing/out-of-order original actor0 reply or commit")
            if kind == 14:
                require(e["r0"] == active["slot"], "original slot commit differs from emission")
            if kind == 15:
                require(e["r0"] == active["expected_move"],
                        "original move-ID commit differs from historical slot")
            if kind == 16:
                require(e["r2"] == 1, "original committed target is not the foe")
            name = {7:"reply",12:"complete",13:"validator",14:"slot_commit",
                    15:"move_commit",16:"target_commit"}[kind]
            active[name] += 1
            active["last_order"] = rank
            continue
        if kind == 5:
            if e["pc"] != 0x0809E6BA or e["before"] != e["after"] + 1:
                non_writer_pp += 1
                continue
            if active is None:
                orphan_pp += 1
                continue
            require(not after_battle_clear and (e["inbattle"] & 2)
                    and e["flags"] == 4 and e["battlers"] == 2,
                    "claimed PP debit after native battle context exited")
            require(active["last_order"] == len(ORDER),
                    "PP debit without full original player command chain")
            require(e["slot"] == active["slot"]
                    and e["address"] == base.PP + active["slot"]
                    and e["r1"] == e["address"],
                    "original PP byte/pointer belongs to different move slot")
            require(active["native_pp_debits"] == 0,
                    "repeated original PP writer on one candidate submission")
            active["native_pp_debits"] += 1
            active["writer_frames"].append(e["frame"])
    if active is not None:
        results.append(active)
    require(orphan_pp == 0,
            "native PP writer without a recorded original actor0 submission")
    # Results summarize provenance, not a proof that the proposed action
    # executed or that a no-debit action was rejected/cancelled.
    public=[]
    for r in results:
        complete = r["last_order"] == len(ORDER)
        public.append(dict(emit_frame=r["frame"], slot=r["slot"],
                           historical_move_id=r["expected_move"],
                           reply_and_commits_observed=complete,
                           original_pp_writer_observed=bool(r["native_pp_debits"]),
                           native_writer_frames=r["writer_frames"],
                           execution_or_cancellation_decision="UNPROVEN"))
    return dict(source_scope="original actor0 CPU marker chronology, source-only triage",
                candidate_player_submissions=len(public),
                complete_reply_commit_chains=sum(x["reply_and_commits_observed"] for x in public),
                original_pp_writer_debits=sum(x["original_pp_writer_observed"] for x in public),
                original_submissions_without_matched_writer=sum(not x["original_pp_writer_observed"] for x in public),
                non_writer_pp_byte_mutations=non_writer_pp,
                candidate_epochs=public,
                original_battle_outcome_decision_pc_certified=False,
                unmatched_submissions_reason_certified=False,
                dynamic_legality_or_one_use_ownership_certified=False,
                manual_fallback_or_full_terminal_certified=False,
                production_promotion_authorized=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--private-trace", type=Path, required=True)
    ap.add_argument("--current", type=Path, required=True)
    ap.add_argument("--modified", type=Path, required=True)
    ap.add_argument("--save", type=Path, required=True)
    args=ap.parse_args()
    for p in (args.private_trace,args.current,args.modified,args.save):
        if not p.is_file() or p.is_symlink():
            ap.error("private existing non-symlink inputs required")
    try:
        raw=args.private_trace.read_bytes()
        base.attest(raw,args.current.read_bytes(),args.modified.read_bytes(),args.save.read_bytes())
        result=correlate(json.loads(raw.decode("utf-8")))
    except (ValueError,UnicodeError,KeyError,TypeError) as e:
        ap.error(str(e))
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":main()
