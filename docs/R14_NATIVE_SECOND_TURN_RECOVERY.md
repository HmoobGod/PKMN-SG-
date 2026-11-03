# 16266R14 — Natural second-turn denial and usable manual recovery after first in-ROM Smart AI action

**Verified November 3, 2026. Research-only, not daily-play or general autoplay authorization.** This R14 work extends the existing **unchanged 16266R13 fixture-locked private lab ROM**. No new gameplay ROM/IPS build, no baseline game source changes, no Current ROM or save writes.

## Why this matters

R13 proved the first ROM-resident automatic move in two ordinary fresh-wild fixtures. The R13 gate is not engine-owned permission; it approves exactly one previously observed 44-byte request when player PP and other fields match. Until R14, we had **not** verified what happened to the **NEXT** original player move request in that same battle. An accidental second automatic submission or broken fallback would make the R13 test unsafe even for its limited scope.

R14 followed the **same running original engine** with the same disposable private R13 ROM, the same original save, and the two independent naturally generated R11 precontroller states. After the first original actor0 auto subcommand10/payload257 completed and its native restriction result0/slot1/move157/target1 were accepted, the host sent **NO** battle/menu input and stepped until the original native copier generated another actor0 opcode19 request.

| Native evidence | Fresh fixture A | Fresh fixture B |
| --- | --- | --- |
| Original player/foe installer | Original R13 pass | Original R13 pass |
| First R13 in-ROM player auto move | One accepted slot1/move157 | One accepted slot1/move157 |
| Initial player PP before action | `[20,10,10,20]` | `[20,10,10,20]` |
| Next naturally generated player request frame | **3570** | **3586** |
| Full original second native copier stores | **44/44** | **44/44** |
| Original pending-bit activation after new copy | **23 guest instructions** | **23 guest instructions** |
| Next live/player-request move IDs | `[325,157,92,269]` | same |
| Next live PP | **`[20,9,10,20]`** | same |
| Next request SHA256 | `b92746c4fe980c1d9b05da0eddbff8a6765524390a67fd6f97950b6a41b2cf24` | same |
| R13 private guard on second request | **Denied (r0=0)** | **Denied (r0=0)** |
| Second-turn in-ROM player auto emit | **0** | **0** |
| Original opponent native command path | Observed | Observed |
| Original manual player menu | Opened, no host button before it | Opened, no host button before it |
| Human-equivalent A *after manual menu* | Normal player cmd257, reply, restriction0, slot/move/target commits | Same |

The second request is **different** from the fixture-locked R13 first request (`46a2425f06b61f66a71f361fa96241c01f73268933fbb0f6fa6264b99086adeb`), including the PP decrement. The second-request hash alone is not an engine-owned nonce/epoch. The guard's denial is valid for these two historical states, not for all future identical requests.

## Reproducible source and verification

- `tools/trace_second_request.c`: bounded read-only host observer; stops **before** next original player copy, guard, emitter or manual chooser. Does not write game RAM, program counter, ROM, save or inputs.
- `tools/probe_private_r14_second_turn.py`: uses R13's exact original emulation protocol, two original precontroller states and SHA-pinned fixture-only candidate; executes first ROM-auto move, watches second original 44-byte copy and pending transition, checks guard0/manual fallback, and **only then** sends one ordinary A for a human-equivalent manual confirmation. Reports first R13 native-event timeline and independent second native copied bytes, SHA, store indices, denial events and manual reply/commit sequence. Runs only against private inputs.
- `tools/verify_private_r14_second_turn.py`: defaults to exact historical request SHA, validates original R13 first-turn report with existing `verify_private_r13_in_rom.verify_positive`, verifies all 44 byte stores/copy identities, timing, PP drift, *no* second automatic player emitter/acceptance, original opponent and manual result paths, and rejects overclaims. It also has a clearly labeled synthetic-test-only mode which cannot establish live evidence.
- `tools/test_private_r14_second_turn.py`: **12 synthetic unit tests**, including many individual changed inputs, duplicated/early second emissions, broken native reply/completion, wrong target/slot, misclassified manual as auto, missing manual menu and false general-autoplay claims. Public CI does **not** execute the private ROM, save, states or host binary.

Private full reports (not committed to GitHub):

- Fixture A R14 second-turn report SHA256: `b82a7942f7c087bd096bacc8d535fec568a39db6c3c6357ab959781f8007280a`.
- Fixture B R14 second-turn report SHA256: `4771f0686d20a554066dbe0e787f90c4ab9c7f23d5ee95c9751ab9f61c3b21ed`.

## What R14 DOES NOT establish

**No new automatic action feature was implemented in the ROM.** Only the unchanged R13 private fixed-request LAB ROM was exercised more deeply. Both normal second turns required a **manual** confirmation; the overall feature goal is fully automatic battle, not this lab fallback. This result does not solve an engine-issued one-use request epoch, guaranteed owner authorization, choice-item/trait/effect-specific move and target legality, cancellation/rejection recovery, trainer doubles, partner exclusions, Android/speed-up, or a complete battle. No formal 20-scenario general auto acceptance has passed (**0/20**). No recommendation to install R13 or any experimental build for ordinary gameplay. Source checklist completion remains an isolated source-only measure, **not overall playable completion**.

## Next engineering target

Implement and verify an engine-derived **one-use actor0 request grant** bound to original controller installation and the later pending transition, invalidated by original completion/cancellation/replacement and independent of identical 44-byte payload equality. Keep fail-closed on unsupported legality/target/Choice/trait conditions. Require independent installed-hook review and multi-turn native acceptance before any Current ROM promotion. Preserve manual mode, current save, original opponent/NPC-partner AI, no automatic items/capture/Master Ball.