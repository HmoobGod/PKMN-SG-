# Private original-ROM controller move cursor: R4 research checkpoint

## Static ROM identity (read-only)

- Original player0 ChooseMove direct response handler (R3): `0x08065EB4`, reading the current cursor byte from the pointer at `0x02001E90` plus `0x106`.
- **New:** thumb `BL` at `0x08018620` calls `0x080183F0`. The return value `r0` is stored by `STRB r0,[r3]` at `0x0801862E` to `pointer+0x106` in the observed battler-0 path. Exact-ROM opcode and intermediate instructions are pinned in the R4 auditor.
- **New:** `0x08016FB6` writes the target cursor at `pointer+0x10A` via `STRB r0,[r3]`.
- Original pointer lifetime includes initialization from `0x080F8438` and clear from `0x080F85DA` in the observed runs.

## Native observations in the private environment

Both successful instrumented 8,000-frame replays used disposable ROM/save copies with full-save load checks and zero observed/requested battle inputs after detection. Each observed two original player0 move-slot stores (0->0), three target stores (one 0->1), and one pointer initialization plus clear. The original controller emitter showed two player0 Fight action-0 and two player0 Move action-10 responses, zero player0 action-2 Switch responses, with separate foe records excluded. All stores were validated against a private exact-ROM copy by the strict R4 reader. A third replay reached a battle introduction but no move submission; it is not a successful writer corroboration.

A previous R3 EWRAM series recorded slot 3 during repeated Taunt, but did **not** record the CPU writer at that time. Therefore it remains unresolved whether it was repeatedly recomputed as slot 3 or merely retained. It is not proven that `0x080183F0` is a smart scorer or that it was bypassed.

## Manual fallback and Switch safety (not certified)

Existing ROM has automatic action-2 Switch branch. No Switch in a bounded observed trace does not prove it cannot happen. Strict player-only wild singles, no automatic bag/capture, no forced switches, no enemy/NPC-partner AI changes, cancellation evidence, legality and a usable manual fallback remain hard requirements for eventual source-first integration. The old RAM-only zero-PP test is not a fallback proof. This R4 draft adds **observation**, not a ROM change or a runtime prevention mechanism.

## Native acceptance

**0/20 formal, 0% production.** No original-game patch acceptance or source-to-C build identity is established. No public repository or Drive uploads, merges, private ROM/save edits, installs or releases.
