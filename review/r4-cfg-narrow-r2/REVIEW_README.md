# SoulGold R4 CFG Narrow R2 — source-only independent review

**Scope:** review the unchanged R4 assembly and the revised *audit tools*, not a new gameplay patch. No ROM, SAV, savestate, game asset, private runtime log, binary patch or compiled game artifact is included. Branch is isolated, not merged, not released.

## Exact R4 identities
- Approved R4 source SHA256: `ce8d38b718939243a99eed560d250ed30e15b29255a0b4f0c21f3cd3ced12333`.
- Expected ARMv4T Thumb output: 252 bytes; SHA256 `d588d77c7096afcf9130b445d184ef06842f7599da92649c65ae73d637abc584`.
- ZIP before GitHub staging: `SoulGold_R4_CFG_Audit_Narrow_R2_SourceOnly_20261117.zip`; SHA256 `fb9e16eda336e38bc5422d5318e0f22315efb4d7c09499566ca20a73f6e726e9`. GitHub staging publishes the 7 files required for review, not a ZIP.

## Review instructions (READ-ONLY)
In this directory, verify `sha256sum -c SHA256SUMS.txt`. Then run:
```sh
python3 -m unittest -v test_r4_source_only_repairs.py
python3 audit_r4_cfg_v2.py --selftest
```
Use clang and llvm-objcopy if available. Run and independently extend the same six adversarial groups: two-operand register-shift r7 reads; nested PUSH/POP origin and unbalanced stack; BX r3 rejection and saved-LR return provenance; literal LDR/ADR non-jump behavior; 0x66000 caller window; raw B/conditional B/BL hook-entry and veneer-middle hits fail closed.

**Expected old local result:** 60/60 public/synthetic tests. A passing suite is not an independent review or a native gameplay witness. Report exact head SHA, file/line evidence, and APPROVE or REQUEST CHANGES **for the R2 audit tools only**. Do not infer the protected ROM-side CFG from the address-only JSON; that JSON is historical reported metadata, not a new trace.

**Hard boundaries:** no private game bytes or user saves are part of this branch. Do not download/access the private ROM/SAV, modify main, open or merge a PR, release a build, or claim native certification. Formal 0/20, production 0%.
