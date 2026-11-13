# Original customized-ROM actor0 live GDB capture — diagnostic HOLD (PR #26 R2)

**Research-only, never a gameplay authorization.** The source tests simulate a debugger, not mGBA. Native 20-case acceptance **0/20 (0%)**; production Smart Auto-Battle **0%**; historical unmatched PP submissions **0/2 classified**. Keep PR #26 DRAFT and unmerged pending exact-head independent review and authentic CPU evidence. This second isolated source repair responds to independent Claude REQUEST CHANGES at R1 head `20f3376dcb262159783b40c1a82ad7498e182571`, after the initial review at `cedfc9df0a0c3267bdad86a21242fdfa66cf8115`. A new exact-head review is still mandatory.

The exact customized-ROM **input file** must have SHA-256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44`; original private save input must have SHA-256 `8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4`. Never point mGBA at protected Current ROM/save. Use separate disposable emulator copies; report hashes are about **the named input files**, NOT proof of what was loaded by the external emulator. The tool rehashes the files after a session and refuses altered or symlinked originals.

## Claude B1–B6 repair boundaries

- **B1: Deadlines and cleanup.** `--deadline-seconds` bounds total research run. An idle `c` read timeout means *running*, not failed: the script continues waiting for a CPU stop. Deadline or Ctrl-C sends a raw debugger `0x03` interrupt, expects an actual bounded stop reply, and removes breakpoints **only when paused**. Cleanup has a separate short total deadline; failures and leftover breakpoints remain visible in the private report. Exceptions preserve a mode-0600, exclusive-created, **partial** report with a failure string. No scenario is promoted from a partial report.
- **B2: Enforcement in the wire sender.** `m` is restricted to named exact source/destination six-byte windows, four observed player PP bytes, and one observed Main IWRAM byte (`0x03005A0D`). `Z0/z0` are restricted to eleven exact original Thumb PCs, including newly observed candidate post-A-loop instruction `0x0806B3C6`. `c` is accessible only via bounded `resume`. `s` is allowed **once** and only immediately after a player0 PP-writer stop and one-byte before-read. CPU execution naturally changes game state; this is not a claim that all CPU side effects are read-only. Software breakpoints `Z0` may themselves patch guest memory on some stubs; **mGBA behavior remains unverified**, and the tool does not measure guest writes caused by debugger breakpoints.
- **B3: Honest provenance.** Report uses `input_file_rom_sha256`, `input_file_save_sha256`, `tool_sent_battle_commands=0`, `tool_sent_guest_writes=0`, `operator_input_log=NOT_RECORDED`, `host_input_during_battle=NOT_EXCLUDED`, `emulator_loaded_rom_verified=false`, `emulator_loaded_save_verified=false`. The PID is the **recorder**, not mGBA. `stop_budget_reached` and `marker_stop_count` are descriptive only; there is no automatically certified `completed_capture`. `native_acceptance` and one-use authority remain false/zero.
- **B4 / D1–D2: Post-loop, NOT shared return.** Record all `r0`–`r15`. At `0x0806B370` copier entry, accept `r2` as a candidate source ONLY when exactly `0x0201CF94`. A **subsequent observed** `0x0806B3C6` hit is the static non-link buffer-A loop fall-through, not a formal write proof: at this candidate point, original Thumb instructions leave `r0` holding the destination base, `r1` indexing the copied bytes, `r2` count=6, and `r4` the source. Require `r4==entry source`, `r1==r2==6`, observed `r0` equal to independently pinned `0x0201C794` (player0) or `0x0201C994` (other actor), and `r0 != source` before comparing six bytes. Any source-self-comparison, unknown/other pointer, or count mismatch is explicitly `destination_unreadable` with `six_byte_pair_equal=null`; an observed other-actor buffer is labeled separately and does **not** become player0 authority. Shared `0x0806B3A6` has only `shared_epilogue_reached=true` and `copy_completion_proven_here=false`; link/empty/invalid paths also reach it. The candidate instruction register semantics are static evidence from R5; **no instruction parity has been proven in a live exact modified-ROM target**, and even equal bytes do NOT prove guest stores or engine request authorization. Orphaned copies are not stitched across unrelated markers.
- **B5 / D3–D4: PP before/after and partial preservation.** At `0x0809E6BA` (original `STRB r6,[r1]`), gate ONLY on `r1` inside the exact four player0 PP bytes. `r0` is recorded as `pp_register_r0_unverified`, never assumed actor identity. Append the CPU marker event and its `pp_before` **before** a single debugger step, then read the new PC and `pp_after`. A failed step retains `pp_before` and `pp_step_error` in the mode-0600 partial file. `pp_decrement_observed` needs an actual one-byte debit and low `r6` match. This still does not prove move authorization or explain historical PP-unmatched submissions.
- **B6: Strict CPU PC bias.** First unique matching breakpoint stop fixes a raw-PC bias of **0, +2 or +4**. Every subsequent stop must use that identical bias; mismatch rejects the trace. This is a consistency guard, not real original instruction parity or a substitute for reading CPSR/ROM opcodes from the debugger.


## R2 raw-wire provenance and interruption repair (D5–D6)

- Every debugger packet **transmitted/received** is captured in ordered private `raw_wire_trace.events` as hex, regardless of successful parsing; ``tx`` means a send *attempt*, not proof of target receipt. Raw `g` framing, corrupt checksum, unsupported RLE (`*`), escaped payload (`}`), truncated frames and malformed probe data are retained on failure. Encoding support itself is intentionally fail-closed; it is not GDB-RSP compatibility certification.
- Wire preservation is bounded to 524,288 bytes and 8,192 direction-change events. `truncated`, `omitted_bytes`, and per-direction raw hex are explicit; such an archive cannot certify full protocol provenance if truncated. Reports are exclusive-created mode `0600`. Never upload raw wire or buffer bytes to public GitHub.
- `--probe-only` populates a partial `probe_transcript` immediately after the initial stop, and the raw wire trace is assigned in `finally` even when parsing fails. The first real mGBA probe must be inspected privately, not used as native gameplay proof.
- `resume` restores the configured socket timeout after a completed stop/deadline so `g/m/s` do not inherit an almost-expired deadline. After a debugger interrupt, up to four surplus **CPU stop frames** are drained in at most 0.2 seconds before breakpoint cleanup; malformed surplus replies or cleanup errors remain visible and fail the session.

## First contact: probe-only, no guest continuation

Connect to an **already-paused** mGBA GDB server on loopback. Run probe mode first. It sends **only** `?`, `g`, and a six-byte read at the previously observed, named EWRAM address. It never installs breakpoints, resumes with `c`, steps, sends keys, or touches a savestate. The raw received/transmitted bytes (including unexpected packets), register payload size when decodable, and decoder state are saved **privately**, even on a probe failure. Do not post this report to GitHub.

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

RSP `g` length/order/CPSR, `T05` versus `S05` stop behavior, whether `Z0` is actually a software-guest write, stepping over an installed breakpoint, `0x03` interrupt semantics, escaped or run-length GDB replies (explicitly rejected), live exact-ROM post-A-loop `r0` destination semantics, mGBA loaded-ROM/save binding, operator input, genuine issuance of a one-use engine-owned actor0 request, legality and cancellation remain unproven. Main-clear sampling reads **the byte before that observed PC**, not a proven `2->0` write. Existing source/provenance verifiers use different STOP/console grammar; this JSON **is not compatible** with them without a separately reviewed adapter. Synthetic tests are not CPU authenticity evidence.

## Native priority (no source-only inflation)

1. Validate *probe-only* contact against authentic private mGBA on disposable copies; retain raw protocol receipt privately.
2. Capture original engine request creation and **unique player0 ownership** before any six-byte response, including opcode, request bytes and one-use cancellation/consumption epoch.
3. Correlate original six-byte copier, actual dynamic move slot/target legality, PP debit or cancellation, and battle outcome/overworld callback in the **same** run. Never stitch separate archives or infer cancellation merely from missing PP.
4. Confirm no host battle inputs, next natural wild, manual fallback and other-actor isolation with new original CPU witnesses; prove a **new** Smart Auto-Battle chooser actually ran before promotion.

Do not modify the protected ROM/save, main, enemy/NPC-partner AI or automatic item/capture policies. Keep uncertified doubles, trainer and forced-switch automation disabled.

### R3: actor-isolated original copier observation

- A new original request copier entry always breaks the previous provisional pair. A foreign-actor, wrong-direction/count or unpinned-source entry clears the pending actor0 entry and records `incomplete_previous_copy_pair`, never allowing a later post-A marker to reuse stale bytes.
- Only the pinned `DST_PLAYER0` destination of an immediately paired actor0 entry can produce a six-byte equality observation. `DST_OTHER` remains a **read-only, other-battler buffer** for diagnostics; it is never compared with an actor0 source or treated as player-owned. Cross-battler and invalid pointers produce an explicit `destination_unreadable` reason and null equality.
- The R3 regression suite includes synthetic actor0→actor1 interleaving, actor0→other destination, raw probe truncation/disconnect, wire byte/event caps, timeout restoration, PC bias +4, T-stop stepping and extra-length `g` replies. These fixtures do not certify actual mGBA protocol behavior. The initial real contact remains **probe-only** and the private transcript must not be committed.

## R4 diagnostic review checkpoint — source/test only

- Claude R3 independent review marked the actor0/foreign-battler D7 pairing fix source-acceptable but **REQUEST CHANGES** until the near-deadline timeout restoration test actually fails when the `resume()` restore is removed. The R4 regression uses an overall deadline shorter than the configured read timeout, confirms a shortened read timeout occurred, and asserts the final configured value was restored. This must be independently mutation-checked.
- A rejected COPY_ENTRY without an earlier active player0 pair does **not** imply `incomplete_previous_copy_pair`; rejection remains explicit. The marker reports only describe original debugger observations, not request ownership.
- Added fake-stub `T05` resume-stop and extended-`g` in-capture tests; register layout/CPSR are still UNVERIFIED against mGBA. No fresh mGBA contact, player-auto hook, engine request, ROM or save write occurred in R4. Formal native 0/20, production 0%, unmatched PP 0/2.

## Isolated Current-copy protocol preflight (stacked diagnostic draft; no live acceptance)

The original diagnostic above pins the separate historical experimental image
`4b2585e1…`; a duplicate of the protected Current ROM has **a different hash**
and must never be renamed or silently treated as the experiment. A new,
explicit `--current-copy-probe-only` option allows the **Current ROM copy**
`7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32`
with the protected save copy
`8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4`.
It **requires** `--probe-only`, rejects all attempt to run full capture, and
retains the original historical-experimental default unchanged.

Before **any** debugger connection, the tool requires the exact Current 32 MiB
hash and verifies two separate original Thumb byte windows in that file:

| Original CPU address | Length | Pinned static SHA256 |
|---|---:|---|
| `0x0806B370` copier region | 104 bytes | `c3d3181837d0aaf69fc471c4f5598870257c622c81bca9771a5d96d45850ab57` |
| `0x0809E6AA` PP-writer region | 64 bytes | `84ffa68c024412568ce64fdac3719cd460c40a55caf07a5549bd150a7fe50923` |

These *static* anchors were independently measured on the locally available
Current duplicate and matched its protected original byte-for-byte. They are
**not** ROM-loaded identity, debugger instruction parity, move legality,
player request ownership, proof of a PP deduction, or a new native replay.
The save is read-only and hashed before and after. `m` still reads only the
named six-byte EWRAM buffer. No ROM bytes, private save contents or raw GDB
captures belong in public git or source ZIPs.

Only when a disposable current copy is already loaded and paused in a **real**
mGBA GDB server on loopback, run locally from a working copy of this script:

```powershell
python tools/capture_original_request_rsp.py --rom "C:\\SoulGoldLab\\Pokemon_SoulGold_TEST_COPY.gba" --save "C:\\SoulGoldLab\\Pokemon_SoulGold_TEST_COPY.sav" --output "C:\\SoulGoldLab\\private_current_probe.json" --port 2345 --probe-only --current-copy-probe-only
```

This optional command sends at most `?`, `g`, `m0201cf94,6` and RSP ACK/NAK;
**no `Z0`, `z0`, `c`, `s`, injected move, menu input or savestate**. The output
is new, private, mode 0600 where supported, and may contain battle-buffer bytes.
Do not publish it. A real RSP failure may still preserve valuable raw bytes
in a partial report; keep that report private. Use a fresh output path for
each attempt. If mGBA's `g` encoding differs, fail closed and report bytes,
never rewrite an emulator response until independently understood.

No emulator process/server is available in the current ChatGPT container.
The source tests use disposable synthetic ROMs (with patched constants inside
tests only); **no live current-copy GDB probe has run**. Real gameplay
acceptance remains **0/20**, native production **0%**, PP discrepancies **0/2
classified**. Only after an actual private protocol probe and independent
review may further real CPU capture be designed. Do not modify the protected
Current game, save, enemy/NPC-partner AI, items/capture or uncertified doubles.