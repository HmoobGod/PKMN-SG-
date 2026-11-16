# Pokémon SoulGold — private exact-ROM dispatch/cursor research, R3

**Scope:** source-only gate and host-read-only analysis of a user-authorized disposable exact-ROM copy. Not a ROM patch, auto-planner integration, battle legality certification, or deployable release. No public game data.

## Exact ROM (conditional proof, not symbol linkage)

The source-side `sPlayerBufferCommands` command indices for `CONTROLLER_CHOOSEACTION` (17) and `CONTROLLER_CHOOSEMOVE` (19) align with a candidate ROM dispatch table at 0x08444508. The ROM table entries point to Thumb handlers at 0x08065E9C (action) and 0x08065EB4 (move). The action handler calls 0x080171B8 and completes. The helper contains an original Fight (`B_ACTION_USE_MOVE`, 0) response branch and also an action-2 Switch response branch; the latter is *capability*, not a witnessed automatic switch.

The move handler loads an extant slot-selection byte through a game battle pointer, rather than running a visible per-turn move-scoring loop in this handler. It calls the normal original engine emitter at 0x0806BD80, from BL 0x08065F28, with action 10 (`B_ACTION_EXEC_SCRIPT`), and then invokes original controller completion at 0x0806C2EC. In CPU store traces, original action-0 emitter LR 0x08017211 is followed by action-10 emitter LR 0x08065F2D. Both come from player battler 0 without emulated battle button input. Original PP writer candidate 0x0809E6BA follows.

### Independent local observations

- Three Fight->Move->PP host-only unverified joins across two old private replays, at frames 3194->3195->3306; 3994->3995->4002; 4129->4130->4137.
- ROM control-flow audit pins **16** exact instruction/data call-edge checks, including the action-0 emitter and *possible* action-2 switch branch. Each check must pass; false positives fail closed.
- In an older private EWRAM frame series, a byte reached through the ROM move-handler's pointer+0x106 read remained slot 3 during sampled frames 3700–6600, then 2 at 6700, then 1 at 6800–7100. This is compatible with repeated selection of a stored Taunt slot. It does NOT prove no upstream scoring or prove the cursor writer's origin; in later overwritten/out-of-context snapshots the pointer/byte fails the strict gate.
- The uploaded `soulgold-master` **source** normally initializes menus through `PlayerHandleChooseAction` and `PlayerHandleChooseMove`. The tested ROM direct-auto path differs. This comparison is useful lineage evidence but **not** a linked source-file/function identity because no matching exact-ROM ELF, MAP or reproducible build identity was available.

## Most important safety blockers

1. Identify who writes the slot at the pointer+0x106, its request epoch and legality basis. A repeat of slot 3 without re-evaluation plausibly explains ineffective Taunt; a scoring algorithm upstream remains unverified.
2. Reject unusable, disabled, zero-PP, immobile, or stale moves **before** emitting a one-use player-only action response; fail closed to the original manual UI, not an automatic Switch or forced Struggle. Existing ROM behavior does not prove this fallback.
3. Confirm full original engine move and target legality, request ownership and cancellation, with original CPU witnesses; do not treat emitter LR or PP write in isolation as certification.
4. The original ROM's action routine has a potential automatic Switch branch. It must be disabled or proven unreachable under the player's no-forced-switches rule in an exact-ROM-compatible integration. Do not change foe/NPC partner AI or introduce automatic items/capture or unproven doubles.
5. Obtain reproducible, exact private-ROM build linkage or a sufficiently authenticated function/patch map before attempting binary edits. The public source-first laboratory output is not byte-identical to the uploaded game.

## Tool inputs and privacy

Source-only tools accept externally provided `--private-rom`, `--private-owner-stores`, `--private-pp-trace`, and `--private-ewram-dir` and emit only redacted statistics. The archive contains NO ROM, save, memory dumps, screenshots, private trace records, RAM-edit diagnostics, emulator binary, or linked ELF. The original files are never opened by the build/tests, only by the separately authorized private audit when explicitly invoked.

All certification fields remain false. Formal original-game Smart Auto-Battle acceptance remains 0/20; production authorization remains false. No merges or releases.
