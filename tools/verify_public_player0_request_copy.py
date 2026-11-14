#!/usr/bin/env python3
"""Strict SOURCE-ONLY original player0 44-byte request copy Proof triage.

A memory-only C fake CPU can emit Proof as JSON for *synthetic* CI coverage.
This module does NOT authenticate the original modified ROM, emulator
instructions, private save, engine-owned one-use request epoch, gameplay,
or movement. No private file loading or attestation entry point exists.
"""
import json

BRIDGE_SCHEMA = "sg-public-synthetic-request-copy-v3"
PROOF_FIELDS = frozenset((
    "state", "error", "begin_frame", "end_frame", "entry_frame", "post_frame",
    "source", "dest", "actor", "direction", "length", "entry_sp", "entry_lr",
    "post_sp", "post_lr", "stores", "pending_entry", "pending_post",
    "opcode_post", "total_steps", "tag", "source_before", "source_after",
    "dest_after", "store_values", "store_indices", "dest_before",
    "entry_insn", "store_insn", "post_insn",
))
ARRAYS = ("source_before", "source_after", "dest_after", "store_values",
          "dest_before")
BASE = 0x02000000
END = 0x02040000
COUNT = 44
TAG = 0x16266007


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def u32(value):
    return type(value) is int and 0 <= value <= 0xFFFFFFFF


def byte_seq(value):
    return (type(value) is list and len(value) == COUNT and
            all(type(x) is int and 0 <= x <= 255 for x in value))


def audit_proof(proof):
    """Validate shape + internal recorder consistency, NEVER provenance."""
    require(type(proof) is dict and set(proof) == PROOF_FIELDS,
            "unexpected original player request proof field set")
    require(all(u32(proof[k]) for k in PROOF_FIELDS if k not in ARRAYS
                and k != "store_indices"), "invalid proof scalar field")
    require(all(byte_seq(proof[k]) for k in ARRAYS),
            "invalid or incomplete 44-byte proof array")
    indices = proof["store_indices"]
    require(type(indices) is list and len(indices) == COUNT and
            all(u32(v) for v in indices),
            "invalid proof store index array")
    require(proof["state"] == 2 and proof["error"] == 0,
            "not a completed successful candidate copy")
    require(proof["tag"] == TAG and proof["actor"] == 0
            and proof["direction"] == 0 and proof["length"] == COUNT,
            "wrong original player0 copy identity")
    require(proof["opcode_post"] == 19 and proof["source_before"][0] == 19,
            "not original 44-byte opcode19 request")
    require(all(0 < proof[name] <= 0xFFFF for name in
                ("entry_insn", "store_insn", "post_insn")),
            "missing or non-Thumb halfword CPU opcode")
    require(proof["stores"] == COUNT and indices == list(range(COUNT)),
            "missing, duplicated or unordered observed store")
    require(proof["source_before"] == proof["source_after"]
            == proof["dest_after"] == proof["store_values"],
            "observed request-copy bytes do not match")
    require(all(before != after for before, after in
                zip(proof["dest_before"], proof["store_values"])),
            "unchanged destination byte cannot witness original store")
    source, dest = proof["source"], proof["dest"]
    require(BASE <= source <= END - COUNT and
            BASE + 0x10 <= dest <= END - COUNT and
            (source + COUNT <= dest or dest + COUNT <= source),
            "original player0 copy out of bounds or overlapping")
    require(proof["entry_frame"] == proof["post_frame"] and
            proof["begin_frame"] <= proof["entry_frame"] <= proof["end_frame"]
            and proof["end_frame"] - proof["begin_frame"] <= 10000,
            "inconsistent original request copy frame chronology")
    require(proof["total_steps"] == COUNT + 1,
            "request entry + 44 observed stores require 45 guest steps")
    require(proof["entry_sp"] >= 8 and
            proof["post_sp"] == proof["entry_sp"] - 8 and
            proof["post_lr"] == proof["entry_lr"],
            "original player0 copy entry/post CPU register drift")
    # v2 rejects a pre-existing equal destination: this shows a memory
    # difference on FAKE CPU, not authentic original ROM instruction provenance.
    # The source pointer, pending status and byte equality do not attest
    # which instruction generated the trace. Zero certified gameplay.
    return {
        "scope": "PUBLIC SYNTHETIC C-proof INTERNAL consistency only",
        "internally_consistent_44_byte_player0_copy_candidate": True,
        "all_44_poststep_destination_changes_witnessed_in_fixture": True,
        "public_fake_cpu_opcode_triplet_recorded": True,
        "original_modified_rom_instruction_pc_attested": False,
        "engine_owned_one_use_request_epoch_certified": False,
        "effective_move_target_legality_certified": False,
        "real_player0_auto_move_or_pp_debit_certified": False,
        "native_battle_outcome_or_overworld_return_certified": False,
        "manual_fallback_certified": False,
        "native_acceptance_scenarios": 0,
        "production_promotion_authorized": False,
    }


# Fixed marker PC positions, not data read from a user-supplied transcript.
ORIGINAL_ENTRY_PC = 0x0806B372
ORIGINAL_STORE_PC = 0x0806B3C0
ORIGINAL_POST_PC = 0x0806B3C8


def verify_public_opcode_triplet_against_image(proof, image):
    """Compare three synthetic/public halfwords; caller must authenticate ROM.

    No private file IO, hash assertion, or native acceptance here. A match to
    an arbitrary fake image does NOT prove the guest executed an instruction.
    """
    require(type(image) in (bytes, bytearray), "CPU opcode image must be bytes")
    for key, pc in (("entry_insn", ORIGINAL_ENTRY_PC),
                    ("store_insn", ORIGINAL_STORE_PC),
                    ("post_insn", ORIGINAL_POST_PC)):
        offset = pc - 0x08000000
        require(offset + 2 <= len(image), "image missing public opcode PC")
        require(int.from_bytes(image[offset:offset+2], "little") == proof[key],
                "public CPU opcode triplet differs from supplied bytes")
    return True


def audit_public_fixture(raw):
    """Accept only the explicitly labeled in-memory fake C fixture schema."""
    require(type(raw) is dict and set(raw) == {
        "bridge_schema", "mode", "proof"}, "unknown fixture envelope")
    require(raw["bridge_schema"] == BRIDGE_SCHEMA
            and raw["mode"] in {
                "valid", "skipped_store", "bad_opcode", "wrapped_buffer",
                "wrong_register", "frame_rollback", "short_budget",
                "missing_callback", "preexisting_equal", "opcode_drift",
                "transient_dest", "transient_source"},
            "unknown request-copy fixture mode/schema")
    return audit_proof(raw["proof"])


if __name__ == "__main__":
    # No --private / --rom / --save CLI by design.
    import sys
    if len(sys.argv) != 1:
        raise SystemExit("no private input or attestation is accepted")
    print(json.dumps({"scope": "source-only; use test_player0_request_copy_json_audit.py",
                      "native_acceptance_scenarios": 0}))
