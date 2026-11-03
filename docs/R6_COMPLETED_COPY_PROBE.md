# 16266R6 — Paired original copier instruction witness (source-only)

**Source-only research.** No gameplay patch, ROM modification, automatic submission, enemy/NPC partner control, or new emulator replay is claimed. This is an instrumented **read-only observer** and a strict offline consistency validator, built from the 16266R5 instruction-path audit. It remains deliberately separate from `src/` and `include/`.

## What is now implemented

`tools/probe_completed_copy.py` can, when all SHA-pinned private components are present, observe the original game's non-link, actor-0 request copier in the same pinned saved battle fixture. It registers debugger PC breakpoints at **entry `0x0806B370`**, **store instruction `0x0806B3BE`**, and **post-loop branch `0x0806B3C6`**. It does not patch any original instruction. On a candidate 44-byte request, it snapshots entry registers and source data, then records each store-instruction encounter in order. At the original post-loop PC, it reads destination and source memory, records SP/LR and other relevant registers, and requires a coherent paired trace. The optional script drives only the same ordinary cancel/A-confirm buttons as earlier probes; it never calls a game command emitter.

`tools/verify_native_copy_pairs.py` is the offline fail-closed ledger checker. It checks five supplied file-hash identities; non-link actor0/direction0/44-byte opcode19 context; nonoverlapping bounded EWRAM pointers; original instruction PCs; strictly increasing debugger-hit sequence; exactly 44 sequential byte-store observations with matching source bytes, destination, SP and LR; final post-loop registers and source/destination contents; and refuses any claim that this proves ownership, move/target legality or automatic dispatch. The hit IDs are **host diagnostic counters**, never native engine epoch tokens.

`tools/test_native_copy_pairs.py` is a synthetic, ROM-free regression suite with **four passing unittest methods** and **37 named adversarial trace mutations that fail closed**. A duplicate request payload is not deduplicated; independent execution-path events must carry a monotonic observation order. No private ROM, save, savestate, debugger runtime or copied original code is published.

## Actual local evidence

- Pinned Current and experimental16266 game ROMs and preserved save have matching expected SHA-256 identities. The R5 original copier window is unchanged between those two ROMs.
- Python syntax validation and 4 synthetic test methods passed; all 37 adversarial trace mutations rejected.
- **NO real post-copy runtime execution has been obtained in R6**. The pinned private bridge `mgba_bridge_16187.so` and `libmgba.so.0.10` are absent. Consequently, observed completed-copy count remains **0**, authoritative player-owner certificates **0**, automatic Smart AI native acceptance **0/20**.
- This is a source implementation and CI exercise, **not** gameplay integration or certification. An error in debugger ABI, instruction-state timing, or callback re-entrancy may still be discovered when the optional private probe becomes runnable.

## When the exact private runtime is available

```bash
python3 tools/probe_completed_copy.py \
  --rom /private/SoulGold_16266.gba \
  --save /private/Soulgold.sav \
  --state /private/genuine_wild_hook.ss \
  --bridge /private/mgba_bridge_16187.so \
  --runtime /private/libmgba.so.0.10 \
  --case cancel \
  --output /private/reports/completed_copy_cancel.json
python3 tools/verify_native_copy_pairs.py /private/reports/completed_copy_cancel.json
```

The tool fails if the protected exact private paths do not match the pinned hashes, an invocation is incomplete, or the post-loop/byte-store record is inconsistent. It uses disposable ROM/save copies and does not overwrite the original source files; the resulting report is private because it includes short request payload snapshots.

## Required after this research

1. Execute and independently inspect the original debugger entry/store/post-loop trace; validate callback ABI, stack and IRQ behavior, link-path exclusion, destination writes and timeline. Repeat in natural singles and trainer doubles with correct player-only ownership. This script only covers the pinned actor0 saved fixture.
2. Prove player/session identity and unique current-request authority from the original engine. Neither a post-copy PC hit nor a host counter grants this.
3. Complete legal-move, effective choice lock, target/partner and stale-state certification without extra side-effecting native calls or hidden foe reads.
4. Retain human-confirmed preview and manual gameplay; only after independent reviews and actual native acceptance should a separate automatic emitter implementation be considered.

**Current:** experimental gameplay ROM16266, isolated-source checklist 100% defined, native automatic acceptance 0/20. Current ROM and save preserved. R6 is not a new playable ROM release.