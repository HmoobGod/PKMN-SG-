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
SCHEMA = "sg-original-outcome-pp-instruction-edges-v2"
PP = 0x02001EF1
MAIN = 0x030055D4
CALLBACK_WINDOWS = {
    0x0808E33C: "e92a2c689b0dc81c18664509bd52dfb00737b76d6c5b268ba952261301c21281",
    0x081AED58: "87a078714223450057d306b127deea90d6d8ef37173973216c103f72f95dc333",
    0x0809E6BA: "84ffa68c024412568ce64fdac3719cd460c40a55caf07a5549bd150a7fe50923",
}
FIELDS = {"frame", "step", "pc", "opcode", "kind", "address", "before", "after", "slot",
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
    # Never trust a trace-supplied acceptance/privilege field; every top-level
    # key must belong to the fixed evidence envelope and has strict types.
    top_fields = {"schema", "current_sha256", "modified_sha256",
                  "save_sha256", "guest_writes", "host_move_menu_inputs",
                  "new_hook_installed", "candidate_outcome_byte_address",
                  "status", "steps", "events"}
    require(type(data) is dict and set(data) == top_fields and
            data.get("schema") == SCHEMA, "wrong trace schema/field set")
    require(data.get("current_sha256") == CURRENT and
            data.get("modified_sha256") == MODIFIED and
            data.get("save_sha256") == SAVE, "identity metadata does not match")
    require(type(data.get("guest_writes")) is int and
            type(data.get("host_move_menu_inputs")) is int and
            data.get("guest_writes") == 0 and data.get("host_move_menu_inputs") == 0
            and data.get("new_hook_installed") is False,
            "active input/guest writes or installed hook not allowed")
    addr = data.get("candidate_outcome_byte_address")
    # Outcome candidates cannot alias already known wild-battle metadata:
    # flags, battler-count byte, request-copy buffer pointer, PP, pending.
    # These exclusions match the passive C observer's early guard.
    reserved = (set(range(PP, PP+4)) |
                set(range(0x02001AB4, 0x02001AB9)) |
                set(range(0x02001C6C, 0x02001C70)) |
                set(range(0x02001D2C, 0x02001D30)))
    require(type(addr) is int and (addr == 0 or
            (0x02000000 <= addr <= 0x0203FFFF and addr not in reserved)),
            "outcome address must be absent or a non-overlapping EWRAM candidate")
    require(type(data.get("status")) is int and data.get("status") == 1 and
            type(data.get("steps")) is int
            and 0 < data["steps"] <= 0xFFFFFFFF,
            "only completed bounded original guest stepping is accepted")
    rows = data.get("events")
    require(type(rows) is list and 1 <= len(rows) <= 2048, "unbounded/no native edge events")
    candidate = native_pp = other_pp = emissions = replies = callbacks = manual = 0
    complete = validator = slots = moves = targets = 0
    prev_frame = prev_step = prev_pc = -1
    seen_edges = set()
    last_cpu_snapshot = None
    last_poststep_context = None
    last_poststep_step = None
    prior_watched_after = {}
    # C samples all poststep watcher values from the same live core.
    # A trace cannot mix contradictory poststates for one CPU step.
    watcher_value_fields = {2: 'inbattle', 3: 'callback1', 4: 'callback2',
                            9: 'flags', 10: 'pending'}
    for e in rows:
        require(type(e) is dict and set(e) == FIELDS and
                all(type(e[k]) is int and 0 <= e[k] <= 0xFFFFFFFF for k in FIELDS),
                "unexpected original CPU event fields or types")
        f, step, pc, kind = e["frame"],e["step"],e["pc"],e["kind"]
        # CPU events outside the original ROM cannot be opcode-attested
        # against the protected modified-ROM image. No empty sentinel and
        # no RAM/BIOS instruction receives inferred provenance.
        require(1 <= kind <= 16 and pc % 2 == 0 and
                0x08000000 <= pc <= 0x09FFFFFE and
                e["opcode"] <= 0xFFFF,
                "missing original modified-ROM CPU PC/opcode provenance")
        require(step < data["steps"] and
                (step > prev_step or (step == prev_step and pc == prev_pc)) and
                f >= prev_frame, "reordered, duplicated or post-budget guest instructions")
        # The C collector records each marker before executing one CPU
        # instruction and memory changes after that SAME step; the original
        # registers, PC, opcode and frame cannot change among those events.
        # Watched RAM context may change as a result of the CPU step, so it
        # must NOT be frozen across pre/post events in the same step.
        cpu_snapshot = (f, pc, e["opcode"], e["r0"], e["r1"],
                        e["r2"], e["r3"], e["r4"])
        if step == prev_step:
            require(cpu_snapshot == last_cpu_snapshot,
                    "split or forged original CPU event within one step")
        last_cpu_snapshot = cpu_snapshot
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
            # sg_edge_append samples the watcher's `after` value and the
            # live snapshot only AFTER step(core). They must agree exactly.
            expected_context_field = watcher_value_fields.get(kind)
            if expected_context_field is not None:
                require(e[expected_context_field] == e["after"],
                        "poststep watcher and live RAM snapshot disagree")
            # Each PP slot is its own watcher; never link one slot's
            # previous byte to a different party move slot.
            watch_key = (kind, e["slot"]) if kind == 5 else kind
            if watch_key in prior_watched_after:
                require(prior_watched_after[watch_key] == e["before"],
                        "watcher chronology skips a changed RAM value")
            prior_watched_after[watch_key] = e["after"]
            context = tuple(e[k] for k in
                ("flags", "battlers", "pending", "inbattle", "callback1", "callback2"))
            if last_poststep_step == step:
                require(last_poststep_context == context,
                        "one CPU step has contradictory poststep RAM snapshots")
            else:
                last_poststep_step = step
                last_poststep_context = context
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
                else:
                    other_pp += 1
            else:
                require(e["address"] == ADDRESSES[kind],
                        "wrong original callback/battle watcher address")
                if kind in (2,11):
                    require(e["before"] <= 255 and e["after"] <= 255,
                            "expected single-byte Main field")
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


def verify_original_event_opcodes(rows, modified):
    """Byte-check EVERY recorded original CPU event; testable on fake bytes."""
    for event in rows:
        off = event["pc"] - 0x08000000
        require(0 <= off and off + 2 <= len(modified),
                "original event PC outside byte-pinned ROM range")
        require(int.from_bytes(modified[off:off+2], "little") ==
                event["opcode"], "original outcome PP CPU opcode parity failed")


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
    record = json.loads(raw.decode("utf-8"))
    result = audit(record)
    # An unchanged 64-byte PP writer/callback neighborhood alone cannot
    # authenticate the OTHER original instruction PCs in this trace.
    verify_original_event_opcodes(record["events"], modified)
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
