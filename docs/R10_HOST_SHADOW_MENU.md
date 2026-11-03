# 16266R10 — Original Smart AI ranker chooses a host-driven move in the real emulator

**Purpose:** Establish a single, exact-fixture **Smart AI decision → original move menu → original native accept** path without modifying or enabling a game ROM hook. This is a **HOST-ONLY scripted input experiment**, not in-ROM Smart AI, a complete battle, full move/target legality or player-ownership certification.

## Source provenance

The test compiles the *unchanged* repository `src/ranker_workspace.c` with the corresponding original `src/sg_action_gate.c`, `src/sg_baseline_mode_guard.c`, `src/sg_public_types.c` and repository `include/` headers. Local copies were checked against GitHub main at the exact Git blob SHA-1 values, with no source rewrite. `tools/shadow_ranker.c` is a **standalone laboratory caller**. It supplies a bounded public observation of actor0, a single present enemy, and four **player-owned known move IDs, PP and original ROM move metadata**. It does not inspect the opponent's hidden HP, moves, PP, item, ability or reserve party.

The candidate mask is limited to slots **0 and 1 only**, because these were **separately witnessed as native-accepted HUMAN menu choices** in R9's *same saved wild encounter*. This historical mask is **not an engine legality mask or a permission token for future turns**; no other move, target or battle mode is included. If the exact own four-move/PP values, negative restriction mask, controller signature, save/ROM/state hashes or public wild-single context drift, the host trial aborts.

## Reproduced live emulator trials

Both are fresh, disposable alternative-Linux-mGBA processes pinned to the same original ROM, save, state and host hashes as R9. The original save, Current ROM and experimental16266 ROM are never modified. An earlier scripted ordinary A press advances to the saved next-turn move selection; after the same completed player request, 44 original byte stores and native pending transition, the unchanged ranker chooses a slot. The host then scripts ordinary buttons **inside the emulator** (not a native emitter call):

| Allowed historical manual slots | Scorer proposal | Host menu buttons | Original native result |
|---|---|---|---|
| 0, 1 | slot1 / move157 / target1 | A | restriction result0, original slot/move/target commit reached |
| 0 only | slot0 / move325 / target1 | LEFT, release, A | restriction result0, original slot/move/target commit reached |

The scorer selects slot1 when both prior-manually-accepted attacks are present (move157 base power75, accuracy100; move325 base power60, known always-hit). When slot1 is excluded by the explicit historical **test mask**, it selects slot0. The exclude mask is a laboratory exercise, **not** a newly observed game-side Disable/Choice status or authentic change in the Pokémon's PP.

Each replay passes `tools/verify_shadow_menu.py`: original copied request and pending/context evidence, the ranker's move and target, exact original emitted command10 payload257 or256, matching native six-byte reply, completion, original restriction return0, and original three commit instruction markers. The old R9 unmodified manual baseline still passes separately.

These are **two host-chosen, native-accepted MENU choices**, *not* two completed automatic battles and not in-ROM automatic native move submissions. The host made all ordinary button inputs; the original engine still performed the emitter and restriction checks. **Native in-ROM automatic acceptance: 0/20.** General or exclusive player ownership certificates: 0. Full target/held-item/trait legality certificates: 0. Overall playable completion remains unestimated.

## Run

```sh
python3 tools/test_shadow_menu.py
# Requires private pinned inputs, available to the user but not in public CI:
python3 tools/probe_shadow_menu.py --host /private/sg_mgba_mgba-rom-test \
  --rom /private/SoulGold_16266.gba --save /private/original.sav \
  --state /private/genuine_wild_hook.ss --accepted-mask 3 \
  --output /private/reports/host_shadow_both.json
python3 tools/verify_shadow_menu.py /private/reports/host_shadow_both.json
```

Use `--accepted-mask 1` with a **different** output filename to test the excluded-slot branch. Source-only GitHub CI runs 10 public synthetic scorer/verifier unit methods with many negative mutations, C11 warnings-as-errors compilation via the test suite, and Python syntax. The private emulator binary, ROM/save/state and raw observation JSON are not public or committed.

## Important limits and next integration work

The fixture is a **saved, wild-single scene** with an emulator savestate game-version warning and prefetch-restoration workaround. The original player-controller installer was not observed in the same process. The source-only `sg_action_gate` treats the supplied historical test mask as its input and therefore does not prove full **native game-side** move legality, ownership or current request epoch identity. The game has not been patched and no Android/speed-up or wild/trainer-double autoplay was tested.

**Next:** capture a genuinely fresh original controller assignment and complete native owner/session evidence, implement a fail-closed engine-derived legality/target/Choice-lock policy (without side-effecting original validator calls or hidden foe reads), obtain independent installed-hook review, and only then try a native in-ROM automatic action on a disposable ROM. Preserve manual mode, user Current ROM/save, no automatic items/capture/Master Ball, no foe/NPC-partner AI changes, and no doubles/NPC-partner auto until separately certified.