# Source-LAB player0 wild-single: turn binding, foe identity and Struggle denial

Scope: one disposable upstream `src/battle_controller_player.c` native patch only. The user's Current game ROM, save, main branch and opponent/partner AI are **not** modified by this source-LAB proposal. Source checks and GNU ARM compilation do not constitute modified-ROM native gameplay acceptance.

## Problem addressed

The two-command `CONTROLLER_CHOOSEACTION` -> `CONTROLLER_CHOOSEMOVE` laboratory auto path previously staged a one-use slot under owner/party/moves/PP/volatiles, but did not also pin the upstream engine's current battle-turn counter. A stale choose-move request that crosses a turn boundary should not reuse an earlier authorization. It also did not explicitly bind the opponent's party slot and all three opponent types. Finally, custom move lists could theoretically contain `MOVE_STRUGGLE`, which is not a certified automatic path.

## Changes

- At staging, **read only** the upstream `gBattleTurnCounter` and record it alongside the frozen move slot. At consumption, require the same counter, then recheck it after the original `CheckMoveLimitations(..., MOVE_LIMITATIONS_ALL)` call. An advanced or changed turn cancels automatic reply and falls through to the native manual chooser. This counter is a conservative *turn continuity guard*, **not** an authenticated per-request engine epoch. It cannot prove a request/reply ownership relationship by itself.
- Bind the original foe's `gBattlerPartyIndexes[foe]` and all three `gBattleMons[foe].types[]` entries to prevent stale targeting across an opponent identity/type change. Combined with the existing opponent species, HP, status, ability and position snapshots, any mismatch invalidates the reply.
- Explicitly reject `MOVE_STRUGGLE` alongside `MOVE_NONE` and zero PP at both the speculative action preflight and final move slot check. Engine-required Struggle stays outside the auto path.
- Preserve original player0 wild-single ownership and live request, original `CONTROLLER_CHOOSEMOVE` command, one-use lease consumption, dynamic move legality check **only on final reply**, target validation, cancellation on unrelated controller commands, and manual fallback. No automatic bag/capture/forced switching, opponent or NPC-partner AI paths.

## Evidence and verification constraints

Input is pinned upstream source `src/battle_controller_player.c` SHA256 `deb649e441dd28909ade7053119b4af29450c9686e43000f319149d44c43e594`. The diff must apply to **only that file** in a disposable copy. All source tests are synthetic/static, not original modified-ROM CPU tests. A successful ARM build is a build-only laboratory check.

The authentic separate modified test ROM SHA256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44` and pinned original mGBA guest execution are still needed before any production hook can be certified. Native outcome decision PC, full unattended battle result/overworld exit, two PP-unmatched submissions, full dynamic legality, exact per-request engine lease, forced switch, Struggle, doubles and trainer fights remain unapproved. Formal native acceptance stays 0/20.

## Next steps

Check exact-head Source CI and disposable GNU ARM job. With the exact private modified-ROM image, run a single continuous original actor0/PP/Main CPU trace on the archived second/third natural wild fixtures, determine the original outcome decision store/branch PC, classify each unmatched PP writer with exact instructions, verify no-input safe field return and original manual fallback, then pursue independent review and the 20 real gameplay acceptance cases before promotion.
