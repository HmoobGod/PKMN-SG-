# Independent R7 R4 exact-head review request — source-only

Parent is independently Claude-approved R7 R3 PR122 SHA
`43b96ac451c3d777a00b7c6dfacea65fc9f02907`.

## Changes

1. Require `ChooseAction` command17 to have `payload_length == 4` (source
   `BtlController_EmitChooseAction` transfers exactly four bytes). Test lengths
   0 through 41 and ensure no automatic proposal or lease consumption on
   malformed lengths. The action/item header bytes remain uninterpreted but
   are compared across the two engine-source snapshots.
2. For `ChooseMove` command19, source `ChooseMoveStruct.maxPp[4]` follows
   `currentPp[4]` at buffer offsets 16..19. Defer if `maxPp < currentPp`
   or a populated move has no max PP capacity. Test all four slots, values
   both consistent and contradictory, changed host/current PP and tail drift.
3. Preserve all previously approved R7 R3 guards, R5 reference C guard,
   original player0-only scope and `R7_DEFER` no-action sentinel; no native
   certification or manual-menu claim.

## Independent review demands

- Verify the source-layout assumptions against the original symbolic code,
  and **do not treat the source archive as an exact-ROM ABI witness**.
- Run the entire fake-only R7 C suite, GCC/Clang pedantic checks, ASan/UBSan
  if supported, and mutation tests that remove the command17 length and
  maxPP checks. Check the 0-current PP with nonzero maxPP case.
- Ensure no underflow, 16/40-byte off-by-one, auto-Switch or item action,
  false certification flags or silent ticket/lease mutation on defer.
- Treat all source-only results as simulated. Formal native acceptance stays
  **0/20**, production **0%**, no merges/releases and no private game data.

This follow-up does not implement ticket expiry, consumed-request memory or
original manual-menu fallback. These require independent design and testing.
