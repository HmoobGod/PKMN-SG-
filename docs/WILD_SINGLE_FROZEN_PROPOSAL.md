# Wild-single fixed-slot proposal and dynamic move rejection (source LAB only)

**Scope:** This modification changes only the disposable upstream `src/battle_controller_player.c` via `source-first/wild-single-lab.patch`. It does NOT change the user's protected Current ROM/save or GitHub main, and does not install Smart Auto-Battle on the exact separate modified ROM.

## The safety issue

The earlier lab accepted a two-stage engine-owned action request, proposed `B_ACTION_USE_MOVE`, and, upon receiving `CONTROLLER_CHOOSEMOVE`, selected the first legal move *again*. Dynamic Disable, Choice, Encore, Imprison and other restrictions can change between these two stages. In that case, the lab might auto-pick a **different** legal move than originally proposed. Even though final move legality was checked, this reselection complicated one-use request ownership and cancellation analysis.

## Changes

1. Action preflight selects a conservatively targetable move slot, without calling the potentially stateful `CheckMoveLimitations` before the engine's ChooseMove request. The slot is stored as `sSourceFirstWildLease.proposedSlot` in the same single-use lease as owner, opponent, party index, the four moves, and their PP.
2. The staged lease additionally snapshots the player's species, HP, and major-status word. If these change before the move reply, the lease is consumed and no automatic reply is emitted.
3. The final reply **only** considers that same proposed slot and verifies `CheckMoveLimitations(..., MOVE_LIMITATIONS_ALL)`, current target validity, original move-list/PP, ownership and live request opcode. A now-illegal/disabled/Choiced/Encored/Imprisoned or invalid-target slot fails closed; the original manual move-selection path remains reachable. The selector does not switch to another legal slot.
4. Unrelated controller commands continue to invalidate the lease before original controller dispatch. Only player-owned wild-single actor 0 is eligible; no opponent/partner code, RNG, bag, capture, switching or fallback engine commands are modified by this patch.

## Regression evidence and limits

- `tools/test_wild_single_fixed_proposal.py`: 54 synthetic/static mutation tests, including first-slot restriction with an otherwise legal second slot, status/HP/species swap, repeated consumption, late cancel, wrong actor/target, and fallbacks.
- Previous `tools/test_wild_single_cancel_request.py`: 39 tests; old `test_wild_single_lab_contract.py`: 18 tests remain intact.
- Patch generated as a deterministic unified diff against exact upstream `battle_controller_player.c` with original SHA256 `deb649e441dd28909ade7053119b4af29450c9686e43000f319149d44c43e594`, applies as a single file; source CI and separate GNU ARM disposable-source build must pass on the exact new commit before treating compilation as verified.

These tests are **not** dynamic target/legality certification for the user's custom modified ROM. Real engine-owned request epochs, full battle outcome PC and terminal, two historical PP-unmatched auto submissions, trainer/doubles, forced switch, Struggle, save compatibility and full Smart AI scoring remain uncertified. Formal gameplay acceptance remains 0/20. No production ROM promotion without independent review and authenticated exact-ROM gameplay evidence.
