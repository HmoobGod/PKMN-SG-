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
