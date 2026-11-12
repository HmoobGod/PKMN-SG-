# Original customized-ROM actor0 live GDB capture — diagnostic HOLD (PR #26 R1)

**Research-only, never a gameplay authorization.** The source tests simulate a debugger, not mGBA. Native 20-case acceptance **0/20 (0%)**; production Smart Auto-Battle **0%**; historical unmatched PP submissions **0/2 classified**. Keep PR #26 DRAFT and unmerged pending exact-head independent review and authentic CPU evidence. This repair responds to independent Claude REQUEST CHANGES at `cedfc9df0a0c3267bdad86a21242fdfa66cf8115`.

The exact customized-ROM **input file** must have SHA-256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44`; original private save input must have SHA-256 `8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4`. Never point mGBA at protected Current ROM/save. Use separate disposable emulator copies; report hashes are about **the named input files**, NOT proof of what was loaded by the external emulator. The tool rehashes the files after a session and refuses altered or symlinked originals.

## Claude B1–B6 repair boundaries

- **B1: Deadlines and cleanup.** `--deadline-seconds` bounds total research run. An idle `c` read timeout means *running*, not failed: the script continues waiting for a CPU stop. Deadline or Ctrl-C sends a raw debugger `0x03` interrupt, expects an actual bounded stop reply, and removes breakpoints **only when paused**. Cleanup has a separate short total deadline; failures and leftover breakpoints remain visible in the private report. Exceptions preserve a mode-0600, exclusive-created, **partial** report with a failure string. No scenario is promoted from a partial report.
- **B2: Enforcement in the wire sender.** `m` is restricted to named exact source/destination six-byte windows, four observed player PP bytes, and one observed Main IWRAM byte (`0x03005A0D`). `Z0/z0` are restricted to ten exact original Thumb PCs. `c` is accessible only via bounded `resume`. `s` is allowed **once** and only immediately after a player0 PP-writer stop and one-byte before-read. CPU execution naturally changes game state; this is not a claim that all CPU side effects are read-only. Software breakpoints `Z0` may themselves patch guest memory on some stubs; **mGBA behavior remains unverified**, and the tool does not measure guest writes caused by debugger breakpoints.
- **B3: Honest provenance.** Report uses `input_file_rom_sha256`, `input_file_save_sha256`, `tool_sent_battle_commands=0`, `tool_sent_guest_writes=0`, `operator_input_log=NOT_RECORDED`, `host_input_during_battle=NOT_EXCLUDED`, `emulator_loaded_rom_verified=false`, `emulator_loaded_save_verified=false`. The PID is the **recorder**, not mGBA. `stop_budget_reached` and `marker_stop_count` are descriptive only; there is no automatically certified `completed_capture`. `native_acceptance` and one-use authority remain false/zero.
- **B4: Original copy observation.** Record all `r0`–`r15` for each stop. At copier entry, sample `r2` as a *candidate source* only when in the named source window. At epilogue, report observed `r0` as a **candidate** destination and read bytes only if it falls within a separately pinned named destination window. `destination_is_player0_buffer` is computed from the observed candidate, not hardcoded as the destination. Actual copier destination semantics remain subject to original CPU instruction proof. Orphaned copies are not stitched across unrelated marker stops.
- **B5: PP before/after.** At the observed original PP writer `0x0809E6BA`, require actor `r0=0`, observed `r1` within the four own-PP bytes, read before, issue exactly one `s`, check next reported raw PC advanced +2, read after, record original `r6`. `pp_decrement_observed` needs an actual one-byte debit and the low `r6` byte to agree. Even that **does not** prove move authorization or explain the historic unmatched submissions.
- **B6: Strict CPU PC bias.** First unique matching breakpoint stop fixes a raw-PC bias of **0, +2 or +4**. Every subsequent stop must use that identical bias; mismatch rejects the trace. This is a consistency guard, not real original instruction parity or a substitute for reading CPSR/ROM opcodes from the debugger.

## First contact: probe-only, no guest continuation

Connect to an **already-paused** mGBA GDB server on loopback. Run probe mode first. It sends **only** `?`, `g`, and a six-byte read at the previously observed, named EWRAM address. It never installs breakpoints, resumes with `c`, steps, sends keys, or touches a savestate. The raw response bytes, register payload size, and decoder shape are saved **privately**. Do not post this report to GitHub.

```sh
python3 tools/capture_original_request_rsp.py \
  --rom /private/exact_modified_original_input.gba \
  --save /private/original_immutable_save_input.sav \
  --port 2345 \
  --probe-only \
  --output /private/sg_rsp_probe_unique.json
```

**Only after a human verifies actual mGBA packet framing, stop semantics, safe `Z0`, register ordering and relevant original code parity** should full source-only capture be attempted on disposable test assets:

```sh
python3 tools/capture_original_request_rsp.py \
  --rom /private/exact_modified_original_input.gba \
  --save /private/original_immutable_save_input.sav \
  --port 2345 --timeout 5 --deadline-seconds 180 --max-stops 40 \
  --output /private/sg_rsp_capture_unique.json
```

These names are examples, not proof that the runtime is installed here. The debugger may stay paused after successful capture, and failed interrupts can leave breakpoints installed. A run is **not** safe to reuse for gameplay until the operator has verified debugger cleanup. No live mGBA GDB contact is claimed by this source-only repair.

## Known unverified protocol/semantics blockers

RSP `g` length/order/CPSR, `T05` versus `S05` stop behavior, whether `Z0` is actually a software-guest write, stepping over an installed breakpoint, `0x03` interrupt semantics, escaped or run-length GDB replies (explicitly rejected), actual register `r0` destination semantics, mGBA loaded-ROM/save binding, operator input, genuine issuance of a one-use engine-owned actor0 request, legality and cancellation remain unproven. Main-clear sampling reads **the byte before that observed PC**, not a proven `2->0` write. Existing source/provenance verifiers use different STOP/console grammar; this JSON **is not compatible** with them without a separately reviewed adapter. Synthetic tests are not CPU authenticity evidence.

## Native priority (no source-only inflation)

1. Validate *probe-only* contact against authentic private mGBA on disposable copies; retain raw protocol receipt privately.
2. Capture original engine request creation and **unique player0 ownership** before any six-byte response, including opcode, request bytes and one-use cancellation/consumption epoch.
3. Correlate original six-byte copier, actual dynamic move slot/target legality, PP debit or cancellation, and battle outcome/overworld callback in the **same** run. Never stitch separate archives or infer cancellation merely from missing PP.
4. Confirm no host battle inputs, next natural wild, manual fallback and other-actor isolation with new original CPU witnesses; prove a **new** Smart Auto-Battle chooser actually ran before promotion.

Do not modify the protected ROM/save, main, enemy/NPC-partner AI or automatic item/capture policies. Keep uncertified doubles, trainer and forced-switch automation disabled.