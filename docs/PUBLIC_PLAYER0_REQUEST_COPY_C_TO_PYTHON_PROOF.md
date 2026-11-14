# Original 44-byte player0 request COPY: actual C observer → Python consistency gate

This is an isolated **PUBLIC / SOURCE-ONLY / SYNTHETIC** research draft
stacked on review-pending PR61 exact
`9c89ebb7d27a3fcc4558878a256f739e68cf065d`, which is unchanged.
Approval of PR61 or any ancestor does **not** transfer here.

## Gap closed

PR61 executes the original read-only player0 44-byte CPU COPY recorder
against a memory-only fake core. Its C assertions confirm 44 observed
post-step destination checks. However, the resulting 44-byte `Proof`
struct was not verified by an independent consumer. A later owner-local
original-game witness needs a separate, strict report-validation step.

This draft adds:

- `tools/test_player0_request_copy_json_fixture.c`: executes the
  **actual unchanged C recorder from PR61** and emits its full
  44-byte `Proof` as an explicitly labeled PUBLIC SYNTHETIC JSON
  envelope. Modes include successful full copy, skipped poststore,
  invalid opcode19, wrapped source buffer, wrong source register,
  clock rollback, partial CPU budget and missing ABI callback. It does
  **not** open emulator, ROM, save, private trace or host paths.
- `tools/verify_public_player0_request_copy.py`: validates exact
  shape/types/lengths and cross-consistency of all four 44-byte arrays,
  indexed 44 observed stores, original player0 identity, 44-byte
  opcode19 request, EWRAM source/destination/nonoverlap, entry/post
  frame and SP/LR chronology, exactly 45 stepped CPU instructions,
  and success/error/identity fields. No `attest()`, ROM/SAV loading,
  real CPU instruction provenance or promotion API.
- `tools/test_player0_request_copy_json_audit.py`: **compiles the
  real C fixture**, feeds all 8 output modes to the Python validator,
  insists only internally consistent synthetic baseline qualifies,
  and rejects 26 independent tampering mutations, unexpected schema,
  missing assertion compile guards and private CLI attempts.
- Full Source CI + dedicated five-minute public C→Python workflow.

All successful reports explicitly retain **zero** native gameplay
acceptance and no one-use engine request, dynamic legality, PP
writer/cancellation, battle outcome, overworld callback, manual
fallback or production-promotion claims.

## Important limits

A complete C proof is only *internally consistent*. A final buffer
byte equal to its expected value does not by itself prove the
individual original instruction executed if the byte was unchanged.
This does not authenticate the original modified-ROM opcode at
`0x0806B3BE` (store), the original caller PC, source-buffer ownership
or a one-use original request lease. **No original game ROM, private
save, private savestate, emulator session, actual engine-owned request,
or guest CPU replay has been run here.** A future separately authorized
owner-local immutable copy replay must independently pin the exact
original modified-ROM bytes, original original engine request
execution/control-flow and no-input same-run native move/PP/terminal.

This patch changes no underlying C observer or controller, no approved
exact SHA, protected main/source-first/Current ROM/save, no enemy/NPC
partner AI, auto items/capture, trainer/doubles eligibility or manual
fallback. The new files and CI wiring are independent source
verification only. PR61 remains DRAFT/unmerged.

Formal actual native acceptance **0/20 (0%)**.
Production native auto **0%**.
Two historical PP-unmatched causes classified **0/2**.

Hold this new draft unmerged until full exact-head Source CI, dedicated
C→Python workflow and an **independent Claude exact-head** source,
test and security review. An approved parent never authorizes child.


## Isolated PR64 follow-up: unchanged destination must fail closed

This intentionally incompatible **v2** synthetic proof envelope (not native
emulator evidence) requires a real *pre-step* destination byte for every one
of the 44 original STORE_PC candidate iterations. The read-only C recorder
refuses to increment its successful store count when the byte was already
equal to the intended store value, because a poststep equal byte alone does
not demonstrate an observable CPU memory change. A changed value must then
be observed **after** the corresponding step. Each original store index's
`dest_before[44]` is sent to the strict Python auditor, which requires a
well-formed 44-byte vector and an actual before/after difference for each
index, with the existing source/destination and chronology checks retained.
The old v1 JSON envelope is explicitly rejected; the C `Proof` struct has
been **extended at the tail** and any future local host binding must adopt
the new ABI explicitly before use. Its original fields retain order/offsets.

The new FAKE C mode `preexisting_equal` poisons byte 7 with the correct value
**before** the CPU step, so the old poststep-only check would wrongly pass.
The v2 test requires error 10 at index 7; 44 changed-byte positive cases,
negative C modes and Python JSON tamper mutations remain covered by CI.
This will reject legitimate original stores when destination bytes were
already equal (known evidence limitation; strict failure, not a false pass).
A changed byte after a fake CPU step also does **not** prove the original
modified-ROM instruction actually executed, prove engine-issued one-use
request ownership, legality, PP debit/cancellation, native battle outcome or
manual fallback. Separately owner-authorized exact modified-ROM provenance
and real original-game execution would still be needed; no Current ROM/save,
private trace or emulator is staged, read or run in this research patch.

Do not merge, install, release or count this source-only test as a native
acceptance case. Native original-game acceptance 0/20 (0%), production 0%,
and historical two PP-unmatched causes classified 0/2.


## Isolated PR67 follow-up: read-only pre-step Thumb instruction fingerprints

Existing fake-only 44-byte request-copy evidence records CPU markers, registers,
destination byte changes and source/destination identity, but no original
instruction halfwords at ENTRY_PC 0x0806B372, STORE_PC 0x0806B3C0, POST_PC
0x0806B3C8. New C observer records their PRE-step Thumb 16-bit halfwords
using its existing read8 callback, in append-only Proof ABI fields:
entry_insn, store_insn and post_insn. Every one of 44 pre-step STORE_PC
observations must yield the SAME nonzero halfword; an intervening opcode
mutation fails closed with error 11 before counting the changed byte.
Entry and post markers also require nonzero halfwords. The public JSON
bridge is explicitly incompatible v3, and strict Python rejects missing,
zero, oversized or boolean halfword fields.

A new pure byte-image parity helper compares the three observations with
the same fixed CPU addresses on a supplied **public synthetic 2-MiB image**.
It reads no files and does not authenticate any image hash. The C FAKE
core generates instruction words 0x2101/0x7003/0x4718 deliberately; these
values are NOT original Pokémon ROM instruction bytes. A mutation to the
store opcode after seven synthetic steps, changes in supplied image bytes,
and tampered JSON are negative controls. Exact original modified-ROM
identity and real CPU execution are still NOT proved. Future owner-local
private attestation would need a separately authorized authenticated
immutable ROM and actual emulator trace; none are read or executed here.

PR67 is an isolated child of PR64, itself independent-review pending,
and does not touch approved PR62 or PR61, main/source-first or Current
ROM/save. This is source-only evidence instrumentation, not playable
native gameplay, one-use engine request authority, effective legality,
PP debit/cancellation, outcome decision or manual fallback certification.
Original native 0/20 = 0%, production 0%, historical PP causes 0/2.


## Isolated follow-up: intermediate byte integrity at every observed store

The source-only read-only C 44-byte request observer originally checked
the destination's current store byte after each CPU step, but only
re-checked the full source and destination byte arrays at POST_PC.
That permits a prior destination byte or unrelated source byte to be
corrupted by a fake guest and **restored** before the final full-array
comparison, producing an apparently successful source-only proof.

The observer now checks the entire copied destination prefix AND all
44 unchanged source bytes after each witnessed STORE_PC step, before
incrementing its accepted store count. Transient copied-prefix corruption
fails with error 12 and in-flight source mutation with error 13. Dedicated
fake-only C modes corrupt byte 0 at store index 7 and would restore it
at index 8; both are rejected at index 7 (7 stores counted), so the
later restoration never masks the evidence violation. No guest writes
are performed by the observer; the fake core alone makes those changes.
No Proof ABI or JSON schema changes relative to PR67 v3.

This gate increases public trace *internal consistency* but is not an
authenticated instruction stream, original modified-ROM byte attestation,
engine-issued one-use request, dynamic legality, PP cause, battle outcome
or manual fallback. In a real run, a failure is conservatively rejected.
No protected private ROM/save/savestate or emulator is staged/read/executed,
and no upstream approved or review-pending head is changed. Formal
native 0/20 (0%), production 0%, old unmatched PP causes 0/2.
