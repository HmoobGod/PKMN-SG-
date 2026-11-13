# Original actor0 / PP writer native context — targeted negative controls

This isolated **source-only draft** is stacked on independently Claude-approved
PR49 exact head `fcd708663f85ce198af4913925729fe2d7224c64`.
The parent PR49 is unchanged, still a draft and unmerged. Approval does not
transfer to this new head.

## Why this follows PR49

Claude approved PR49 source/test/security but identified one untested
failure mode: removing the `flags==4` or `battlers==2` terms from
the authentic writer guard still passed its existing 49-test audit suite.
That would allow a writer PC and matching own PP delta with the wrong
wild-single battle context to count as original in-battle evidence.
This is an evidence attribution flaw, **not** proof of gameplay execution.

## New enforced negative evidence

A new Python-only regression file exercises original Main-active,
writer-PC and own PP contexts with exactly one changed field at a time:

- `flags=0` and `battlers=0` must each fail closed independently.
- Guest `inbattle=0` must fail independently even when the other fields
  and original Main remain valid.
- A non-writer PC with a PP change must not count as an original writer.
- An apparently valid writer after the authentic Main-clear edge must fail.
- Main clear and reentry never reattributes an old actor0 candidate's PP.
- A positive synthetic case still yields only a descriptive candidate,
  never outcome, cancellation, manual fallback or production certification.

The mutation test uses the repository's `audit` function text **in memory**
and deliberately strips each writer-guard conjunct. The corresponding
invalid synthetic event then becomes accepted by the *mutant*, demonstrating
that a regression lacking the original guard would be caught by normal
negative tests. No monkeypatch or mutation is written to GitHub files, the
private ROM/save, a guest process or CI artifacts.

## Safety / acceptance

The new CI step runs `tools/test_exact_pp_writer_context_negative.py` in
the existing Source checks workflow. It invokes `audit()` with handcrafted
dicts only; never `attest()`, the emulator, original-ROM opcodes, ROM or save
bytes, or a game hook. No new game runtime behavior, AI, item, capture,
doubles, protected branch or save change.

Formal native gameplay acceptance remains **0/20 (0%)**; production **0%**;
the two historical PP-unmatched cases remain **0/2 resolved**. A real owner-
authorized same-run original CPU replay, separately reviewed and verified,
would still be required for any claims beyond source-only negative controls.

Keep this stacked PR DRAFT and unmerged pending **fresh independent Claude
exact-head review plus completed exact-head Source CI**.
