# Original battle-outcome byte candidate: CPU writer-PC store triage

This separate **read-only source evidence** draft extends the stricter
original outcome/PP instruction-edge verifier from parent PR75 exact
`1871707aa0ab8deb3a70e12a4705ff8eb7b61714`, without touching
the independently source-approved PR72 or the sibling player0 request
copy semantics PR77.

## Concrete evidence gap

The prior outcome candidate watcher counted any change to a
user-specified, non-overlapping EWRAM byte as a 'candidate outcome
transition'. It did not require the recorded original CPU opcode to
encode a byte write to that exact watched address. A simultaneous
unrelated CPU instruction, or changed byte outside the opcode's actual
destination, could therefore be mistaken for a candidate original
result-writer **PC** in subsequent research.

## New fail-closed source gate

Each candidate EWRAM byte watcher change is now divided into
`candidate_outcome_strb_writer_matches_unverified` versus
`candidate_outcome_unattributed_byte_transitions`. A writer match
requires (1) an observed original pre-step Thumb-1 `STRB` immediate
or register-offset halfword, (2) the effective address computed from
all 8 recorded low CPU registers equals that same EWRAM byte, and
(3) the pre-step encoded source `Rt & 0xff` equals the witnessed
post-step byte. Only matching guest CPU PCs are included in the
deduplicated, sorted `candidate_outcome_writer_pc_candidates_unverified`
report list.

The watcher still requires nonreserved EWRAM candidate bounds, strict
event shape/order/CPU continuity and actual byte value change. The
added source-only synthetic tests cover a coherent STRB writer at
0x08012340, LDRB/word STR instruction false positives, incorrect
source register, incorrect destination, arithmetic overflow, repeated
writer PCs and absent candidate windows.

## Essential limits

This **does not** identify `gBattleOutcome`, certify the game-result
value or its semantics, or prove an overworld callback/return. The
candidate address is still unverified and may represent any unrelated
EWRAM byte. Fake CPU registers and original ROM byte parity are
untrusted unless separately attested in an explicitly authorized
owner-local genuine original game trace. The live protected ROM/save,
savestate, emulator and private traces are NOT opened, copied,
hashed, staged or executed in this source-only patch.

The main result flags deliberately stay FALSE:
`original_battle_outcome_decision_pc_certified`,
`full_native_terminal_certified`, `production_promotion_authorized`.
No player auto-gameplay code, enemy/NPC AI, manual fallback,
items/capture, production ROM or protected branches change.

Formal original-game native 0/20 = 0%, production Smart Auto 0%,
historical two PP missing-debit cause classifications 0/2.
