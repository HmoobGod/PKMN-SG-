# Original actor0 PP candidate: Main-clear lease cannot rearm without new emitter

This **public source-only research** draft follows independently
Claude-APPROVED PR49 at exact
`fcd708663f85ce198af4913925729fe2d7224c64`.
It does NOT modify that approved head or any protected game file.

## Original attribution defect

The older `verify_exact_actor_epoch.correlate()` already rejected
PP after a Main-clear edge **until** a recorded Main-set edge.
But it left the previous actor0 `active` candidate in memory.
When Main cleared and subsequently set, the verifier could accept
a PP writer into the **old preclear player request**, even without
observing a new original actor0 move emitter. This is a false
same-request provenance claim and directly affects research into
two historically unmatched PP submissions.

The newer independent `verify_exact_joint_player_terminal.py`
had already made this correction, but the original actor-epoch
triage tool still needed its own lifecycle fix.

## Changes

- On observed **Main battle bit1 clear**, append the active old
  actor0 candidate as unproven and immediately set `active=None`.
- On subsequent **Main bit1 set**, permit a NEW original actor0
  emitter, but never resurrect the earlier candidate.
- Distinguish Main **bit0-only** noise from actual Main
  `inBattle` bit1 transitions: a bit0 change alone must neither
  cancel nor rearm a request.
- PP writer without a fresh original owner0 candidate must fail
  closed with the existing orphan-writer gate.
- No change to player0 action or enemy/NPC controller code,
  candidate output schema, original opcode PCs or verified
  private-file attest mode.

New tests cover two real-looking original actor0 submissions
separated by Main clear/set, a stale writer without new emitter
(rejected), a fresh post-reentry emitter (new separate candidate),
postclear writer without reentry (rejected), Main bit0-only change
(not a lifecycle edge), no PP debit being unproven cancellation,
and manual marker not certifying fallback. The dedicated public
CI runs original outcome and actor epoch tests, using no ROM,
save, emulator, private trace or guest execution.

This is not a production or real modified-ROM gameplay fix.
An original Main set does not prove a native request epoch,
and an unmatched PP writer does not prove a cancellation.
The two historical PP-less outcomes remain unresolved.

Native modified-ROM formal acceptance **0/20 (0%)**,
production Smart Auto-Battle **0%**,
unmatched PP causes resolved **0/2**.
Keep draft/unmerged pending exact-head CI and **fresh independent
Claude exact-head source/test/security** review. PR49 approval
does not transfer to this new candidate.
