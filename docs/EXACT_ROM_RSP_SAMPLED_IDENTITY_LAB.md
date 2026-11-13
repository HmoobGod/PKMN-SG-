# Experimental modified-ROM identity probe — research HOLD

**Scope:** Source-only, isolated, private read-only RSP sampler. **Native acceptance 0/20, production Smart Auto-Battle 0%; neither emulator-loaded ROM/save identity nor engine-owned one-use request is certified.** Do not promote to gameplay or merge without independent exact-head review.

## Why

Existing original CPU observations are associated with exact experimental ROM SHA-256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44`. The protected Current ROM is **not** the same experiment: SHA-256 `7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32`. Data from one process or ROM must not authorize another. A GDB connection alone does not establish which ROM is loaded.

This optional helper first validates both *on-disk* 32 MiB ROM identities, then selects distinct eight-byte windows where they differ plus an identical control window. Against an **already-paused, disposable** mGBA debugger on `127.0.0.1`, it sends only `?`, `g`, and precisely whitelisted `m<romaddr>,08` read requests. The transcript is retained privately even on failures. Raw debugger output and register data **must not** be added to public GitHub or shared packages.

## Private operator procedure (not performed in this patch)

1. Obtain a real, locally held **separate** 32 MiB exact modified-ROM file with SHA `4b2585e1…` and the protected Current ROM as a read-only baseline. The exact modified ROM is **not included** here; do not substitute the protected Current ROM, a historical research ROM or a rebuilt source ROM.
2. Make disposable test copies of the exact modified ROM and compatible save. Start mGBA locally, load **the disposable exact modified ROM**, pause the emulator, enable the mGBA GDB server on loopback, and use no host controls during the probe. This tool does **not** set up the emulator, validate its loaded save, pause it, or press any game buttons.
3. Run with a fresh private report path:

```bash
python3 tools/probe_exact_rom_rsp_identity.py \
  --exact-modified-rom /private/test/exact-modified.gba \
  --protected-current-rom /private/reference/Pokemon-Soulgold-Current.gba \
  --report /private/sg-sampled-rom-identity.json \
  --port 2345 --timeout 2
```

4. Keep the output file private (exclusive create, permissions `0600`). Inspect `failure`, `raw_wire_trace`, `g_reply_char_count`, `stop_reply`, the four selected `candidate_windows` and `samples`. A failed probe still retains bounded raw wire evidence. The program never sends host game input, debugger resume `c`, step `s`, breakpoints `Z0/z0`, reset, or target memory writes `M/X/P/G`.

## Interpret results conservatively

- `SAMPLED_WINDOW_PARITY_ONLY` means the **few sampled remote ROM-address bytes** matched the exact modified on-disk input, and selected differing samples did not equal the protected Current image. It does **not** prove the target loaded the complete modified ROM; arbitrary debugger servers or ROM overlays could mimic those bytes, and the loaded save has not been verified.
- `FAILED_PARTIAL` is not a gameplay failure or success. It can mean a protocol discrepancy, disconnected debugger, identity mismatch, file change, checksum issue or unsupported packet encoding. Raw traffic is private, bounded and retained where available.
- `g_reply_char_count` and `stop_reply` are **uninterpreted** protocol observations. Neither register layout, CPSR, real mGBA's ACK/stop behavior nor emulator state is certified by fake-server tests.
- Windows are sampled in ROM-mapped `0x08000000`–`0x09FFFFFF`. No instruction decoding, physical memory parity, control-flow causation, battle inputs, PP consumption or request ownership is determined.
- This report is **not** in the approved `RUN_START/STOP/EVENTS` native verifier grammar. It cannot be used to claim a native Smart Auto-Battle gate.

## Exact safety and next gates

Both source images are checked by size, symlink policy and SHA-256 **before any connection** and rehashed after probing. The connection is always loopback; finite per-read timeouts, packet caps, trace caps and a narrow allowlist limit risk. No report overwrites protected inputs or existing files. Network / file races and arbitrary external RSP implementation remain unverified; no real mGBA probe was run in this patch.

If Claude independently approves this helper as source-only, the *next real milestone* is the paused mGBA `?`/`g`/`m` private probe from disposable exact-ROM and save, and a private captured transcript. A separately reviewed opt-in `Z0/z0` install/remove check (without `c`) would be needed before interpreting breakpoints or stepping; then a same-session engine-issued player0 request, post-A-loop six-byte copy, dynamic legality, PP/cancel, battle outcome, overworld and second wild witness. **Historic two unmatched PP submissions remain 0/2 classified.**