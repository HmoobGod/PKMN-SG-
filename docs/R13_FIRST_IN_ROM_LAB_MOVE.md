# 16266R13 — first original native-accepted *in-ROM* player move (fixture-only laboratory)

**Status: first ROM-resident automatic action experimentally verified, NOT a general playable auto-battle build.** No Current ROM/save changed and no new Current/Android promotion authorized. The independent combined 16264/16265 installed-hook review remains outstanding.

## Why this is a different milestone from R10/R12

In R10/R12 the real isolated C Smart AI scorer ran **outside the ROM**, and a host test pressed buttons at the original move menu. In R13 the original experimental 16266 ROM's **existing compiled in-ROM scorer** returned diagnostic status 4, with cursor slot 1, then a new *fixture-locked* in-ROM guard allowed its own original native **auto preflight** path to proceed. **No host move-menu input** occurred after copying the player request. The original native game submitted a move command and committed it.

**Two independent native emulator runs** from the private R11 fresh-normal-save wild pre-controller states A and B:

| Evidence point | Fixture A | Fixture B |
|---|---|---|
| Original player/foe installers in same battle | 1 + 1 | 1 + 1 |
| Completed original player copy | 44/44 original stores | 44/44 original stores |
| Original pending bit0 after completed copy | 23 guest instructions later | 23 guest instructions later |
| Original in-ROM C ranker diagnostic | status 4, cursor slot1 | status 4, cursor slot1 |
| R13 fixture guard | one positive | one positive |
| Original player-native auto entry | once | once |
| Original player emitter | subcommand 10, payload **257** | subcommand 10, payload **257** |
| Original native reply | 6 bytes, header0x0A20, payload257 | same |
| Original player completion | pending bit0 cleared | pending bit0 cleared |
| Native restriction result | **0, accepted** | **0, accepted** |
| Original commit markers | slot1 → move157 → target1 | same |
| Host move-menu buttons | **0** | **0** |

A and B have separate private pre-controller savestates SHA256 `4157e7c910d9a55a1f19484c4a2daf6eae9707d52ecff3083b9adff3d08d9085` / `534a4b71dec2c5adff9b6a76639ac426469645ef44a64268fd713a08f0546bf8` and original native-controller witnesses from R11. Emulator and original game are unchanged; only the disposable candidate ROM differs.

**Negative real-emulator control:** Change one of the 44 expected request data bytes in the PRIVATE lab cave, leaving the rest of ROM identical. The guard returns zero, makes **no player native auto call or player emitter**, and the original **manual move menu remains active**. Opponent's original AI continues normally. This distinguishes genuine guarded selection from a forced button press. The first R13 iteration accidentally jumped back to the diagnostic wrapper, producing a repeated-callback loop; it was **discarded** before any claim. This corrected version reaches the original preflight entry and passes the normal original reply/acceptance path.

## Exact source design and privacy

New **research-only** source files:

- `research/r13_fixture_wrapper.s`: small Thumb ARM7TDMI wrapper replacement in the existing experimental hook cave at guest address `0x09F20000` (108 bytes). Calls the unchanged in-ROM C scorer, then on diagnostic status4 checks the optional fixture guard, dispatches the **existing original player-auto preflight** at `0x09F1F001` only if the guard says yes, and falls back to original manual setup otherwise. On any other diagnostic result the prior native path remains.
- `research/r13_fixture_gate.c`: tightly scoped checks for wild flags4/count2, player/foe class and original completion pointers, player pending bit, own selected cursor, absence/positions, original restriction cache/Disable/Encore/repeat exclusions, all four own live moves and PP, and **byte-for-byte exact matching** of one previously verified player request. Only after all checks pass does it write original actor0 automatic move-slot byte 1. It does not read hidden opponent HP, move, PP, item or ability fields.
- `tools/build_private_r13_lab.py`: accepts **only** the SHA-pinned experimental16266 ROM and a **private 44-byte request** with SHA `46a2425f06b61f66a71f361fa96241c01f73268933fbb0f6fa6264b99086adeb`. The raw 44 bytes are **NOT** committed to the public repository. Generates temporary compile header, assembles exact ARM Thumb cave overlays, enforces FF space, and writes a separate 32 MB private experimental ROM plus a tiny `.ips32` patch and manifest. Never overwrites its input ROM or the user's Current ROM/save.
- `tools/probe_private_r13_in_rom.py`: original SHA-pinned alternative Linux mGBA emulator, disposable ROM/save copies, original R11 pre-installer state, exact player copy and pending observations, then **14 more frames with key input zero** to witness original in-ROM auto emitter, reply, restriction, commit.
- `tools/trace_r13_candidate.c`, `tools/verify_private_r13_in_rom.py`, `tools/test_private_r13_in_rom.py`: original PC/register and own reply read-only observations, fail-closed offline trace consistency, and public synthetic adverse tests.

The candidate private fixture ROM SHA256: `70b0f846f8685cc09719476a166621289a5e7d47707695b5de9dc7f3e1bfde05`. Its only differences from preserved experimental16266 ROM are **510 changed bytes in two reserved source-wrapper/cave ranges**. The original Current ROM SHA remains `7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32`, save SHA `8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4`; their hashes must be checked again before delivery. The candidate is **not safe as a normal gameplay ROM**.

## Nonclaims and next work

- **R13 verified:** 2/2 *fixture-locked* first ROM-resident player automatic moves accepted by the original native game. This is a separate experimental indicator from the project's original **formal 0/20 general in-ROM automatic-battle acceptance tests** (none has been certified). It does **not** mean 2/20 and does not constitute a complete battle.
- **Not verified:** general battle-session owner authority, robust one-use epoch across repeated/replaced requests, normal random wild encounter legality, legal targets for all move effects, Choice-item/trait and other locks, rejection and cancellation recovery, trainer doubles/partner modes, Android/fast-forward, stack/IRQ safety.
- The source-level fixture condition is not a positive engine-owned permission certificate. A later battle with identical game-request bytes and own state could hypothetically activate the same guard. **Do not promote this lab ROM to Current or call it a playable auto mod.** Keep manual controls, no automatic items, capture or Master Ball, never edit enemy/NPC partner AI.
- Next priority: replace the private fixed fixture with a **general engine-owned request lease and full fail-closed original move/target/legal restriction proof**, get independent installed-hook review, verify exactly-once normal and rejected choices, then test and certify the formal 20+ native scenarios including trainer doubles, partner exclusion and Android.

**Source CI executes ONLY public synthetic verification, strict C syntax, and source boundaries. Actual original ROM/save/emulator replay is private and must not be claimed as public CI coverage.**