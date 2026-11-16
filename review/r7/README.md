# Pokémon SoulGold R7 — public source-only engine adapter and compatibility review

**STATUS: DRAFT / UNVERIFIED / NOT INSTALLED. Original-game native acceptance 0/20.**

This draft intentionally changes **no emulator, ROM, save, or gameplay**. It introduces
an adapter contract that a *future*, independently validated integration must fulfil
using the actual original player-controller buffer, original current-turn move
limitations and targeting helpers, and an authentically engine-issued request.

It does **not** call any game function, access guest memory, emit a battle response,
change an enemy or NPC partner, open a manual menu, or assert a native win.

## Dependency and precise scope

- Source/test baseline: Claude source-only approved **R5 R3 PR117** exact
  `228255138e70692d87af9b023c9608973f481ba3`.
- Uses `review/r5/source-first/player0_fail_closed_guard.{h,c}` *as a reference*.
- Approved R6 sibling models are NOT merged into this branch. It is a separate
  composition candidate with a fresh independent review required. The R6 reviews
  (PR102, PR108–114, PR118–119) have no inherited native evidence.
- Additional source-first public lab PRs remain independently gated.
- R7 writes only `review/r7/` and its own source-only CI workflow.

## Security contract

`r7_plan` obtains two snapshots around the *required* original-engine legality
callback. Snapshots include original header/payload bytes, move IDs/PP, owner,
party, foe, turn, request ID/epoch, resources and controller flags. Every field
must remain unchanged. It then requires the approved R5 guard to return the
same legal slot across ChooseAction (17) and ChooseMove (19). A one-use lease is
consumed only on a successful source-only proposal; overlapping Fight stages
are rejected. The only output actions are 0 (Fight) and 10 (Move). No API can
request or emit Switch, items, capture, forced-switch acceptance or a guest write.

### R7 R2 — original ChooseMove move/PP binding (review pending)

For command 19, `r7_plan` now requires at least 16 original payload bytes,
then decodes the four move IDs from original-buffer bytes 4–11 as four
little-endian 16-bit integers and PP from bytes 12–15 as four bytes. All eight
host-exposed `moves[]` / `pp[]` values must **exactly match those original bytes**
before the legality callback runs. The two independently read original snapshots
must then remain byte/field-identical after the callback. Command 17 retains its
own 4-byte minimum; its move/PP side fields are not asserted to come from a
ChooseMove buffer. Tests reject mismatched host move arrays, mismatched PP,
corrupted body bytes (even if both snapshots match), command19 length 4–15,
header and payload agreeing with each other but not with the declared command,
and legality helpers that mutate PP before the second read. Source tests also
pin the `read → legality → read` callback order and all success-path native,
manual, switch and production flags to zero.

This **proposed binary layout** follows user-supplied
`soulgold-master/src/battle_controllers.c` (`BtlController_EmitChooseMove`) and
`include/battle_controllers.h` (`ChooseMoveStruct`). An independently verified
exact-ROM ABI/symbol map is still required before trusting any offset as native
evidence. A host fabricating both snapshots can still fool source-only tests.
No original game functionality has been modified or installed.

If any guard fails, the *plan* returns `R7_DEFER` with no-action sentinels.
`manual_defer_requested=1` is **NOT** evidence of a functioning original menu.
All four native, manual, no-forced-switch and production flags remain zero in
all cases, including successful source-only mock transactions.

The `read_engine_legality` callback and input `R7Original` are **not trustworthy
by virtue of their types**; a future adapter must independently authenticate
that its data came from the actual original engine. The source-only mock tests
cannot prove this.

## Running tests (public fake data only)

```sh
cc -std=c11 -Wall -Wextra -Werror -pedantic \
  review/r7/engine_adapter.c review/r7/test_engine_adapter.c \
  review/r5/source-first/player0_fail_closed_guard.c -o /tmp/sg-r7-source-test
/tmp/sg-r7-source-test
```

See `ENGINE_AND_NATIVE_GATES.md` for the unresolved original-game integration
points and *explicit evidence required* before any formal acceptance.

No ROM, save, EWRAM dump, CPU trace, screenshot, emulator binary, or private
execution log belongs in this PR or its CI.
