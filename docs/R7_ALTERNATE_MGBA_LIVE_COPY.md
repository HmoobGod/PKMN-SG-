# Revision 16266R7 — First completed native actor-0 request-copy observation

**Nature of work:** Actual emulator execution with original experimental16266 game code, replaying **one manual** confirmation from a previously preserved battle savestate. Source-only host research scripts, no ROM hook or gameplay patch. **Native automatic acceptance remains 0/20.** Do not enable automatic moves.

## What changed since R6

The user-supplied `soulgold-master.zip` already contains a Linux `tools/mgba/mgba-rom-test` executable (SHA256 `4304688a0b44007cca23c9e887af17c44530fd602ee3d1e57a232da397bec769`). This different mGBA build provides exported runtime functions, independent of missing pinned private `mgba_bridge_16187.so` / `libmgba.so.0.10`. A disposable copy of this exact ELF is changed only at the exact `DT_FLAGS_1` value to clear PIE, making it loadable under Python `ctypes`; it is never distributed as part of these source files. Loadable copy SHA256 `fef5effac26b13f53afe88511990fdf3049184402ca50faf9325d4daed7869c7`. This transformation is **host-only**, not a patch to the ROM.

The exact experimental16266 ROM SHA256 `6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de`, user save SHA256 `8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4`, and saved native battle state SHA256 `0dbcb91a26a3825357f14c18800708a28ef371db57e8fe907ecfbb9dc2c1c7ef` are loaded only from disposable copies, with exact hash checks.

**Important warning:** The alternative emulator reports that the savestate is for a different version of the game and emitted earlier DMA warnings. Loading the state without restoring Thumb prefetch gives a divergent manual payload of `256`. Restoring the original CPU Thumb prefetch (guarding the exact PC and prefetched instructions) reproduces the historical original native manual payload **257**. This is an exploratory emulator-specific fix, not a certification of compatibility or Android behavior.

## Positive read-only observation, one saved fixture

- Existing native saved menu reached at frame **14,244**, CPU PC `0x0806449E` in this emulator's Thumb convention.
- Ordinary **A button** pressed at frame **14,246** through the emulator's key-input API, causing the original engine's native emitter to produce **payload257, subcommand10, actor0**. No direct command writing and no Smart AI submission.
- Original actor0/direction0 44-byte buffer-A request entered at original code `0x0806B370`, then 44 original byte-store instructions at `0x0806B3BE` executed in sequential order 0..43, then reached original candidate postloop `0x0806B3C6` at frame **14,369**.
- The original source buffer, source buffer after looping, observed store values, and destination buffer after looping match byte-for-byte (44 bytes, opcode19) at player request buffers `0x0201CF14` -> `0x0201BF14`.
- Request SHA256 **`b92746c4fe980c1d9b05da0eddbff8a6765524390a67fd6f97950b6a41b2cf24`** matches the next actor0 request hash in the independently recorded prior 16266R3 manual `confirm` report.
- **New timing observation:** actor0 pending bit0 was *clear* at both original copier entry and postloop; **23 native guest instruction steps later**, within frame14,369 at emulator CPU PC `0x080D4CA4`, the original engine sets pending word to1 with request opcode19. A lease must not assume pending bit was already set at the copy boundary.

These observations establish **one native completed original request copy plus a subsequent pending transition**, on an alternative host emulator. They do **not** establish exclusive player ownership or native move/target legality, and do not show a single automatic move/complete automatic battle. Historic original R3 entry-only observations must not be retroactively upgraded to completed-copy witnesses. The six-record historical body and original hash records are not modified.

## Reproduce (Linux only, exact inputs)

The research scripts under `tools/` require Python, a host C compiler, and the exact user-supplied local executable and game files; CI contains **none of those private binaries**:

```bash
python3 tools/probe_alternate_mgba_copy.py \
  --host /private/mgba-rom-test \
  --rom /private/SoulGold_16266_PENDING_CHOICE_EXPERIMENTAL.gba \
  --save /private/Pokemon-Soulgold.sav \
  --state /private/genuine_wild_hook.ss \
  --output /tmp/16266R7-live-copy-evidence.json

python3 tools/verify_alternate_mgba_copy.py /tmp/16266R7-live-copy-evidence.json
python3 tools/test_alternate_mgba_copy.py
```

All emulator filesystem inputs and the rewritten ELF are copied to a new temporary folder. The original input files are hashed at entry and never written by the tool. Output is created only if the requested report path does not exist. No user save/ROM/savestate/emulator binary is committed or bundled with the public research code.

**Verification:** the replay tool executed successfully to generate the positive report with SHA256 `1b18c16c452bca7fe5f7af60db5529c7d68ffba4088c0424294dc43a045e9099`. The offline validator PASSes that report, checks all four 44-byte records and exact frame/PC/pending invariants. Five public unit methods with per-field missing/changed, wrong order, malformed byte and fake opcode cases PASS. Both C sources pass strict C11 syntax warnings-as-errors; Python sources compile. Public CI checks only sources/synthetic data.

## Safe next milestones

1. Reproduce actor0 request-copy + pending event for other real fixtures (wild single, and later certified trainer double); isolate no-owner cases without reading restricted opponent data.
2. Bind the genuine postcopy/pending pair to the correct owning player controller, battle session, stale epoch invalidation and exact one-use request lease; prove ownership via original engine, not by assuming actor0 is player.
3. Prove every applicable move/target/PP/choice-item/ability-restriction condition without side-effecting native validation. Preserve original native rejections and held-B/manual operation.
4. Only after safety tests and Claude independent review, connect an automatic actor0 move submission in disposable build and evaluate 20 native automatic acceptance cases; final Android tests and Current promotion come after.

No changes to `src/`, `include/`, enemy or NPC-partner AI, manual gameplay, captures or in-battle items. No auto capture or Master Ball selection. Source checklist remains 100% within isolated scope; overall playable completion cannot yet be responsibly estimated.