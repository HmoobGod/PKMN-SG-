# 16266R9 — Two original accepted manual moves in an actual emulated battle

**Scope:** Two independent disposable replays of one pinned wild-single savestate, both using only **ordinary human A / LEFT+A controls**. Native original restriction and commit path reached without instrumented game-code changes. This is **not Smart AI auto battle** and is **not** a general move/target authorization certificate.

## What this changes from R8

R7 established a completed 44-byte player request (original copy and all 44 stores). R8 correlated the subsequent original pending-bit transition 23 guest instruction steps later with the observed actor-0 controller signature and the user's own four move IDs and PP.

R9 continues from that same pending state to the original player menu at **frame 14373**. For each replay it allows the game to perform an original manual choice and records **only player actor-0 original instruction markers**, rather than calling the validator as a diagnostic or writing an action buffer:

| Original event | PC | Slot 1: A | Slot 0: LEFT, release, A |
|---|---|---|---|
| Original native command10 emitter | 0x0806BD80 | frame14375; payload257 | frame14377; payload256 |
| Native six-byte buffer-B reply entry | 0x0806B370 | 0x0A20, payload257 | 0x0A20, payload256 |
| Native completion, pending bit cleared | 0x0806261C | frame14375 | frame14377 |
| Original actor-0 consumer check | 0x080E5E5C | frame14376 | frame14378 |
| Original native legality-result boundary | 0x08094330 | **result0** | **result0** |
| Original slot commit | 0x0809435C | slot1 | slot0 |
| Original move commit | 0x08094374 | move ID157 | move ID325 |
| Original target commit *instruction reached* | 0x08094380 | yes | yes |

The game's move metadata for the two selected moves maps to opponent-target modes **6** and **1** respectively. The original selected command payload is consistent with target position1 in this wild single; the trace confirms a target-commit instruction occurred, **not** a general target resolver or target-value proof for all effects/modes.

Each result is scoped to **one accepted original MANUAL input** in the same saved encounter. The two tests are separate fresh emulator processes; they are not two turns of Smart AI. One additional original native consumer/callback for an opponent may run in later frames, but this observer records only actor0 and never reads an opponent's hidden move, PP, HP, item or ability memory.

## Reproduction with existing PRIVATE assets

```sh
python3 tools/probe_native_manual_legality.py --host /private/sg_mgba_mgba-rom-test \
  --rom /private/SoulGold_16266.gba --save /private/original.sav \
  --state /private/genuine_wild_hook.ss --slot 0 \
  --output /private/reports/slot0_manual.json
python3 tools/probe_native_manual_legality.py --host /private/sg_mgba_mgba-rom-test \
  --rom /private/SoulGold_16266.gba --save /private/original.sav \
  --state /private/genuine_wild_hook.ss --slot 1 \
  --output /private/reports/slot1_manual.json
python3 tools/verify_native_manual_legality.py /private/reports/slot0_manual.json
python3 tools/verify_native_manual_legality.py /private/reports/slot1_manual.json
python3 tools/test_native_manual_legality.py
```

The R9 host runner requires the already merged R7/R8 `tools/alternate_mgba_{trace_frames,capture_player_copy}.c` and `tools/verify_live_context.py` / `tools/verify_alternate_mgba_copy.py` modules. It pins the exact game/save/state/host hashes, creates disposable copies, and uses an exact-byte guarded host-only ELF `DT_FLAGS_1` adjustment for loading the prebuilt mGBA test executable as a shared host library. **No game ROM patch, user save write, game hook, or auto command.** The alternative emulator issues a **savestate version warning** and had initial DMA warnings; do not generalize this fixture to hardware/Android.

Private read-only results retained separately: slot0 report SHA256 `83697fffd2502fef9601fb9ab2e4f00d8d37ceb9faca6a45121437b5f6e96f26`, slot1 report SHA256 `4b9e3e4f5287a42ece7332de44aff98c1e7e9b2f01e0394b3f99321ab39c384e`. Do not commit raw personal save, ROM, savestate, private traces or original mGBA binaries publicly.

## Verification / boundaries

- Both pinned alternative-host original manual emulator replays **PASS**.
- Both reports pass `verify_native_manual_legality.py`, which chains the R8 copy+context verifier and demands exactly 8 actor0 original callbacks with reply payload equality, original native accept result0 and matching move/slot commits.
- Public synthetic unit suite **8 test methods PASS**, including both slot variants and fail-closed mutated order, PC, actor, pending phase, six-byte reply, rejected validator result, invalid move/PP and own negative restriction scenarios. Strict C11 syntax check passes. Public CI has no private emulator inputs.
- No native automatic Smart AI move or battle executed; **automatic acceptance 0/20**. Neither controller signature nor these manually accepted moves establish **exclusive player ownership, complete choice-item/trait legality, complete target legality, double/trainer/NPC-partner correctness, original action authorization or phone certification**.

## Next milestone: first safe automatic move (not yet implemented)

Original actor0 input authorization and fresh lease must be proven from an original engine-owned controller assignment and the currently opened request. Then an isolated move/target candidate must be checked against **complete** native move/target/item/trait/PP restrictions with no extra side-effecting validation calls or unauthorized foe hidden-field reads. After independent review, only a disposable auto-submission experiment may be performed. Preserve manual modes, enemy/NPC-partner AI, no in-battle items, no auto-capture/Master Ball, Current ROM/save compatibility, and disable auto trainer doubles until separately certified.