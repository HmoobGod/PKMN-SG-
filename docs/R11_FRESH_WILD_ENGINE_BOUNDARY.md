# 16266R11 — Clean-save wild controller installation, original 44-byte request and pending gate

**Development scope:** Original native instruction execution in a **disposable Linux mGBA host**, plus public source-only regression tools. This is neither an updated gameplay ROM nor an automatic battle. The normal user Current ROM and save are immutable inputs. The preserved gameplay experimental ROM remains revision **16266**.

## The limitation R11 resolves

R7–R10 used a savestate from **after** controller installation. Those reports could read controller signatures but could not witness the engine assigning that controller to the same battle. R11 boots from the **original save** with **no savestate loaded**; uses only the game's own title/Continue prompts and ordinary directional movement in grass; stops at original constructor entry `0x0806AD46`, before player/opponent controllers have been assigned. The host serializes that *pre-assignment* CPU/RAM state using the original mGBA core serializer into a **private-only** `.ss` for deterministic replay. The state is reloaded in a new instance of that same host and native controller installer entrypoints are observed before the 44-byte request.

The first attempt to save a preconstructor `.ss` through `mCoreSaveStateNamed` produced an all-zero invalid file that failed to load. **It was rejected and not used as evidence.** R11 saves raw mGBA core serialization with `_GBACoreSaveState` and verifies load/initial PC and initial controller table in an independent emulator process; the final snapshots have valid bytes and load successfully. No game memory or original save file is edited.

## Fresh supported wild mode vs excluded roaming encounter

The ROM source's `BATTLE_TYPE_IS_MASTER` is `1<<2`, and `BATTLE_TYPE_ROAMER` is `1<<10`:

- Supported candidate **ordinary wild singles**: `flags=0x4`, `battler_count=2`.
- Excluded **roaming Entei**: `flags=0x404`. A naturally reached Entei fled; the controller layout looked player/opponent, **but the extra roaming flag must cause fail-closed exclusion**. It is not evidence that roamer auto is safe.
- Trainer/doubles/partner/link modes are outside R11. No automatic move or automatic target selection is attempted.

## Two independent clean-save wild fixtures

| Native witness | Fixture A | Fixture B |
|---|---|---|
| Raw pre-assignment constructor frame | 3023 | 3257 |
| Native constructor address | `0x0806AD46` | `0x0806AD46` |
| Flags, count, initial controller kinds | `0x4`, 2, `[0,0]` | `0x4`, 2, `[0,0]` |
| Original actor-0 player installer entry | **once** | **once** |
| Original actor-1 opponent installer entry | **once** | **once** |
| Controller signatures after installation | player kind 1 / opponent kind 3 | player kind 1 / opponent kind 3 |
| First observed actor-0 opcode 19 copy frame | 3402 | 3478 |
| Original 44 byte stores/destination equality | **44/44** | **44/44** |
| Actor-0 original pending set after completed copy | **23 guest steps** | **23 guest steps** |
| Player's live moves = copied request moves | `[325,157,92,269]` | `[325,157,92,269]` |
| Automatic native moves accepted | **0** | **0** |

Both sessions use exact SHA-pinned experimental ROM, original save and the separate Linux mGBA host. No original controller installer/validator/emitter function was invoked as a fake read-only query; the emulator executed them naturally. Host input is used only to continue narration **before** the move request. The request observer *stops before* any move-menu selection. No hidden opponent move, HP, item or ability memory was read by the recorder.

The second fixture is not a re-run of the first preconstructor state; it comes from a separate normal cold-save encounter with a distinct saved state SHA. State A SHA-256 `4157e7c910d9a55a1f19484c4a2daf6eae9707d52ecff3083b9adff3d08d9085`, state B `534a4b71dec2c5adff9b6a76639ac426469645ef44a64268fd713a08f0546bf8`. Original save SHA-256 `8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4`. Current ROM SHA-256 `7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32`. Experimental ROM SHA-256 `6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de`.

## Public source-only reproducibility and tests

- `tools/stop_at_wild_ctor.c`: bounded, passive original constructor PC/flag/count observer, does not execute installers by injection.
- `tools/probe_fresh_wild_constructor.py`: exact-pinned original host/ROM/save; ordinary title/Continue/movement; captures a **private** original preinstaller state using the mGBA core serializer. Fresh wild spawns have random timing; a run can exit without a usable ordinary wild fixture, or reject a roaming/special encounter.
- `tools/wait_original_player.c`: bounded passive wait, counts actual installer entry executions and stops before actor-0 44-byte request copy.
- `tools/probe_fresh_wild_request.py`: reloads a matching private preconstructor state; pairs native player/opponent installers and the existing R7 44-store observer with original pending. No output until exact read-only checks pass.
- `tools/verify_fresh_wild_request.py`: offline consistency validation, **not** cryptographic proof the source JSON is authentic; verifies flags, ordering, state identities, move data, pending interval, and false auto claims.
- `tools/test_fresh_wild_request.py`: seven public unit-test methods, with many adversarial exclusion cases for roamer/trainer/doubles/partner modes, missing installers, mismatched original response and illegal authorization claims.

```bash
python3 tools/test_fresh_wild_request.py
# Private inputs kept outside the public repository:
python3 tools/probe_fresh_wild_constructor.py \
  --host /private/mgba-rom-test --rom /private/SoulGold_16266.gba \
  --save /private/original.sav \
  --output-state /private/fresh_precontroller.ss \
  --output-report /private/fresh_precontroller.json
python3 tools/probe_fresh_wild_request.py \
  --host /private/mgba-rom-test --rom /private/SoulGold_16266.gba \
  --save /private/original.sav --state /private/fresh_precontroller.ss \
  --pre-report /private/fresh_precontroller.json \
  --output /private/fresh_request.json
python3 tools/verify_fresh_wild_request.py \
  --pre-report /private/fresh_precontroller.json \
  --request-report /private/fresh_request.json
```

The public CI runs only synthetic, C syntax and source boundary checks. Private host, state, ROM and save files are NOT committed to the repo.

## Still blocked before in-ROM automatic action

Witnessing the game's original install of player kind1 in two exact wild fixtures is **not** a universal exclusive player ownership token; no persistent in-ROM request-epoch identifier has been installed. The original native post-copy pending transition is a necessary step but not positive action authorization by itself. The script has **not** certified complete choice-item/trait/Disable/Encore/repeat restrictions or every effect-specific target rule, and has not obtained independent review of combined earlier installed hooks.

To reach the first safe disposable in-ROM auto move: (1) bind a one-use request to the original controller installation/encounter and pending without modifying foe/partner AI; (2) prove a complete non-side-effecting legality/target policy or fail closed; (3) have independent review of the exact ROM hook/source and rejection recovery; (4) test only in a disposable ROM and then expand to natural wild and trainer doubles separately. Preserve manual mode, no auto items, capture or Master Ball, original save compatibility and Current ROM. **In-ROM automatic acceptance is still 0/20.**