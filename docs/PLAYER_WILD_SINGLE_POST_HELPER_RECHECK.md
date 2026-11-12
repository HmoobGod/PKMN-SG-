# Player wild-single source-LAB: state revalidation after engine helpers

**Scope:** pinned upstream disposable C source only. Does not modify Current ROM/save/main or enemy/NPC AI and does not authorize native promotion.

## Behavior

The original player-owned wild-single move reply is staged under a single-use token. The token is consumed before calling the engine's `CheckMoveLimitations` or target helpers. The refactor extracts one read-only `SourceFirstWildLeaseSnapshotMatches` predicate, reused at three points: before restrictions, immediately after engine limitations, and immediately after target legality and request-buffer checks. Every comparison includes original player0 ownership, active wild-single, turn, party index, frozen move slot, four move/PP values, species, HP, status, abilities and passives, held items, types and relevant volatile timers; plus the foe identity, party index, types, HP, status and ability.

If limitations or targeting modify those fields or invalidate the original pending command, **no automatic move reply is emitted**. The original manual controller continues. The original selected move is never silently replaced with a different slot. No item, capture, forced switch, enemy/NPC partner input, Struggle or uncertified doubles/trainer auto is enabled. Restrictions are checked once, only at final move phase.

## Validation

- Exact pinned upstream `src/battle_controller_player.c` SHA-256: `deb649e441dd28909ade7053119b4af29450c9686e43000f319149d44c43e594`.
- Patch applies cleanly with `git apply --check` and the applied result matches the generated source byte-for-byte.
- Earlier source tests: 39 + 54 + 65 + 40 = 198 focused regressions, all passing locally.
- New tests: synthetic mutation and mock state transitions before/after original legality and targeting. No modified-ROM native CPU replay performed.
- GNU ARM disposable source compilation is required before this batch can be described as *build verified*, and even after success is not real custom-ROM/save certification.

## Remaining blockers

Exact modified test ROM SHA-256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44` unavailable in this session. Original outcome decision/store PC, Main bit-clear instruction, complete unattended terminal and two PP-unmatched submissions are still unclassified. Engine-issued unique request epochs, cancellation, source/runtime parity, Android/save compatibility and 20/20 native acceptance also remain open. Source-LAB single-use staging does not constitute proof of genuine engine-issued request identity.
