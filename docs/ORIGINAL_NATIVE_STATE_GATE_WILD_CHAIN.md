# Original exact customized-ROM native wild-battle terminal chain — 2026-11-12

Scope: **new live mGBA 0.10.5 CPU research**, not source-LAB integration or production certification. Original modified GBA test ROM SHA256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44`; protected Current ROM/save were independently rehashed unchanged. The private ROM/save/savestates remain off GitHub.

## Three independent disposable emulator processes

- **v3**: 4 complete original same-process player0+foe PP CPU deductions, followed by branch at `0x0808E31A` (Z=1, actual target `0x0808E364`) and original Main flag clear `0x0808E336` (2→0).
- **v4**: 4 complete original same-process sequences. Additional live breakpoint at `0x0808E374`, Z=1, actual target `0x0808E324`, followed by Main clear. One trailing partial PP sequence is excluded.
- **v5**: 3 complete same-process sequences with **original CPU state operand**: at `0x0808E370`, r5=`0x02001AB4`, live word `[r5]=0x00000004`; step loads r3=4. Original TST at `0x0808E372` compares r4=2 with r3=4, sets Z=1; `0x0808E374` BEQ steps to `0x0808E324`; `0x0808E336` then stores 0 to the original Main battle-active byte `0x03005A0D` (2→0).

All three processes used only menu confirmation to load SRAM, then **directional movement** through Route 44; no host battle move, item, capture, or trainer controls. Directional inputs could occur while a battle was ongoing and must not be mislabeled a proof of independent engine auto-selection. The v5 branch is a directly observed **battle-clear state gate**; the precise engine meaning of the bit 0x02 in that state word and a battle winner/outcome enum remain unclassified.

## Read-only verifier

`tools/verify_native_wild_chain.py` checks exact ROM hash recorded in trace, same-run monotonically ordered CPU events, actor0/foe PP decrement step, live load `[0x02001AB4]=4`, taken original branch with flag and target, and Main 2→0 store. It also rejects host battle action contamination, excludes trailing incomplete episodes, and keeps every cross-fixture PP assertion separate. `tools/test_verify_native_wild_chain.py` supplies **15 synthetic public tests**, wired to Source CI. Passing synthetic tests alone proves only the verifier behavior, not emulator gameplay.

Private evidence package (no ROM/SRAM/savestate), verified ZIP SHA256 `6c95e5f5d2bf152a49e88fd51256af9a31da69b54cd37b7b2d9a2780af80e6b7`, 23,320 bytes:
https://drive.google.com/file/d/1R-sy1bTxRRs1Cb3Vhb0JiR6lQQwLvSyZ/view

Includes exact per-process event JSON, console logs, captures scripts, test/source, result JSON, source & protected hash statements, and a CRC/SHA256-checked manifest. Original ROMs/saves/savestates **not** included.

**Acceptance status:** original native research was advanced, but engine-issued one-use player0 request/reply ownership, move legality, new source-LAB controller execution, historical PP unmatched submissions #1/#2 (0/2 separately UNCLASSIFIED), and safe fallback remain **unproven**. Formal native Smart Auto-Battle acceptance **0/20 = 0%**; production hybrid promotion **0%**. Do not add counts from different emulator processes as one continuous run.

## Merge boundaries

This research is isolated from canonical `source-first/rom-identity` baseline `655d2430` and Claude-approved draft PR #21 exact `1666676d`. It changes only docs/tools/source CI; no controller, enemy/NPC-partner, in-battle item/capture, doubles, Current ROM/save, or main branch. Hold any new PR as draft pending independent exact-head review, green CI and genuine native acceptance. The earlier Claude approval **does not transfer** to this new research head.
