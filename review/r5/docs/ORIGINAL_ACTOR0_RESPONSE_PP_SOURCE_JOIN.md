# Source-only original player0 response → PP join (UNVERIFIED)

## Purpose and guardrails

For the *exact private ROM* only, this local host audit matches the regular
GBA player-controller two-return-values response to a separately observed,
direct byte PP decrement. It never changes game bytes. A positive report is
**not** proof of Smart Auto-Battle source integration, native one-use ownership,
effective move legality, an executed move, manual fallback, or production
readiness. Original-game acceptance remains 0/20.

The host adapter's existing mGBA store hooks are exact-binary-specific and
read-only with respect to guest state: every intercepted CPU store delegates
exactly once to the original emulator store function. Its instrumentation
writes host-side logs *only*. This source package intentionally excludes the
private RAM-exhaustion experiment, which used a separate throwaway adapter.

## Original-ROM evidence criteria

- Read the **actual** private ROM bytes, not the emulator's prefetched `op`.
- Verify an actual Thumb-1 BL at `LR & ~1 - 4` targets the emitter.
- Require player battler 0, return-to-engine direction 1, action 10
  (`B_ACTION_EXEC_SCRIPT` in the uploaded public source), a move slot in
  0..3, and a 0..3 tentative target field.
- Require **all five** original CPU emitter stores in the same frame,
  correct widths, byte addresses, and payload values. Enemy battler 1
  packets cannot substitute for actor 0.
- Require a later original decision-PC store and completion-PC store,
  then a separate direct Thumb STRB PP-1 write from original ROM memory.
  A decision-register `r0` is **not** itself an actor identifier.
- The PP address must have a preceding, unambiguous dynamic battle-structure
  candidate with matching move slot; stale snapshots older than 300 frames,
  duplicates, wrong width, wrong STRB source/address, later-added candidates
  and conflicting base/slot structures fail closed.
- Scope each request interval to the **next** player response (or bounded
  300-frame expiry). A new legal turn must not invalidate an earlier turn;
  an overlapping response before PP is ambiguous.

These are strict *necessary syntactic clues*, not proof the auto planner
issued the request; original CPU execution can take this normal path even
without the pending GitHub Smart Auto-Battle source patch.

## Local private invocation

Execute only in a secure local directory and use the actual private game
identity hash supplied by the owner. Never run these private inputs in public
CI. The tool emits only redacted frames, slot indexes, PC metadata and false
certification flags.

```
python3 tools/audit_private_actor0_response_pp_join.py \
  --private-rom /PRIVATE/TEST_COPY.gba \
  --private-owner-stores /PRIVATE/owner_stores.jsonl \
  --private-pp-trace /PRIVATE/pp_store.jsonl \
  --expected-rom-sha256 YOUR_PRIVATE_HASH \
  --battle-ui-frame ACTUAL_FRAME
```

Only generated fake fixtures are permitted in public CI:

```
python3 tools/test_private_cpu_pp_store_audit.py
python3 tools/test_private_actor0_response_pp_join.py
```

## Remaining blockers

No exact-ROM ELF/map, compiler/linker provenance, or certified source-to-ROM
identity for any proposed Smart Auto-Battle patch. No independent execution
proof of the planner or legal target evaluation. No deliberately ineligible
**manual fallback acceptance**, PP cancellation classification, guaranteed
player-only operation, or certified overworld outcome. Repeated ineffective
Taunt behavior needs a separate source-identified moveranking/target-status
analysis; do not modify the live ROM by guessing a fix.
