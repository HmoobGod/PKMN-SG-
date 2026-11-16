# R7 R2 — Claude PR120 exact-head repair packet

Parent under review: PR120 exact `3731e94d6654f75d8547a5bf4a83e6d00de46fde`, REQUEST CHANGES.

Changes here are strictly public source-only and do not modify the original game.

## B1 — engine-owned move/PP payload contradiction

- Command19 original payload now requires 16 bytes and cross-checks 4 little-endian move IDs and 4 current PP bytes at offsets 4–15 against `R7Original.moves[]` and `pp[]`.
- Contradictory payload contents are rejected even when both snapshots agree, including the hostile all-0xAA body case.
- Fixture move/PP bytes now match the fields. Stage 17 retains its independent 4-byte minimum.

## B2 — pin surviving gate mutations

- Tests reject command19 payload lengths 4 through 15, accept length16 only as a structurally valid request that still needs a real Fight ticket, and reject header+payload consistency when both disagree with command.
- Host callback records the exact source-only sequence R, L, R. A legality callback changing PP before the second read must cause `R7_ORIGINAL_REQUEST_CHANGED`, without consuming the lease.
- Success-path tests assert all native/manual/switch/production flags remain zero on both Fight and Move and all alternate-success branches.
- `payload_matches_move_data` centralizes the command19 minimum; independent minimum checks are not duplicated so a single effective length check is pinned.

## Local source-only results

- Host fake C test: **1,231 assertions, 0 failures** with `-O2 -std=c11 -Wall -Wextra -Werror -pedantic`.
- ASan+UBSan: **1,231 assertions, 0 failures**.
- Targeted scratch mutants: length bound, header-vs-command, read/legality/read callback order, success production flag, and move+PP mismatch condition all detected.

No original-game native tests performed in this repair. No source-to-ROM ABI acceptance, manual menu acceptance, original PP causality, no-switch native certification, production authorization, merges or releases.

Formal native acceptance **0/20**. Independently review the new exact head before any combination.
