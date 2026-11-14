#!/usr/bin/env python3
"""Fail-closed read-only native outcome-candidate and PP edge triage.

This cannot identify gBattleOutcome from a guessed RAM byte, prove result
semantics, classify PP-less actions, or authorize an installed gameplay hook.
"""
import argparse
import hashlib
import json
from pathlib import Path

CURRENT = "7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
MODIFIED = "4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
SAVE = "8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4"
SCHEMA = "sg-original-outcome-pp-instruction-edges-v1"
PP = 0x02001EF1
MAIN = 0x030055D4
CALLBACK_WINDOWS = {
    0x0808E33C: "e92a2c689b0dc81c18664509bd52dfb00737b76d6c5b268ba952261301c21281",
    0x081AED58: "87a078714223450057d306b127deea90d6d8ef37173973216c103f72f95dc333",
    0x0809E6BA: "84ffa68c024412568ce64fdac3719cd460c40a55caf07a5549bd150a7fe50923",
}
FIELDS = {"frame", "step", "pc", "kind", "address", "before", "after", "slot",
          "r0", "r1", "r2", "r3", "r4", "flags", "battlers", "pending",
          "inbattle", "callback1", "callback2"}
# Events 1..16 match C observer; markers 6..8 and 12..16.
ADDRESSES = {2: MAIN+0x439, 3: MAIN, 4: MAIN+4,
             9: 0x02001AB4, 10: 0x02001D2C, 11: MAIN+0x438}


def require(test, why):
    if not test:
        raise ValueError(why)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def audit(data):
    require(type(data) is dict and data.get("schema") == SCHEMA, "wrong trace schema")
    require(data.get("current_sha256") == CURRENT and
            data.get("modified_sha256") == MODIFIED and
            data.get("save_sha256") == SAVE, "identity metadata does not match")
    require(data.get("guest_writes") == 0 and data.get("host_move_menu_inputs") == 0
            and data.get("new_hook_installed") is False,
            "active input/guest writes or installed hook not allowed")
    addr = data.get("candidate_outcome_byte_address")
    reserved = set(range(PP, PP+4)) | set(range(0x02001AB4, 0x02001AB8)) \
               | set(range(0x02001D2C, 0x02001D30))
    require(type(addr) is int and (addr == 0 or
            (0x02000000 <= addr <= 0x0203FFFF and addr not in reserved)),
            "outcome address must be absent or a non-overlapping EWRAM candidate")
    require(data.get("status") == 1 and type(data.get("steps")) is int
            and 0 < data["steps"] <= 0xFFFFFFFF,
            "only completed bounded original guest stepping is accepted")
    rows = data.get("events")
    require(type(rows) is list and 1 <= len(rows) <= 2048, "unbounded/no native edge events")
    candidate = native_pp = other_pp = emissions = replies = callbacks = manual = 0
    complete = validator = slots = moves = targets = 0
    contextual_actor0_pp = 0
    # Contextual *candidate* ONLY, not one-use ownership/legality proof.
    # A real Main bit1 clear permanently retires the old emitter. A later
    # battle re-entry never resurrects it without another original emitter.
    actor0_slot = None
    main_cleared = False
    prev_frame = prev_step = prev_pc = -1
    seen_edges = set()
    for e in rows:
        require(type(e) is dict and set(e) == FIELDS and
                all(type(e[k]) is int and 0 <= e[k] <= 0xFFFFFFFF for k in FIELDS),
                "unexpected original CPU event fields or types")
        f, step, pc, kind = e["frame"],e["step"],e["pc"],e["kind"]
        require(1 <= kind <= 16 and pc % 2 == 0 and
                (0x08000000 <= pc < 0x0A000000 or
                 0x02000000 <= pc <= 0x0203FFFF or
                 0x03000000 <= pc <= 0x03007FFE),
                "invalid original Thumb PC/event type")
        require(step < data["steps"] and
                (step > prev_step or (step == prev_step and pc == prev_pc)) and
                f >= prev_frame, "reordered, duplicated or post-budget guest instructions")
        edge_key = (step, pc, kind, e["address"], e["slot"])
        require(edge_key not in seen_edges, "duplicated original guest instruction edge")
        seen_edges.add(edge_key)
        if kind in (6, 7, 8, 12, 13, 14, 15, 16):
            require(e["address"] == e["before"] == e["after"] == 0 and
                    e["slot"] == 255, "fabricated marker edge")
            if kind == 6:
                require(pc == 0x0806BD80 and e["r0"] == 0 and e["r2"] == 10,
                        "move emitter is not original actor0")
                emissions += 1
                packed = e["r3"]
                if (not main_cleared and (e["inbattle"] & 2) and
                    e["flags"] == 4 and e["battlers"] == 2 and
                    packed >> 8 == 1 and (packed & 255) < 4):
                    actor0_slot = packed & 255
                else:
                    actor0_slot = None
            elif kind == 7:
                require(pc == 0x0806B370 and e["r0"] == 0 and e["r1"] == 1
                        and e["r3"] == 6, "reply is not original actor0")
                replies += 1
            elif kind == 8:
                require(pc == 0x0806449C, "wrong manual-menu original PC")
                manual += 1
            elif kind == 12:
                require(pc == 0x0806261C and e["r0"] == 0,
                        "controller completion not original actor0")
                complete += 1
            elif kind == 13:
                require(pc == 0x08094330, "wrong original validator PC")
                validator += 1
            elif kind == 14:
                require(pc == 0x0809435C, "wrong original move-slot commit PC")
                slots += 1
            elif kind == 15:
                require(pc == 0x08094374, "wrong original move-ID commit PC")
                moves += 1
            elif kind == 16:
                require(pc == 0x08094380, "wrong original target commit PC")
                targets += 1
        else:
            require(e["before"] != e["after"], "non-changing memory edge")
            require(e["slot"] == 255 if kind != 5 else 0 <= e["slot"] < 4,
                    "invalid PP slot / watcher slot")
            if kind == 1:
                require(addr and e["address"] == addr and
                        e["before"] <= 255 and e["after"] <= 255,
                        "outcome CANDIDATE watcher address mismatch")
                candidate += 1
            elif kind == 5:
                require(e["address"] == PP+e["slot"] and
                        e["before"] <= 255 and e["after"] <= 255,
                        "wrong original own PP byte")
                if (pc == 0x0809E6BA and e["r1"] == e["address"] and
                    e["before"] == e["after"]+1):
                    native_pp += 1
                    if (actor0_slot == e["slot"] and not main_cleared and
                        (e["inbattle"] & 2) and e["flags"] == 4 and
                        e["battlers"] == 2):
                        contextual_actor0_pp += 1
                else:
                    other_pp += 1
            else:
                require(e["address"] == ADDRESSES[kind],
                        "wrong original callback/battle watcher address")
                if kind in (2,11):
                    require(e["before"] <= 255 and e["after"] <= 255,
                            "expected single-byte Main field")
                if kind == 2 and ((e["before"] ^ e["after"]) & 2):
                    main_cleared = not bool(e["after"] & 2)
                    if main_cleared:
                        actor0_slot = None
                if kind == 3:
                    callbacks += 1
                    if pc == 0x0808E33C:
                        require(e["r4"] == MAIN and e["callback1"] == e["after"],
                                "original callback1 CPU registers disagree")
                if kind == 4:
                    callbacks += 1
                    if pc == 0x081AED58:
                        require(e["r3"] == MAIN and e["callback2"] == e["after"],
                                "original callback2 CPU registers disagree")
        prev_frame,prev_step,prev_pc = f,step,pc
    # Counts are observations ONLY; no guessing a PP debit's action epoch.
    return {
        "candidate_outcome_address_unverified": bool(addr),
        "candidate_outcome_byte_transitions": candidate,
        "original_callback_pointer_transitions": callbacks,
        "original_player_emit_markers": emissions,
        "original_player_reply_markers": replies,
        "original_player_completion_markers": complete,
        "original_validator_markers": validator,
        "original_slot_commit_markers": slots,
        "original_move_commit_markers": moves,
        "original_target_commit_markers": targets,
        "original_pp_writer_single_byte_debits_seen": native_pp,
        # Subset of raw writer sightings with a preceding original actor0
        # emitter since the last Main clear and live wild-single context.
        # NOT original engine-issued epoch proof or actual attack acceptance.
        "contextual_actor0_pp_writer_candidates_unverified": contextual_actor0_pp,
        "other_player_pp_byte_changes_not_certified": other_pp,
        "manual_move_menu_markers": manual,
        "previous_two_pp_unmatched_submissions_classified": False,
        "original_battle_outcome_decision_pc_certified": False,
        "full_native_terminal_certified": False,
        "effective_move_restrictions_certified": False,
        "one_use_request_ownership_certified": False,
        "gameplay_acceptance_scenarios": 0,
        "production_promotion_authorized": False,
    }


def attest(raw, current, modified, save):
    require(len(current) == len(modified) == 33554432 and len(save) == 131072,
            "private source ROM/save sizes differ")
    require(sha(current) == CURRENT and sha(modified) == MODIFIED and sha(save) == SAVE,
            "private original ROM/save mismatch")
    for pc, expected in CALLBACK_WINDOWS.items():
        off = pc-0x08000000
        a,b = current[off-16:off+48],modified[off-16:off+48]
        require(a == b and sha(a) == expected,
                "known original callback/PP writer Thumb parity failed")
    result = audit(json.loads(raw.decode("utf-8")))
    result["private_trace_sha256"] = sha(raw)
    result["exact_protected_rom_and_save_verified"] = True
    # The selected candidate RAM byte still requires independently established
    # gBattleOutcome identity, original result semantic and terminal replay.
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("private_trace", "current", "modified", "save"):
        p.add_argument("--"+name.replace("_","-"), type=Path, required=True)
    args = p.parse_args()
    paths = [getattr(args,n) for n in ("private_trace", "current", "modified", "save")]
    for path in paths:
        if not path.is_file() or path.is_symlink():
            p.error("existing regular private trace, ROMs and save are mandatory")
    try:
        result = attest(*(path.read_bytes() for path in paths))
    except (ValueError, KeyError, TypeError, UnicodeError) as error:
        p.error(str(error))
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__ == "__main__":
    main()
