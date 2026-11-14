# Original engine-owned player0 request copy — 44-byte poststore trace integrity

**Purpose:** improve the *specific original engine request* CPU witness
needed before any native automatic move can be accepted. This is a
standalone SOURCE-RESEARCH draft from protected source-first snapshot
`655d2430c5891c12bbf4bc526b9f98f1468d433b`, not a live game mod.

Previous authentic original-game evidence identifies original player0
copy entry at raw CPU PC `0x0806B372`, 44-byte source request opcode
`19`, original store marker raw `0x0806B3C0` and post-copy PC
`0x0806B3C8`. The existing read-only C collector
`tools/alternate_mgba_capture_player_copy.c` recorded 44 matching
pre-store registers and checked final source/destination equality,
but **did not inspect destination bytes after each original CPU store**.
A fake core could skip one store and still appear complete when
destination contents happened to match. Further, `buffer+16` was
computed before validating the source buffer pointer, risking
integer-wrap EWRAM aliasing.

## Source-only patch behavior

- Retain the existing entry/store/post CPU PCs, 44-byte shape, exact
  player0 ownership/length, non-overlap, saved source/destination
  snapshots, result `Proof` binary layout and original no-input,
  no-emission semantics.
- Validate the engine buffer pointer is in EWRAM and has enough room
  for 16-byte header + 44-byte request **before** adding the offset,
  preventing an invalid `0x01FFFFF0+16` from masquerading as EWRAM.
- Report the exact count of CPU steps performed at the final observed\n  POST_PC; the previous recorder incorrectly included that unstepped\n  post-copy observation as an extra instruction.\n- Count a candidate store only **after** the original CPU `step()`
  returns and the actual destination byte equals the expected
  pre-instruction value. The captured sequence is not merely 44
  matching PC/register observations before execution.
- Fail closed on decreasing frame counts, missing mGBA callbacks,
  oversized frame/step budgets and invalid source/opcode.
- Use `memcpy` to load possibly unaligned mGBA callback pointers,
  preserving the guest ABI and avoiding misaligned typed dereferences.
- An assertion-enabled fake-core test executes the actual read-only
  tracer against a public 44-byte synthetic program: complete
  copy, skipped store, original request opcode mismatch, invalid
  wrapped buffer pointer, wrong source register, backward clock,
  incomplete step budget, too-large capture window and missing
  callback. Full public Source CI executes the C fixture.

**Limits:** A post-step destination byte equal to its expected value
does NOT by itself prove that a store instruction executed if the
previous byte was already equal. The raw observed PC still requires
exact original modified-ROM instruction opcode attestation in an
owner-authorized local replay. Nor does a completed 44-byte request
copy establish unique one-use engine ownership, legality of the
chosen move/target, a consumed action, PP debit/cancellation,
battle outcome decision, overworld return or manual fallback.
The observer produces read-only *candidate* evidence only.

Never publish original private request buffer bytes. Protected
Current ROM/save, original modified ROM, main/source-first and
independently approved exact heads remain untouched, unexecuted
and unmodified. No NPC/foe AI, auto items/capture or uncertified
trainer/doubles changes.

**Native formal acceptance 0/20 (0%)**, production auto-battle 0%,
historical unmatched PP causes 0/2. Keep new branch DRAFT/unmerged,
pending exact-head full CI and new independent Claude source,
test and security review. No approval transfers from existing PRs.
