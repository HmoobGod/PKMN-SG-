# Public C observer → Python audit integration (synthetic only)

This isolated research DRAFT is stacked on PR53 exact
`2203716a76a17b16b86a3f44169632983ec2ad55`, which is
**review pending**, itself based on the independent Claude-approved
PR52 head `3d67fbab5042879b9abf210ec753db761e828c6d`.
No approval transfers to this branch.

## Why this matters

Earlier evidence gates ran independent C fake-core and Python
handwritten-event tests. This could miss differences between the
**actual C observer output** and the event schema consumed by the
strict original player0 attribution verifier. Claude flagged this
coverage gap on PR52.

The new `test_exact_joint_c_to_python_bridge.c` runs the actual
`sg_trace_exact_joint_player_terminal()` against the existing
memory-only fake core; it emits precisely observed C event fields,
initial/final memory snapshots, and bounded step metadata in a
**public synthetic bridge schema**.

The new `test_exact_joint_c_to_python_bridge.py` compiles that exact
C exporter with host compiler warnings as errors, runs seven
deterministic modes, parses the JSON and sends each exact C event
dictionary to existing `verify_exact_joint_player_terminal.audit()`.
It never calls `attest()` or opens private bytes. The audit envelope
uses constant SHA labels **only to satisfy the test schema**; it is
NOT original SHA attestation or a genuine original CPU capture.

The test asserts:
- A complete fake original-looking actor0 sequence and PP event
  are only descriptive, with ALL promotion/certification flags false.
- Actual C outputs with wrong wild flags, battler count or inactive
  Main reject under the Python audit.
- A fake original writer PC with **no PP change** does not invent
  a PP event or a writer attribution.
- Real C recording of slot1 PP `10 → 7` (-3, not -1) cannot
  become an authenticated original writer debit.
- A Main bit0-only change `2 → 3` cannot fabricate a Main
  battle-bit1 terminal or later-callback evidence.
- Altered C event ordering, RAM address, PC, final PP snapshot
  or unknown event shape is rejected.
- An unrecognized C bridge mode fails and `-DNDEBUG` cannot
  compile any fake-core assertions away.

## Boundary and status

New changes are one C exporter, one Python bridge suite, two
source-only CI wiring changes and this document. No change to
the game's source patch, Python attribution policy, C observer,
protected original/current ROM or save, main/source-first or any
approved exact head. No emulator, private staging or guest execution.
No auto items/capture, enemy/NPC-partner AI, or uncertified doubles.

**Full actual-game native acceptance 0/20 (0%)**, production
Smart Auto-Battle **0%**, historical unmatched PP classifications
**0/2 resolved**. This is a test-coverage improvement only.
Hold DRAFT/unmerged pending completed exact-head CI and a NEW
independent Claude source/test/security review. Any change to the
SHA resets previous approval; original-game certification remains
separately blocked on an authorized owner-local same-run CPU witness.
