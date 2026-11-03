# Revision 16266R12 — original live wild controller → host Smart AI → original native move acceptance

## What changed and why

R11 verified that the engine assigned the ordinary player/opponent battle controllers **in the same fresh wild encounter** that later produced the player move request. R10 verified that the unchanged isolated Smart AI ranker can drive the old *mid-battle* savestate's original move menu from the host. R12 joins these two source-tested behaviors with **two independent original-normal-save-derived pre-controller fixtures** and the original, unchanged experimental revision 16266 ROM.

In both trials, the test began **before** either original controller installer executed. Original installer entries for actor 0 (kind 1, player) and actor 1 (kind 3, opponent) were observed once each. The original opcode19, 44-byte actor0 request was copied through all 44 byte-store instructions; source/destination bytes matched. Its pending bit became set **23 guest instructions after** the copy. The test then reached the original player move menu, at which time the whole pending word was `3` (both battlers); only **bit0** is the player gate. No copied request itself was treated as authority.

Only after this request and player-context trace passed did a **separate host executable**, compiled from the nine exactly GitHub-pinned Smart AI C source/header blobs without changing their contents, choose an action. The test allowed the scorer to consider **only two move slots historically shown to be accepted manually in R9**. This is a **historical, synthetic test mask**, not a current full legal move mask, an in-ROM game permission flag or a real Disable/Encore/Choice item condition.

| Scoped evidence | Fresh wild A | Fresh wild B |
|---|---:|---:|
| Origin | original save, normal grass encounter | separate normal-save grass encounter |
| Pre-controller state SHA256 | `4157e7c910d9a55a1f19484c4a2daf6eae9707d52ecff3083b9adff3d08d9085` | `534a4b71dec2c5adff9b6a76639ac426469645ef44a64268fd713a08f0546bf8` |
| Original controller installers | actor0 once; actor1 once | actor0 once; actor1 once |
| Original completed copy frame, stores | 3402, 44/44 | 3478, 44/44 |
| Pending transition | +23 steps | +23 steps |
| Original move menu frame; pending word | 3406, `3` | 3482, `3` |
| Live own moves and PP | `[325,157,92,269]`, `[20,10,10,20]` | same |
| Historical **host-only** allowed test mask | slots 0+1 (`3`) | slot 0 only (`1`), *artificial exclusion* of slot1 |
| Unmodified C scorer proposal | slot1, move157, target1 | slot0, move325, target1 |
| Host original menu buttons | A | LEFT, release, A |
| Original native emitter subcmd10 / payload | 257 | 256 |
| Original native consumer restriction result | 0, accepted | 0, accepted |
| Original commit marker instructions | slot, move, target in order at frame 3409 | slot, move, target in order at frame 3487 |
| In-ROM Smart AI automatic acceptance | **0/20** | **0/20** |
| Private final report SHA256 | `249f7388752ad303e686268dbdf1b85613b8ff64c32fb9bef70e1e74854d726d` | `fc8c886a690c5243660b2ac738098d02e48cf6ab153f5385f9ba5ad90b83da59` |

The **game itself** performed the native reply, completion, restriction check, and commit after **host-simulated normal controller buttons**. The test never writes a battle command or modifies the game ROM. The observed target commit is an **instruction marker**, not comprehensive target validity across effects/modes. The host did not read foe moves/HP/PP/items/abilities; the original game may naturally do so while processing its turn.

## Reproduce with the pinned private data

The source files below are public; the raw private `.ss`/reports, exact 16266 ROM/save, and third-party mGBA ELF remain private/user-supplied. Source CI tests only synthetic data and C/Python compilation, not private native emulator execution.

```bash
python3 tools/test_fresh_shadow_menu.py
python3 tools/probe_r12_fresh_shadow_menu.py --host /private/mgba-rom-test --rom /private/experimental_16266.gba --save /private/original.sav --state /private/fixture_A_precontroller.ss --pre-report /private/fixture_A_precontroller.json --output /private/fresh_A_shadow.json --accepted-mask 3
python3 tools/probe_r12_fresh_shadow_menu.py --host /private/mgba-rom-test --rom /private/experimental_16266.gba --save /private/original.sav --state /private/fixture_B_precontroller.ss --pre-report /private/fixture_B_precontroller.json --output /private/fresh_B_shadow.json --accepted-mask 1
python3 tools/verify_fresh_shadow_menu.py --pre-report /private/fixture_A_precontroller.json --request-report /private/fixture_A_native_replay.json --shadow-report /private/fresh_A_shadow.json
```

`verify_fresh_shadow_menu.py` also accepts B's three reports and validates the original constructor→copier→pending→menu→native validation/commit sequence. Its **10 synthetic unit-test methods** cover malformed original identity, controller assignment, request copying, pending timing, source/destination move mismatch, missing/altered restrictions, wrong ranker slot/target, actor/reply/commit order, hidden foe fields and falsely claimed in-ROM permissions. A forged internally consistent JSON can still pass; this is not an authenticated runtime authority.

## What still blocks the first *in-ROM* automatic move

- Preserve a one-use **engine-owned player controller and current request** binding across asynchronous replacement/cancellation, rather than a host-only counter or copied request checksum.
- Establish complete original legal move/target permissions in an effect-, item-, ability- and mode-aware way, or reliably fail closed. A native **post-submission** rejection does not grant a safe *pre-submission* positive legality certificate. No extra side-effecting validator calls or hidden foe reads.
- Obtain independent review of the combined installed 16264/16265 hooks plus exactly-once original emitter/completion/rejection recovery path; then try any automatic submission **only on a disposable experimental ROM**, with original manual gameplay available and no automatic in-battle items/captures.
- Test natural wilds, trainer doubles/partners and Android/speed-up separately. **Neither wild acceptance nor NPC partner/doubles auto is certified** here.

**No playable ROM revision advanced; the original experimental ROM is still 16266, Current ROM/save are unchanged, and native in-ROM automatic battle acceptance remains 0/20.** The historically completed isolated-source checklist remains 100% only within its narrow source scope, not overall gameplay completion.