# Original C observer: independent slot/delta and enabled-assertion gates

This separate public-only research DRAFT is stacked on independently
Claude-approved PR52 exact `3d67fbab5042879b9abf210ec753db761e828c6d`.
Neither PR52 nor its approved parent PR49 is modified.

It addresses two of PR52 Claude's nonblocking advisories:
- Explicit `#ifdef NDEBUG / #error` fail-closed protection ensures that
  the C test can never pass vacuously with `assert()` disabled.
  The isolated workflow also deliberately verifies `-DNDEBUG` compilation
  FAILS before running the normal `-O2` executable.
- A deterministic fake core changes player PP **slot 1** from 10 to 7
  at the same original-looking writer CPU PC while keeping slot 0
  unchanged. The real C observer must report exactly one slot1 event,
  the authentic recorded pointer, and raw **-3** delta, not silently
  synthesize a slot0/-1 event or label it as an authenticated native
  PP debit. It remains purely descriptive.
- An additional Main bit0-only change from 2 to 3 must never
  manufacture an original Main battle-bit1 exit edge.

This supplements PR52's five existing fake-core modes. It does not
change the C observer implementation, commercial game data, CPU
capture, guest state or any automatic battle behavior.

C-to-Python end-to-end original-ROM correlation remains unimplemented
and must not be inferred from these synthetic C tests.
Source-only fake-core success does not establish original player0
native auto moves, legality, PP debit/cancellation, battle outcome or
fallback. No private ROM/save staging/execution, AI edits, items,
capture, enemy/NPC partner or uncertified doubles.

Formal original-game acceptance 0/20 (0%); production 0%;
historical unmatched PP causes 0/2 resolved. Keep DRAFT/unmerged
pending exact-head CI and new independent Claude source/test/security
review. No approval transfers from PR52 or PR49.
