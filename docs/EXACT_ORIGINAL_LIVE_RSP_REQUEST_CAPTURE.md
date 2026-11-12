# Original customized-ROM actor0 live GDB capture — diagnostic HOLD

**Scope:** read-only capture adapter, no Smart Auto-Battle implementation or gameplay approval. Its branch must remain draft. Source-only synthetic tests do not count toward formal native acceptance (0/20) and do not classify the two historic unmatched PP submissions (0/2).

The original exact modified test-ROM fingerprint is `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44`; its paired original save fingerprint is `8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4`. Never substitute the protected Current ROM (different SHA), clean source build, or an arbitrary savestate. Only point this tool at separate immutable input files; the emulator must itself use **disposable copies** of the same authenticated inputs.

## What this adds

`tools/capture_original_request_rsp.py` connects to an already-running mGBA GDB Remote Serial Protocol server on `127.0.0.1`. It checks original file hashes before/after, sends only GDB stop query, read-register (`g`), bounded EWRAM reads (`m`), debugger breakpoint install/remove (`Z0`/`z0`) and CPU resume (`c`). It **never** sends gamepad keys, battle commands, register/memory writes, item/capture instructions, reset or savestate operations. It samples original actor0 emitter/copy/completion/validator/slot/move/target/PP/Main instruction PCs and tries to pair actual six-byte source/destination samples in one live debugger session. Every raw stop PC is retained because ARM/GDB pipeline offsets vary and this tool cannot prove the true executed instruction by a guessed PC alone. The output is **private** and must not be committed as a public fixture.

With the correct files and an already-paused debugger stub, example (run from the repository root, *after* starting disposable mGBA with GDB server):

```sh
python3 tools/capture_original_request_rsp.py \
  --rom /private/exact_modified_disposable_source.gba \
  --save /private/original_readonly_source.sav \
  --port 2345 \
  --max-stops 40 \
  --output /private/sg_rsp_original_capture_001.json
```

If a GDB implementation uses unsupported packet framing, rejects a breakpoint, times out, or returns ambiguous CPU registers, the adapter **fails closed**. It has **not** yet been exercised against a real exact-ROM mGBA instance; RSP handling is tested with a simulated stub only. Its breakpoint list should be confirmed against live instruction parity before first extended capture. An interrupted session may leave the emulator paused, and a crashed/disconnected debugger may require user-side cleanup; never claim a completed capture on exception. RSP breakpoints are debugger-only instrumentation, not game hooks.

## Required native follow-through

1. Establish the original engine's issued player0 command in the **same actual emulator process** and capture its owner, opcode, live request bytes, and single-use epoch before any reply; the current adapter does not record issuance yet.
2. Pair one original player0 six-byte copy with original slot/move/target commit, effective PP/Disable/Encore/Choice/Imprison legality, PP change or explicit cancellation, and terminal callback. All event order and instruction/ROM parity need verification with the private raw trace.
3. Follow overworld return and next naturally encountered wild Pokémon with zero host battle selection inputs; distinguish original custom-ROM behavior from any newly installed Smart AI hook.
4. Prove manual fallback and actor isolation. No item/capture, enemy, NPC partner, uncertified doubles, trainer or force-switch automation.

The adapter alone proves **none** of those gates. Preserve private evidence and its manifest in Drive; do not expose ROM/save/savestates or private register/memory dumps in a public PR. Independent Claude exact-head review, source CI, combined compatibility and full native 20/20 acceptance are separate prerequisites to promotion.