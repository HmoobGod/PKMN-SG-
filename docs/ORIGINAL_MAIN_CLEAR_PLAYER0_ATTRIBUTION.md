# Original exact-ROM player0 evidence: Main-clear and reentry attribution gate

New independent source-only research draft on unchanged
`source-first/rom-identity` at
`655d2430c5891c12bbf4bc526b9f98f1468d433b`. This is
**not** a gameplay patch, an emulator probe, or an authorization to
read or stage a commercial ROM/save. It adds fail-closed constraints to
the existing private-local *offline* joint CPU event verifier,
`tools/verify_exact_joint_player_terminal.py`. The verifier's
`attest` mode still requires complete owner-local SHA-pinned ROM/save
and opcode parity, and must never be run inside public CI with those
inputs. CI uses only handcrafted synthetic event dictionaries.

## Concrete attribution defect

The verifier already tracked the real original `gMain.inBattle` bit,
but the actor0-emitter branch trusted stale event `inbattle`, flags
and battler context even **after** a real Main-clear edge. A later
original PP writer PC (0x0809E6BA) and a plausible own PP byte delta
could also appear after that edge; these were previously eligible for
old actor0 attribution. Furthermore, a later Main set edge could
revive the old `active` candidate without observing a new original
actor0 emitter/request. This is a source-evidence false correlation
risk, not proof of a real game bug.

## Narrow fail-closed correction

- Reject new actor0 emitter *claims* while authenticated
  `Main.inBattle` is clear, even if stale event fields still show
  wild-single player context.
- Reject labeling an original PP writer as battle-owned when Main is
  clear, when guest `inbattle` is false or when original wild-single
  flags/battler count do not agree. A matching opcode PC and decrement
  are not enough.
- When the original Main bit clears, append the existing candidate to
  the historical candidate report and reset the candidate to NONE.
  A later Main set edge cannot re-arm that actor0 candidate; a newly
  observed original actor0 emitter is required for any later
  attribution.

The four added synthetic regression cases cover a postclear stale
actor0 emitter, postclear original PP writer with stale battle flags,
wrong live battle state at a genuine writer PC, and a real Main
clear/reentry where the second PP writer must **not** be ascribed to
the first epoch. Existing valid action/PP/callback chronologies should
still pass the Source CI suite. The logic is reporting-only and writes
NO guest ROM/RAM or battle controller hooks.

## Scope and evidence

This check strengthens the evaluation of an eventual authorized
owner-local same-run original CPU replay. It does NOT prove actual
battle outcome, callback/overworld transition, dynamic move legality,
engine-owned one-use request epoch, cancellation reason, or safe
manual fallback. No opponent/NPC partner AI, bag/capture, uncertified
doubles, protected Current ROM/save, `main`, or `source-first`
is changed. The older source-only PR48 player0 proposal/target patch
is separate and unchanged.

Formal actual-game native acceptance: **0/20 (0%)**.
Production promotion: **0% certified**.
Historical PP-unmatched submissions classified: **0/2**.
Keep DRAFT/unmerged, require new exact-head independent Claude review
and completed Source CI.
