# SoulGold — Disposable wild-single dynamic-state continuity gate

**Classification:** player-only SOURCE-LAB, not an installed custom ROM modification.

The latest lab baseline freezes a proposed player move slot and consumes a staging token once. This batch adds snapshots of the live rule-relevant owner and target state at the original `CONTROLLER_CHOOSEACTION` dispatch and rejects any change before `CONTROLLER_CHOOSEMOVE` is answered. Both commands still come from the original battle controller; no new item, capture, switch, enemy, or partner action is generated.

## Implementation

Only `src/battle_controller_player.c` in a disposable, SHA-pinned source checkout is modified by `source-first/wild-single-lab.patch`. The proposed slot remains frozen. The staging token now also binds to:

- Player ability (main and passive), all held-item slots and the compatibility item field, and three battle types.
- Volatile move-rule timers for Taunt, Disable, Encore, and Torment.
- The foe battler's species, HP, major status, and ability. The original foe identity and liveness guard remains required.

All comparisons are read-only and run as part of the existing one-use `SourceFirstConsumeWildLease` path, before any automatic reply. A modified value **denies** the auto answer and enters the engine's original manual path; it does not choose a different move. The engine's effective `CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL)` is still called **only** at final choose-move time, never during speculative first-phase selection. After it runs, original player0 wild-single ownership, Main battle liveness and the incoming choose-move command are re-checked before an auto response. The conservative extra comparisons can cause additional manual fallback, which is safer than an unauthorized auto answer.

No changes are made to opponent/NPC partner AI, random state, inventory, capture, forced switches, trainer/doubles, saved-game data, or the user's Current game. The patch does not identify a real modified-ROM request epoch; it is not a proof that cancellation or legality is complete in the user's custom game.

## Evidence and test semantics

- Source input: `Eemeliri/soulgold` at exact source revision `3f4d90aa8f8bc50054c817d7bd59fcdfcfb4933d`, original `src/battle_controller_player.c` SHA256 `deb649e441dd28909ade7053119b4af29450c9686e43000f319149d44c43e594`.
- `git apply --check` and `git apply` against that disposable file must succeed with byte-for-byte identity to the locally generated patch output.
- `tools/test_wild_single_dynamic_state.py` includes 65 new source-mutation and simulated request-continuity tests. Preserve previous tests `test_wild_single_fixed_proposal.py` (54) and `test_wild_single_cancel_request.py` (39).
- GitHub Source checks and GNU ARM disposable lab must both pass against the **same** final source head. Source-only tests, successful GNU ARM compilation, and mock models are not equivalent to an authentic modified-ROM emulator replay.

## Remaining blockers

Exact separate modified test ROM SHA256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44` plus its pinned mGBA host/savestate are not present in the current local inputs. The original native outcome decision/write/branch PC, full no-input battle ending, exact two PP-unmatched submissions from the historical second wild fixture, engine-owned single-use request epoch, and custom-ROM manual fallback remain unverified. Three past real natural wild fixtures are historical evidence, not new results. Formal native gameplay acceptance remains **0/20**, and the protected Current production integration remains **0%**. Never promote without independent review and all 20 authentic acceptance checks.
