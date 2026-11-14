# Original outcome / PP instruction observer: fail-closed capture integrity

Independent source-research draft based on unchanged protected
`source-first/rom-identity` exact commit
`655d2430c5891c12bbf4bc526b9f98f1468d433b`.
This does **not** touch main, Current ROM/save, existing approved PR
heads, any game or battle controller implementation, opponent/NPC AI,
items/capture, or uncertified doubles. Do not execute private inputs.

## Concrete evidence-integrity defects

The older original outcome/PP C tracer used
`if (f - start_frame >= frames)` on unsigned `uint32_t` frame values.
A clock rollback (for example, start=3200, later=3199) underflows,
making a capture appear `status=1` (completed), even though the
requested frame window was never observed. It also emitted
`pc-2` for native instruction provenance without checking whether
raw CPU PC was a legal, aligned GBA Thumb execution address. A bogus
zero/odd PC could be recorded as an original-looking event or silently
enter the downstream evidence chain. Both are research evidence
validity hazards, not diagnosed commercial-game bugs.

The original C observer additionally accepted arbitrary output capacity
and frame window even though the corresponding offline audit and
owner-local trace format have fixed limits, and used potentially
unaligned function-pointer casts to access established mGBA callbacks.

## Narrow source-only correction

- Check `f < start_frame` and `f < previous_frame` **before** the
  subtraction or any CPU step. A clock rollback returns explicit
  `status=5`, never completed. Check the final frame as well.
- Require aligned, within-range GBA ROM/EWRAM/IWRAM Thumb
  **raw PC+2** before any memory-edge label or CPU marker. Invalid
  CPU PC returns explicit `status=6`, not a pseudo writer or terminal.
  The ranges are deliberately conservative: other execution sources
  require a separate provenance protocol, never guessed permissively.
- Enforce capacity 1..2048 and requested frame window 1..10000,
  instruction steps 1..0xFFFFFFFF. Keep existing distinct overflow,
  budget-exhaustion and malformed-input statuses.
- Copy mGBA ABI function pointers with `memcpy` instead of directly
  dereferencing a potentially unaligned function-pointer location;
  reject any missing method immediately, before reading guest state.
- Preserve old known original RAM watchers, source-only
  `SG_OUTCOME_CANDIDATE` non-certifying semantics and all tracer
  event fields. Do not infer the actual outcome byte's RAM address.

A new C fake-core test runs the **real** compiled observer without
any original ROM or game state. It covers monotonic success,
underflow past the start, in-window frame rollback, invalid initial and
later CPUs PCs, overflow, oversized capacity/window, missing callbacks,
forbidden candidate addresses, and acceptable ROM/RAM PC ranges.
The existing public Source CI executes this test under strict host
compiler warnings-as-errors and standard assertions enabled.

## What this does NOT establish

The only real blocker on next gameplay acceptance is **still**
an independently owner-authorized same-run exact modified-ROM CPU
capture proving the engine-owned player0 request, effective move/target
legality, native PP or cancellation, result-decision PC, full
overworld transition and safe manual fallback. No private byte,
savestate, emulator/core or trace is staged or executed in this PR.
Original `gBattleOutcome` address is still UNKNOWN. The two
historical PP-unmatched submissions are still unclassified.

Formal actual-game acceptance: 0/20 (0%).
Production Smart Auto-Battle acceptance: 0%.
Unmatched PP classifications: 0/2.

Keep DRAFT and unmerged until exact-head Source CI is fully green
and a new independent Claude source/test/security verdict is received.
No previous exact-head approval transfers to this unrelated branch.
