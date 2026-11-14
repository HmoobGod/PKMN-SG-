#!/usr/bin/env python3
"""Conservative original actor0 marker-to-PP window research, no native claims.

All windows are SOURCE-ONLY hypotheses. A PP write following an original
emitter in a trace does NOT establish actor ownership, execution, cancellation,
move legality, or an engine-issued one-use request. Historical causes remain
unclassified until separately authorized original-game evidence exists.
"""
import json
import argparse
from pathlib import Path
from verify_exact_outcome_pp_edges import (
    audit, PP, observed_thumb_strb_address, observed_thumb_strb_source_byte,
)

PP_WRITER_PC = 0x0809E6BA

def is_original_byte_writer_candidate(e):
    if e["kind"] != 5 or e["pc"] != PP_WRITER_PC:
        return False
    regs=tuple(e["r"+str(i)] for i in range(8))
    return (e["address"] == PP+e["slot"] and
            observed_thumb_strb_address(e["opcode"],regs) == e["address"] and
            observed_thumb_strb_source_byte(e["opcode"],regs) == e["after"] and
            e["before"] == e["after"]+1)

def triage(raw):
    certified=audit(raw)  # strict v3 CPU identity, chronology, no promotion
    emitted=[]
    current=None
    orphan_pp=0
    seen_writer=0
    for e in raw["events"]:
        kind=e["kind"]
        if kind==6:  # original actor0 emission marker, not request epoch proof
            current={"emitter_step":e["step"],"reply_count":0,
                     "completion_count":0,"syntactic_pp_candidate_count":0,
                     "other_pp_changes":0}
            emitted.append(current)
        elif kind==7 and current is not None:
            current["reply_count"]+=1
        elif kind==12 and current is not None:
            current["completion_count"]+=1
        elif kind==5:
            candidate=is_original_byte_writer_candidate(e)
            if candidate:
                seen_writer+=1
            if current is None:
                orphan_pp+=1
            elif candidate:
                current["syntactic_pp_candidate_count"]+=1
            else:
                current["other_pp_changes"]+=1
    if seen_writer!=certified["original_pp_strb_source_byte_matches_poststep"]:
        raise ValueError("unmatched original source decoder versus PP audit")
    n0=sum(w["syntactic_pp_candidate_count"]==0 for w in emitted)
    n1=sum(w["syntactic_pp_candidate_count"]==1 for w in emitted)
    nmore=sum(w["syntactic_pp_candidate_count"]>1 for w in emitted)
    return {
        "schema": "sg-public-original-pp-marker-windows-v1",
        "original_emitter_marker_windows_unverified":len(emitted),
        "windows_with_reply_marker_unverified":sum(w["reply_count"]>0 for w in emitted),
        "windows_with_completion_marker_unverified":sum(w["completion_count"]>0 for w in emitted),
        "one_syntactic_pp_writer_in_window_unverified":n1,
        "no_syntactic_pp_writer_in_window_UNCLASSIFIED":n0,
        "multiple_syntactic_pp_writers_in_window_AMBIGUOUS":nmore,
        "pp_changes_before_any_emit_unattributed":orphan_pp,
        "other_pp_changes_in_emitter_windows_unattributed":sum(w["other_pp_changes"] for w in emitted),
        "syntactic_pp_writer_candidates_total":seen_writer,
        "windows":[dict(w) for w in emitted],
        "real_actor0_one_use_engine_request_certified":False,
        "historical_two_pp_missing_causes_classified":False,
        "actual_pp_execution_or_cancellation_certified":False,
        "native_gameplay_scenarios_accepted":0,
        "production_authorized":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("public_event_json",type=Path)
    args=p.parse_args()
    report=triage(json.loads(args.public_event_json.read_text()))
    print(json.dumps(report,indent=2,sort_keys=True))
if __name__=="__main__":
    main()
