#!/usr/bin/env python3
"""Validate a bounded read-only original-guest Thumb STRB discovery transcript.

This is an instruction + CPU-register provenance check for potential writes.
It NEVER identifies the battle outcome byte, interprets win/loss, classifies
unmatched PP submissions, certifies one-use ownership, or promotes gameplay.
"""
import argparse
import hashlib
import json
from pathlib import Path

CURRENT = "7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
MODIFIED = "4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
SAVE = "8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4"
SCHEMA = "sg-exact-thumb-strb-store-scout-v1"
MAIN = 0x030055D4
EVENT_FIELDS = {"frame", "step_index", "pc", "halfword", "form", "address",
                "base_register", "offset_register", "source_register",
                "old_byte", "new_byte", "expected_byte", "registers",
                "battle_flags", "battlers", "pending", "inbattle",
                "callback1", "callback2"}
TRACE_FIELDS = {"schema", "current_sha256", "modified_sha256", "save_sha256",
                "guest_writes", "host_move_menu_inputs", "new_hook_installed",
                "status", "guest_steps", "start_frame", "end_frame",
                "window_frames", "range_lo", "range_hi", "events",
                "start_inbattle", "end_inbattle", "start_callback1",
                "start_callback2", "end_callback1", "end_callback2"}


def require(test, reason):
    if not test:
        raise ValueError(reason)


def is_u32(value):
    return type(value) is int and 0 <= value <= 0xFFFFFFFF


def ram_region(lo, hi):
    return lo <= hi and ((0x02000000 <= lo <= hi <= 0x0203FFFF)
                        or (0x03000000 <= lo <= hi <= 0x03007FFF))


def decode(h, registers):
    """Decode two Thumb-1 STRB forms without using source-symbol assumptions."""
    if h & 0xF800 == 0x7000:
        form = 1
        rn, rt, rm = (h >> 3) & 7, h & 7, 255
        offset = (h >> 6) & 31
    elif h & 0xFE00 == 0x5400:
        form = 2
        rn, rt, rm = (h >> 3) & 7, h & 7, (h >> 6) & 7
        offset = registers[rm]
    else:
        raise ValueError("instruction is not a supported original Thumb-1 STRB")
    address = registers[rn] + offset
    require(address <= 0xFFFFFFFF, "guest address arithmetic overflow")
    return form, rn, rm, rt, address, registers[rt] & 255


def audit(data):
    require(type(data) is dict and set(data) == TRACE_FIELDS and
            data["schema"] == SCHEMA, "wrong or unbounded transcript schema")
    require(data["current_sha256"] == CURRENT and
            data["modified_sha256"] == MODIFIED and
            data["save_sha256"] == SAVE, "wrong original game/save provenance labels")
    require(type(data["guest_writes"]) is int and type(data["host_move_menu_inputs"]) is int
            and data["guest_writes"] == data["host_move_menu_inputs"] == 0
            and data["new_hook_installed"] is False,
            "not a passive original-guest read-only scout")
    require(type(data["status"]) is int and data["status"] == 1
            and is_u32(data["guest_steps"])
            and 0 < data["guest_steps"],
            "truncated, overflowed or timed-out instruction observation")
    lo, hi = data["range_lo"], data["range_hi"]
    require(is_u32(lo) and is_u32(hi) and ram_region(lo, hi),
            "watched region must be bounded GBA EWRAM or IWRAM")
    start, end, frames = (data["start_frame"],data["end_frame"],
                          data["window_frames"])
    require(all(is_u32(x) for x in (start, end, frames)) and
            1 <= frames <= 10000 and end >= start+frames,
            "original frame-budget completion unverified")
    require(all(is_u32(data[x]) for x in ("start_inbattle", "end_inbattle",
            "start_callback1", "start_callback2", "end_callback1", "end_callback2"))
            and data["start_inbattle"] <= 255 and data["end_inbattle"] <= 255,
            "untrusted original Main callback snapshots")
    events = data["events"]
    require(type(events) is list and len(events) <= 8192,
            "unbounded original guest byte-store events")
    previous_frame = previous_step = -1
    per_address = {}
    per_pair = {}
    for event in events:
        require(type(event) is dict and set(event) == EVENT_FIELDS,
                "unexpected guest CPU event fields")
        require(all(is_u32(event[k]) for k in EVENT_FIELDS-{"registers"}),
                "negative/non-integer/or oversized guest CPU fields")
        registers=event["registers"]
        require(type(registers) is list and len(registers) == 8 and
                all(is_u32(x) for x in registers), "untrusted original pre-CPU registers")
        f, step, pc = event["frame"],event["step_index"],event["pc"]
        require(start <= f <= end and f >= previous_frame and
                step > previous_step and step < data["guest_steps"],
                "out-of-order, duplicated or post-budget guest CPU write")
        require(0x08000000 <= pc <= 0x09FFFFFE and pc % 2 == 0,
                "non-ROM or misaligned original Thumb source PC")
        require(event["halfword"] <= 0xFFFF, "not a Thumb-1 instruction")
        decoded=decode(event["halfword"],registers)
        require(decoded == (event["form"],event["base_register"],
                            event["offset_register"],event["source_register"],
                            event["address"],event["expected_byte"]),
                "decoded original STRB instruction/register/address mismatch")
        a, old, new = event["address"],event["old_byte"],event["new_byte"]
        require(lo <= a <= hi and 0 <= old <= 7 and 0 <= new <= 7
                and old != new and event["expected_byte"] == new,
                "not a genuine bounded small-value STRB candidate")
        require(event["battle_flags"] in (0,4) and
                event["battlers"] in (0,2) and
                event["inbattle"] <= 255,
                "unexpected native wild/terminal context in original guest")
        per_address[a] = per_address.get(a,0)+1
        key=(pc,a)
        if key not in per_pair:
            per_pair[key]=dict(pc=f"0x{pc:08X}",address=f"0x{a:08X}",
                               instruction=f"0x{event['halfword']:04X}",
                               first_frame=f,last_frame=f,count=0,
                               observed_during_inbattle=bool(event["inbattle"] & 2))
        per_pair[key]["last_frame"]=f
        per_pair[key]["count"]+=1
        per_pair[key]["observed_during_inbattle"] |= bool(event["inbattle"] & 2)
        previous_step,previous_frame=step,f
    # Frame/callback observations alone never prove win/loss, PP cause,
    # full terminal or user-production gameplay. Candidate-only summary.
    return {
        "scope":"bounded original guest Thumb-1 STRB CPU/address scouting only",
        "ram_region":"EWRAM" if lo<0x03000000 else "IWRAM",
        "candidate_byte_stores":len(events),
        "distinct_ram_byte_addresses":len(per_address),
        "candidate_addresses_hex":[f"0x{a:08X}" for a in sorted(per_address)],
        "distinct_pc_address_pairs":len(per_pair),
        "candidate_pc_address_pairs":list(per_pair.values())[:64],
        "candidate_pc_list_truncated":len(per_pair)>64,
        "main_inbattle_before":data["start_inbattle"],
        "main_inbattle_after":data["end_inbattle"],
        "callback1_changed":data["start_callback1"]!=data["end_callback1"],
        "callback2_changed":data["start_callback2"]!=data["end_callback2"],
        "original_code_instructions_verified":False,
        "authentic_gbattleoutcome_address_identified":False,
        "original_battle_outcome_writer_pc_certified":False,
        "two_old_unmatched_pp_submissions_classified":False,
        "dynamic_legality_or_manual_fallback_certified":False,
        "full_native_terminal_certified":False,
        "formal_native_gameplay_acceptance":0,
        "production_promotion_authorized":False,
    }


def digest(x):
    return hashlib.sha256(x).hexdigest()


def attest(raw, current, modified, save):
    require(len(current) == len(modified) == 33554432 and len(save) == 131072,
            "missing/truncated exact original private ROMs/save")
    require(digest(current) == CURRENT and digest(modified) == MODIFIED
            and digest(save) == SAVE, "private original/exact modified/save identity mismatch")
    trace=json.loads(raw.decode("utf-8"))
    result=audit(trace)
    protected_matches=0
    for e in trace["events"]:
        off=e["pc"]-0x08000000
        actual=int.from_bytes(modified[off:off+2],"little")
        require(actual == e["halfword"],
                "original CPU opcode does not match exact modified ROM bytes")
        if current[off:off+2] == modified[off:off+2]:
            protected_matches+=1
    result.update(private_trace_sha256=digest(raw),
                  exact_modified_rom_opcode_matches=len(trace["events"]),
                  protected_current_instruction_parity_matches=protected_matches,
                  all_candidate_code_parity_to_current=(protected_matches==len(trace["events"])))
    # No candidate is automatically mapped to a gBattleOutcome global.
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("private_trace","current","modified","save"):
        p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    paths=[getattr(a,k) for k in ("private_trace","current","modified","save")]
    for path in paths:
        if not path.is_file() or path.is_symlink():
            p.error("regular non-symlink private ROM/save/trace required")
    try:
        result=attest(*(path.read_bytes() for path in paths))
    except (ValueError,TypeError,UnicodeError,KeyError) as e:
        p.error(str(e))
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
