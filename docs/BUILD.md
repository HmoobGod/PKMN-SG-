# Reproduce checkpoint16266 with private inputs

Requires Python3, Zig0.13.0 and the packages pinned in tools/requirements-build.txt. Install dependencies into your own virtual environment. No network download is performed by the builder.

Python dependency versions are pinned; distribution/wheel hashes are not pinned. The final artifact hash checks verify this checkpoint's output, not the provenance of installed dependencies.

```
python3 -m pip install -r tools/requirements-build.txt
python3 tools/build_private.py --zig /path/to/zig --base-rom /private/SoulGold_16265.gba --out-dir build/16266
```

The base must be exactly16265 SHA256 deef0016003b281137ef2b85479e4e3691c909f7a2df51725149bf600d22442a. This is a private experimental base, not an original commercial ROM or historical16249 base. Recover it separately. The builder needs no old work directories or saves. It rejects another input before compiling or writing outputs, checks Zig version, rejects a cave shorter than the pinned5850-byte base cave rather than leaving a stale tail, compiles public C, assembles the public wrapper, and verifies cave/ROM/IPS hashes before writing anything. Output directory must differ from the input ROM directory.

Outputs are ignored private artifacts: ROM, cave, ELF, incremental IPS and a receipt listing public source SHA256 values. Exact expected identities are in docs/checkpoint.json. The receipt is a local reproduction record, not an emulator test or action-authority certificate. Public CI has no ROM and runs source checks only.

## Held-B template installation inherited from16264

| Decision | Veneer address | ENTRY | RESUME with Thumb bit | BX continuation |
|---|---|---|---|---|
| Player action | 0x08065324 | 0x09F23000 | 0x0806532B | 0x0806532C |
| Player move | 0x08065A5C | 0x09F23100 | 0x08065A63 | 0x08065A64 |

Each original eight-byte span is actor extraction `lsrs r4,r4,#24`, `bl 0x0806DF4C`, `cmp r0,#0`. RESUME is the original BL return value with bit0 set; it denotes the replayed compare location, not the branch that is resumed. The wrapper restores LR to RESUME, adds2 to the BX destination, and replays cmp immediately before BX. The original beq/bne consumes those flags. The private base already contains this installation; this incremental builder does not assemble/install held_b.s. Original byte excerpts remain in private review evidence.

The held-key address0x03005600 was observed as positive-logic held keys (mask2 for B) in local native probes. That is reported evidence, not a hardware portability guarantee. Scope remains actor0/player signature/flags4/count2; no trainer/partner override certification.
