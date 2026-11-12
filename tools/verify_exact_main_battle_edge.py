#!/usr/bin/env python3
"""Fail-closed, offline Main.inBattle transition triage for exact modified ROM.

A CPU step associated with Main.inBattle bit 1 changing is NOT evidence of
battle-outcome decision, win/loss, PP debit, safe cancellation, or full terminal.
The complete trace and ROM checks are private; no raw ROM is published.
"""
import argparse
import hashlib
import json
from pathlib import Path

CURRENT = "7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
MODIFIED = "4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
SAVE = "8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4"
SCHEMA = "sg-exact-main-inbattle-edge-v1"
C1_OLD = 0x0808CBDD
C1_NEW = 0x081C7589
C2_OLD = 0x0808F225
C2_NEW = 0x081C9FC5
TRACE_KEYS = {"schema", "current_sha256", "modified_sha256", "save_sha256", "guest_writes",
              "host_move_menu_inputs", "new_hook_installed", "status", "start_frame",
              "end_frame", "window_frames", "guest_steps", "start_byte", "end_byte",
              "start_callback1", "end_callback1", "start_callback2", "end_callback2",
              "start_flags", "end_flags", "events"}
EVENT_KEYS = {"frame", "step_index", "pc", "opcode_halfword", "before_byte", "after_byte",
              "before_callback1", "after_callback1", "before_callback2", "after_callback2",
              "before_flags", "after_flags", "before_pending", "after_pending",
              "before_battlers", "after_battlers", "registers"}

def require(ok, why):
    if not ok:
        raise ValueError(why)

def u32(v):
    return type(v) is int and 0 <= v <= 0xFFFFFFFF

def audit(d):
    require(type(d) is dict and set(d) == TRACE_KEYS and d["schema"] == SCHEMA,
            "unknown Main transition transcript schema")
    require(d["current_sha256"] == CURRENT and d["modified_sha256"] == MODIFIED
            and d["save_sha256"] == SAVE, "wrong protected or modified ROM/save identity labels")
    require(type(d["guest_writes"]) is int and d["guest_writes"] == 0
            and type(d["host_move_menu_inputs"]) is int and d["host_move_menu_inputs"] == 0
            and d["new_hook_installed"] is False, "guest or host mutation disallowed")
    require(type(d["status"]) is int and d["status"] == 1,
            "CPU trace overflow, invalid inputs or frame budget unfinished")
    require(all(u32(d[k]) for k in TRACE_KEYS - {
        "schema", "current_sha256", "modified_sha256", "save_sha256", "guest_writes",
        "host_move_menu_inputs", "new_hook_installed", "events", "status"}),
        "invalid frame/step/Main field")
    start, end, window = d["start_frame"], d["end_frame"], d["window_frames"]
    require(1 <= window <= 10000 and start + window <= end,
            "unfinished or invalid frame window")
    require(d["guest_steps"] >= 1 and d["guest_steps"] <= 0xFFFFFFFF,
            "invalid guest step count")
    require(d["start_byte"] <= 255 and d["end_byte"] <= 255,
            "inBattle field is a single original byte")
    require(d["start_flags"] in (0, 4) and d["end_flags"] in (0, 4),
            "unexpected original wild mode")
    rows = d["events"]
    require(type(rows) is list and len(rows) <= 256,
            "too many original Main bit transitions")
    last_step = -1
    last_frame = -1
    active = d["start_byte"] & 2
    for row in rows:
        require(type(row) is dict and set(row) == EVENT_KEYS,
                "unknown or private CPU event fields")
        require(all(u32(row[k]) for k in EVENT_KEYS - {"registers"}),
                "invalid CPU event value")
        regs = row["registers"]
        require(type(regs) is list and len(regs) == 8 and all(u32(x) for x in regs),
                "invalid pre-instruction CPU registers")
        require(start <= row["frame"] < end and row["frame"] >= last_frame
                and row["step_index"] > last_step and row["step_index"] < d["guest_steps"],
                "duplicated or out-of-order CPU instruction edge")
        require(row["before_byte"] <= 255 and row["after_byte"] <= 255,
                "not original inBattle byte")
        before, after = row["before_byte"] & 2, row["after_byte"] & 2
        require(before == active and before != after,
                "not a real inBattle bit-1 transition in chronological sequence")
        require(row["before_flags"] in (0, 4) and row["after_flags"] in (0, 4)
                and row["before_battlers"] in (0, 2) and row["after_battlers"] in (0, 2),
                "not original wild/safe-terminal state")
        pc = row["pc"]
        require((pc == 0 and row["opcode_halfword"] == 0) or
                (0x08000000 <= pc <= 0x09FFFFFE and pc % 2 == 0
                 and row["opcode_halfword"] <= 0xFFFF),
                "instruction address not supported or opcode malformed")
        active = after
        last_step = row["step_index"]
        last_frame = row["frame"]
    require(active == (d["end_byte"] & 2),
            "missing/extra Main transition at end of completed frame budget")
    # The Main bit could clear on forced transition as well as normal victory;
    # callback values and stale battle flags NEVER change this classification.
    return {
        "source_scope": "original gMain.inBattle bit-1 CPU-step edges only",
        "inbattle_bit_transitions": len(rows),
        "observed_clear_edges": sum(bool(e["before_byte"] & 2) and
                                    not bool(e["after_byte"] & 2) for e in rows),
        "observed_set_edges": sum(not bool(e["before_byte"] & 2) and
                                  bool(e["after_byte"] & 2) for e in rows),
        "cpu_pc_candidates": [f"0x{e['pc']:08X}" if e["pc"] else "UNRESOLVED"
                              for e in rows],
        "callbacks_changed_by_window": (d["start_callback1"] != d["end_callback1"]
                                        or d["start_callback2"] != d["end_callback2"]),
        "guest_instruction_opcode_parity_verified": False,
        "original_battle_outcome_decision_pc_certified": False,
        "original_native_result_or_victory_certified": False,
        "full_unattended_terminal_certified": False,
        "unmatched_pp_reason_certified": False,
        "dynamic_legality_and_one_use_certified": False,
        "manual_fallback_certified": False,
        "formal_gameplay_acceptance": 0,
        "production_promotion_authorized": False,
    }

def sha(b):
    return hashlib.sha256(b).hexdigest()

def attest(raw, current, modified, save):
    require(len(current) == len(modified) == 33554432 and len(save) == 131072,
            "missing or truncated original/modified game and save")
    require(sha(current) == CURRENT and sha(modified) == MODIFIED and sha(save) == SAVE,
            "private exact input hashes do not match")
    data = json.loads(raw.decode("utf-8"))
    result = audit(data)
    matches = 0
    for row in data["events"]:
        pc = row["pc"]
        if not pc:
            continue
        off = pc - 0x08000000
        require(int.from_bytes(modified[off:off+2], "little") == row["opcode_halfword"],
                "CPU edge opcode not byte-identical to separate exact modified ROM")
        matches += 1
    result["private_trace_sha256"] = sha(raw)
    result["exact_modified_rom_instruction_match_count"] = matches
    result["original_battle_outcome_decision_pc_certified"] = False
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ("private_trace", "current", "modified", "save"):
        ap.add_argument("--" + k.replace("_", "-"), required=True, type=Path)
    args = ap.parse_args()
    paths = [getattr(args, k) for k in ("private_trace", "current", "modified", "save")]
    for path in paths:
        if not path.is_file() or path.is_symlink():
            ap.error("existing regular private inputs required; no symlinks")
    try:
        print(json.dumps(attest(*(p.read_bytes() for p in paths)), sort_keys=True, indent=2))
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        ap.error(str(exc))

if __name__ == "__main__":
    main()
