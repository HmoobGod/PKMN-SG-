# Exact original PP writer: raw PC sightings are not player0-owned moves

This independent source-only research draft is based on immutable
`source-first/rom-identity`
`655d2430c5891c12bbf4bc526b9f98f1468d433b`.
No protected branch, private game ROM/save, approved exact head or
runtime controller source changes.

## Research evidence gap

The existing original outcome/PP verifier reported a genuine
`0x0809E6BA` + exact own PP address + one-byte decrement as an
`original_pp_writer_single_byte_debits_seen` observation. That is
accurate as a **raw CPU PC + byte mutation**, but the report did not
distinguish this from a plausible active original **player0**
wild-single move context. The original writer PC could be encountered
when flags/battlers are no longer compatible, or after the recorded
Main battle bit has already cleared. This risks over-interpreting
the two historical PP-unmatched actions.

## Narrow, additive provenance classification

Keep the original raw writer count unchanged. Add an expressly
**UNVERIFIED** subset
`contextual_actor0_pp_writer_candidates_unverified`. A writer
belongs to this subset ONLY if a prior original CPU player0 emitter
had exact packed target battler1 and own slot (0..3), wild flags4,
battlers2 and Main bit active; the PP writer event must debit that
slot at the original instruction/address while current flags,
battlers and Main context still agree. A Main battle **bit1 clear**
unconditionally retires the previous emitter; a later Main set
does not revive it without a new original player0 emitter.
Main bit0-only noise is not an exit. Wrong slot or nondebit never
qualifies.

This subset is only **contextual correlation**, not proof of an
engine-issued one-use request epoch, full reply/complete/validator/
slot/move/target chain, effective runtime restrictions, real
action execution, PP-cancellation classification, battle outcome
or safe manual fallback. The existing stricter actor-epoch and joint
verifiers still decide whether a full command candidate was observed.
No automatic acceptance or production promotion field is changed.

The new public synthetic test covers original-looking valid PC
with wrong target/owner context, wrong battle flags, battler count,
Main cleared/reentry, stale emitter after reentry, fresh emitter,
Main bit0-only noise, wrong slot and no PP debit. Source-only CI
runs both original outcome audit and new tests. It never invokes
private `attest()` or reads/runs game bytes.

Actual original-game native formal acceptance **0/20 (0%)**,
production Smart Auto-Battle **0%**, two historical PP-less causes
resolved **0/2**. This candidate alone does not classify either
historic case.

Keep draft/unmerged pending completed exact-head Source CI and a
NEW independent Claude source/test/security review. Nothing here
changes user ROM/save, manual fallback, items/capture, foe/NPC AI,
doubles or any previously approved SHA.
