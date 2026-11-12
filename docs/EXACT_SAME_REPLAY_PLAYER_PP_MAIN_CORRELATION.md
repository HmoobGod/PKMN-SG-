# Same-replay original player0/PP/Main native evidence — source-only observer

Date: 2026-11-12. This batch is **read-only research**. It installs NO hybrid
hook, makes NO player/foe controller, ROM or save change and does not claim
original battle-outcome decision, win/loss, dynamic legality, cancellation,
Android compatibility, or any formal production acceptance.

## Purpose and what this solves

Before this batch, original actor0 emit/reply/commit and PP writer evidence,
`gMain.inBattle` transition watch, and original callback1/callback2 evidence
could be collected using separate observers, potentially on separate emulator
replays. Those datasets are individually valuable but cannot prove a single
causal chain or explain two PP-undebited submissions from the earlier second
wild. Previous authentic third fixture proved original callback1 writer
`0x0808E33C` and callback2 writer `0x081AED58`, with stale battle flags4
while gMain.inBattle was cleared. Original outcome-decision instruction remains
unknown; no source offsets are used to invent it.

New `tools/trace_exact_joint_player_terminal.c` records **one continuous CPU
step sequence** using read-only mGBA core ABI with the *same frame/step counter*
for the following original events:

- Player0 action markers: native emitter `0x0806BD80`, buffer-B reply
  `0x0806B370`, controller completion `0x0806261C`, validator `0x08094330`,
  slot `0x0809435C`, move `0x08094374`, and opponent-target `0x08094380`.
- Original Main `inBattle` (bit1 of `0x03005A0D`) clear and set, callback1
  `0x030055D4`, callback2 `0x030055D8`, and phase byte `0x03005A0C`.
- All four player PP bytes at `0x02001EF1..0x02001EF4`, explicitly retaining
  original pre-write instruction PC. **Only** original native writer
  `0x0809E6BA` with matching `r1`, slot and one-point debit is an authentic
  PP writer candidate. Confounding PP-byte bulk/overlay copy writes are not
  credited as move PP.
- The original manual move-menu marker `0x0806449C` is recorded, and the
  offline unattended audit fails if visited.

Each event includes original frame, exact guest instruction step ordinal,
original pre-step ROM PC (unknown if outside supported ROM range), original
Thumb halfword (read, NOT guessed), stage (0 = pre-step control marker,
1 = post-step RAM mutation), r0..r4, flags, battlers, pending, Main inBattle,
and current callbacks. Event caps and instruction budgets fail closed: status
1 means full frame-window observation, not a battle finished. Status 2=step
budget, 3=overflow, 4=invalid inputs, 5=frame rollback; none certify evidence.
This is not an ARM-mode decoder; mGBA's observed guest PC convention is used
for known ROM-address markers only. Opcode parity is verified privately
against the exact modified-ROM bytes by the offline verifier.

`tools/verify_exact_joint_player_terminal.py` verifies private input identity,
strict original transcript format and chronology, read-only provenance,
consistent Main/callback/PP memory chain across the **same** replay, original
actor0-target markers, and PP writer attribution only after ordered native
reply/complete/validate/slot/move/target markers. It returns *candidate*
counts with permanent `*_certified=False` and zero production acceptance.
A submission without a corresponding writer remains **UNCLASSIFIED** rather
than classified as missed attack, canceled, blocked, or PP-free move.

## Required next *real* exact modified-ROM experiment (NOT executed here)

1. Reconcile latest development branch and Drive tracker before experiment.
   Verify disposable, separately authenticated modified ROM SHA256
   `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44`,
   original protected Current ROM SHA256
   `7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32`,
   original save SHA256
   `8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4`,
   and matching private pinned mGBA host + fixture. Never use an unrelated
   ROM/run to authorize claims about this ROM.
2. Run the **second independently constructed wild** from its original saved
   player pending state across all eight existing original player0
   submissions, six snapshot PP deductions, and its following Main/field
   transition. Use a sufficiently large CPU step budget and event cap; retain
   original private transcript, no host move-menu input, no guest mutations.
   If incomplete/overflow, increase bounded capacity or split the identical
   original saved state into reproducible runs; do NOT splice runs and claim
   one continuous CPU chain. Observe exact writer `0x0809E6BA` before
   attempting to classify either historical PP-unknown submission.
3. Run the **third separately authenticated wild** from pre-clear through
   original callback1 `0x0808E33C` and callback2 `0x081AED58` and compare its
   original Main bit-clear step. A Main clear and callbacks are sufficient
   only for an *engine handoff candidate*. Independently locate the actual
   original `gBattleOutcome` RAM address and original writer/branch PC with
   instruction/register/address provenance; determine the precise result type
   (victory/loss/flee/etc.) in the original engine before reporting terminal.
4. Apply separate original-engine restriction tests for live
   Disable/Encore/Choice/Imprison, target, one-use ownership, cancellation,
   forced switch, partner/doubles/trainer exclusions and manual fallback.
   No source-only witness or mock grants production permission. Retain
   auto-only preference while keeping safe manual fallback inaccessible only
   where gameplay is already certified; no automatic bag/capture/Master Ball.

## Validation and scope

`tools/test_exact_joint_player_terminal.c` uses a deterministic **fake**
mGBA-like core to exercise the exact same read-only observer code, a single
move event, original one-point PP writer, Main bit-clear, callback1 and
callback2 transition, rejection of event overflow, instruction-budget
exhaustion and invalid core. It does **not** execute game CPU. Existing
protected Current ROM has static original Thumb `0x700E` at native PP writer
PC `0x0809E6BA`, `0x6022` at callback1 writer PC `0x0808E33C` and `0x6058`
at callback2 writer PC `0x081AED58`, all *read-only*. Static instruction
bytes are not a new authentic runtime trace of the modified test ROM.

`tools/test_exact_joint_player_terminal.py` includes synthetic false-claim,
missed-event and ownership denial tests. Build this C source with strict C11
`-Wall -Wextra -Werror -pedantic`, run the fake-core executable, Python
`py_compile`, and all prior source checks in the exact-head GitHub workflow.
The source-LAB player chooser patch remains byte-for-byte unchanged, so
previous GNU ARM lab success applies solely to the previous exact patch; no
new ARM game artifact is claimed.

**Baseline remains:** three historical authentically triggered original
wild fixtures, 13 original player0 automatic move submissions across them,
2 old second-fixture PP-unmatched actions unclassified, formal native gameplay
acceptance 0/20 (0%) and protected Current ROM production integration 0%.
The exact modified ROM, pinned private mGBA host and original CPU pending
savestates are **not mounted** here, so no new native CPU/result observation
has been made by this source-only batch. Do not upload any ROM, save,
precontroller state, raw private guest transcript or emulator binary to
public GitHub or the development evidence archive.
