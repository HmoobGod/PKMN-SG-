# SoulGold R4 CFG Narrow R3 — Claude read-only source review (no ZIP required)

**Scope:** Narrow re-review of Claude's R2 r1 saved-LR provenance blocker only. The R4 player Auto assembly is unchanged. No private game files, native traces, patch objects or ROM/SAV content in this folder. **No merge or release permission.**

This directory is pinned to a single Git commit; verify with `sha256sum -c SHA256SUMS.txt`.

## Files to inspect

- `audit_r4_cfg_v2.py`: fixed `may_clobber_r1` conservative return-address provenance; symbolic callee proof; caller CFG and hook-entry scans unchanged.
- `test_r4_source_only_repairs.py`: **67** source/synthetic cases, including the five independently reported false passes at real ARMv4T Thumb opcodes in a fully synthetic 32 MiB image. The fixture is generated in memory and never reads protected ROM/SAV.
- `R4_R7_VISITED_ADDRESSES_ONLY.json`: **historical** address metadata, not fresh ROM/native proof. `--selftest` prints its SHA256 digest.
- `player_taunt_recovery_choice_gorilla_r4.s`: **unchanged** source SHA256 `ce8d38b718939243a99eed560d250ed30e15b29255a0b4f0c21f3cd3ced12333`; expected 252-byte ARMv4T Thumb object-section SHA256 `d588d77c7096afcf9130b445d184ef06842f7599da92649c65ae73d637abc584`.
- `build_r4_disposable_failclosed.py`, `verify_r4_source_layout.py`, `armv4t_header_projection_dump.txt`: unchanged R2 dependencies.

## Independently rerun

```sh
sha256sum -c SHA256SUMS.txt
python3 -m unittest -v test_r4_source_only_repairs.py
python3 audit_r4_cfg_v2.py --selftest
```

Expected author run: **67/67** source/synthetic tests; no R4 native game trial.

### Narrow adversarial review request

1. At the exact auditor revision, try stale-r1 return-provenance exploits after `pop {r1}` for `mvns r1,r0`, `rors r1,r0`, `ldm r0!,{r1}`, `ldrsb r1,[r0,r2]`, and `adr r1,#8`; also register-list ranges and unknown ops.
2. Confirm true read-only operations (e.g., `cmp`, `cmn`, `tst`, `str r1,[r0]`) do not produce an unsafe false approval; store writeback/unknown touch fails closed.
3. Run the complete synthetic production `private_rom_analysis` fixture: 32 MiB made entirely of manufactured Thumb code, **66 visited nodes**, one pre-definition BL, valid original-r7 restoration, and five invalid r1 return paths.
4. Independently mutate new tests and report uncovered false passes. Do not treat bounded symbolic CFG or metadata hashes as proof against indirect BX, ARM-state paths, or actual native gameplay.

**Verdict:** APPROVE or REQUEST CHANGES **for the R3 audit tools only**, with exact file/line and exact commit. Prior R2 REQUEST CHANGES applies only to R2; R4 gameplay code remains unchanged and has no native certification. **Formal 0/20; production 0%.**
