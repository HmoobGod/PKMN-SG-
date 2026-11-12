# Original exact customized-ROM CPU wild-chain research — 2026-11-12

**Research only.** These scripts check archived CPU/GDB evidence for the exact customized ROM recorded as SHA256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44`. They **do not** run Smart Auto-Battle or certify any of the 20 formal production cases. The recorded ROM identity and post-run hash from a console are **attestations in the archive**, not an independent hash of a ROM file by this verifier. The original ROM/save hashes were checked separately during the emulator session; ROM, save and savestate files are not published.

## Three original captures, three verification modes

| Capture | Required original CPU stages, in order | Verified full episodes | Output mode |
|---|---|---:|---|
| v3 | actor0 and opponent PP deductions → `0x0808E31A` taken → Main `0x0808E336` clear | 4 | `v3-basic` (relaxed) |
| v4 | v3 stages → `0x0808E374` taken → Main clear | 4 | `v4-branch` (relaxed) |
| v5 | v4 with `0x0808E370` state load BEFORE `0x0808E374` taken → Main clear | 3 | `v5-full` (strict) |

The **v5** saved CPU log specifically records a read of `[r5=0x02001AB4] = 0x00000004`, loads `r3=4`, then `TST r4=2, r3=4` yields Z=1 and `0x0808E374` branches to `0x0808E324`. The original store at `0x0808E336` then records Main `2→0`. This is an authentic recorded **battle-clear control-flow condition**, **not** a classified outcome/winner enum or a licensed automatic player move submission. Never combine v3/v4/v5 counts as one continuous emulator process.

## Five independent Claude review repairs, R1–R5

- **R1 ordering:** Every *complete episode* must pass original CPU stages in strict order: **PP before first gate, first gate before state load, state load before terminal gate, terminal gate before Main clear** in `v5-full`. The relaxed v3 and v4 modes have proportionally fewer stages, but still check ordered presence. Misordered or duplicate gate events fail, including PP after first gate.
- **R2 process/run provenance:** A capture must include a `run` object with run ID, start marker, checked console SHA256 and source/provenance. Every event must carry the same run ID; a mixed/foreign run fails. Archived scripts v3/v4/v5 did **not** log OS process IDs originally, so `--normalize-legacy` adds a reproducible **post-hoc** run ID derived from the **original complete console SHA256**, without changing original CPU STOP fields. The console must show exactly one `GDB S02` start, and its `STOP` JSON rows must exactly match the capture's CPU events. The resulting `same_emulator_process_log` is intentionally **false** for all legacy imports, while `archive_single_console_consistent` can be true; don't promote a post-hoc ID to a native observed PID. Future fresh captures should log real per-event process/run IDs at capture time.
- **R3 console required:** The CLI requires `--console`; direct verification also rejects `console=None`. Console accepts only specified `GDB`, `BP`, `SNAP`, `KEY`, `STOP`, `EVENTS`, and post-run hash lines. All unknown host commands, input after movement other than directional buttons, mismatched STOP rows, missing movement, malformed timestamps, and duplicate GDB start markers fail. `host_input_checked=true` is emitted only after this complete check. Directional host inputs **might** occur during battle and are not proof of autonomous command selection.
- **R4 chronology:** `t` must be a finite, non-boolean, strictly increasing Python integer or float. CLI's JSON parser rejects `NaN`/Infinity. Distinct PP memory addresses must be observed for player (`r0=0`) and foe (`r0=1`); v5 also checks `r3=4`, `r4=2`, and Z=1 consistency before the terminal branch.
- **R5 reproducibility:** The CLI has explicit `--mode {v3-basic,v4-branch,v5-full}`, defaulting to full v5, and `--normalize-legacy` for transparent archived provenance. All three original archived JSON+console pairs have been re-run under their **appropriate** modes (4, 4 and 3 complete CPU episodes respectively). A v3 or v4 archive cannot pass full-v5 requirements.

```bash
python3 tools/verify_native_wild_chain.py PATH/TO/native_v5/cpu_events.json \
  --console PATH/TO/native_v5_stdout.log \
  --mode v5-full --normalize-legacy
```

`tools/test_verify_native_wild_chain.py` contains **28 synthetic tests** checking the five fixes, raw-vs-normalized console consistency, mixed run IDs, finite chronology, CLI modes, invalid host actions and conservative claim labels. This test file is wired into `.github/workflows/source-check.yml`; claim a GitHub test pass only after **exact-head** CI completes and actual job logs confirm it. A standalone pass of synthetic tests is not itself native gameplay proof.

## Original files, schema and evidence boundaries

Archived original records use JSON `{rom_sha256,save_sha256,original_cpu_events:[...]}` and a corresponding line-oriented GDB stdout log with `GDB S02`, `STOP {original CPU row}`, `KEY`, `EVENTS count`, and `ORIGINAL_POST_HASH` lines. Their CPU events have **no** process IDs. The deliberate post-hoc normalized schema adds `{run:{run_id,start_marker,console_sha256,provenance:'LEGACY_POSTHOC_IMPORT',process_id_observed:false}}` plus an identical `run_id` on each original CPU row; this is an **import envelope**, not a changed original CPU witness. A single console and matching STOP rows are verified; runtime provenance remains weaker than a fresh at-capture recorded process marker.

Original archived raw GDB/CPU witness ZIP SHA256 `6c95e5f5d2bf152a49e88fd51256af9a31da69b54cd37b7b2d9a2780af80e6b7` is stored privately in Google Drive: https://drive.google.com/file/d/1R-sy1bTxRRs1Cb3Vhb0JiR6lQQwLvSyZ/view . The original archive contains no ROM, save or savestate. Complete v5 revalidation output must also be included in a **new verified research ZIP** with an explicit manifest hash. The code and public synthetic tests contain no original game bytes.

## Safety / pending production gates

This isolated research branch changes only `tools/`, `docs/` and CI workflow; it does not change main, canonical source-first, player or enemy/NPC partner controllers, the protected Current ROM/save, in-battle items, capture or uncertified doubles. PR #21 remains independently approved at exact head `1666676d8b158c585033266c7f71e7a4ba545cd8`, draft and unmerged; that independent approval does **not** transfer to this PR #22 head.

Historical PP-unmatched submissions #1 and #2 remain **independently unclassified (0/2)**, not joined to any new trace. Still unproven: engine-issued and one-use actor0 request ownership, move slot and target legality, cancellation and PP linkage, the precise outcome bit meaning, Smart Auto-Battle source-LAB execution in the modified ROM, and manual fallback. Formal native acceptance **0/20 (0%)**, production hybrid promotion **0%**. Keep PR #22 draft/unmerged pending new independent Claude exact-head approval, exact-head source CI and the separate native promotion gates.
