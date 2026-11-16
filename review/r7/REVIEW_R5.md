# R7 R5 — Empty move-slot success regression (source-only)

Parent: Claude-approved R7 R4 PR #123 at `40ad6131151cb1aa4d5ea0987f32e3dcfc8a8c36`.

Claude approval advisory A1: the maxPp consistency code accepts empty move slots (`move==0`, `currentPp==0`, `maxPp==0`), but earlier tests had four populated moves. A mutant rejecting every zero `maxPp` was not detected.

This follow-up changes **tests only**, plus this note. It exercises original command 17 then original command 19, using 1, 2 and 3 valid moves and zero-filled trailing slots. It proves the source-only adapter still proposes legal Fight then Move and maintains the all-zero certification outputs. The regression fails if a candidate changes the maximum-PP check to `maximum_pp==0`, regardless of whether the slot is populated.

No change to the engine adapter, original game, protected main, approved exact heads, native PP evidence or manual menu. **Not native gameplay acceptance.** Formal native acceptance 0/20; production 0%.

Further improvements (separate review heads only): source-proven one-use request ledger, stale ticket expiry/reset behavior, strict callback return values, actual original-engine provenance and manual handoff. No merges or releases.
