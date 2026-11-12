# Same-run native CPU witness review — 2026-11-12

This is a **read-only archived evidence validation**, not a new mGBA native replay. Baseline source-first checkpoint: `655d2430c5891c12bbf4bc526b9f98f1468d433b`. Research branch is isolated; never merge into main or modify Current ROM/save.

## Re-validated original evidence
- Pinned original raw GDB STOP log SHA256 `be70245c59d03d567acf575b09d96574c496e29e7340364773c72234c5a4ec03`, indexed against exact original modified-ROM SHA256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44`.
- *Same raw log* includes two actor0 PP decrements and one actor1 PP decrement at `0x0809E6BA` with GDB before/after single-step, then the original Main flag clear `0x0808E336` (2→0 at RAM `0x03005A0D`), then four callback STOPs with Main=0.
- Original GDB RSP byte checksums, register values, effective RAM addresses, chronological order, and post-step PC were checked; 10/10 local focused *separate evidence-ZIP* verifier tests PASS. These ten tests are not part of this PR's source-check workflow. In this PR, the outcome-window suite has 7 tests and the pre-store branch scout has 11 tests (18/18 local PASS); both have now been added to .github/workflows/source-check.yml. Exact-head GitHub CI must be checked separately.
- Historical unmatched player PP submissions #1 and #2 remain **UNCLASSIFIED (0/2); this evidence is not joined to them.**
- Original pre-store outcome-decision branch, engine-issued one-use request epoch, actual source-LAB auto execution in the customized ROM, dynamic legality, and unattended multi-battle terminal **remain UNOBSERVED**. Formal native acceptance **0/20**, production hybrid promotion **0%**.

## Verified complete source + test + archived log package
[SameReplay Native Witness Verifier](https://drive.google.com/file/d/1ifoHiXh2tZ_xMOn2GQx9fxLd9wg4Fl_z/view), ZIP SHA256 `66a84be33136c380ea23270db9ae0025879e643861ec4d3c5c034ef9483e5dec`; 8,365 bytes, CRC/manifest PASS. It contains the complete verifier, ten regression tests, pinned archived logs/index and output JSON. No ROM, save, or savestate bytes.

## Strict next gate
The exact modified-ROM file is recovered and hash-verified; a matching private before-battle state and new original GDB CPU branch/flags/PC witnesses upstream of `0x0808E336`, then prove engine request+reply and PP/cancellation for each original fixture and uninterrupted field-to-next-wild. Never substitute protected Current ROM (SHA256 `7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32`). Protected SRAM SHA256 `8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4`. No changes to foe/NPC controllers, automatic items/capture, or uncertified doubles.

## Claude exact-head review R1–R5 response (subsequent research head)
- R1: Both `tools/test_exact_rom_outcome_window.py` and `tools/test_exact_rom_prestore_branch_scout.py` are explicitly run by `.github/workflows/source-check.yml`. Prior CI #43233435109 did NOT run either suite; only a newer exact-head run can validate the new CI gate.
- R2: Correct attribution: former outcome-window file had 5 methods, former scout 6. Revised files contain **7 and 11 methods** respectively, independently locally run **18/18 PASS**. The other **10/10** are separate archived GDB evidence-ZIP tests.
- R3: Outcome-window tests now truly reach classification/success, odd window rejection, store opcode rejection and read-only behavior using small synthetic buffers with independently matched synthetic SHA/ROM size/base.
- R4: Scout tests now cover branch-list output, exclusions of UDF/SWI, opcode mismatch and truncated window; no private original ROM in public tests.
- R5: Both read one immutable buffer before SHA and byte-window decode. Scout docstring flags literal-data/Thumb32 false candidates; its PP and acceptance fields are fixed report labels, not runtime inferences.
- Native confirmation remains limited to original earlier archived PP/Main observations and recovered exact-ROM startup/Continue. Static branch targets `0x0808E31A -> 0x0808E364` and `0x0808E322 -> 0x0808E35E` are **not** executed outcome-decision witnesses.
- PR stays draft/unmerged pending independent re-review and authentic same-execution native evidence. Main, protected Current ROM and SRAM, and enemy/NPC controller sources stay unchanged.
