# R7 R3 isolated source-only PR — Claude PR121 advisories A1 / A2

**Parent PR121 (independently source-only APPROVE):**
`a6ec963f6467108a4df7509f3d5d43e184f85ce0`.
**No original ROM/save use, game execution, merges, or releases.**

## Changes for independent exact-head review

- `R7_PAYLOAD_CAP` increases 32 -> 40; command19 requires exactly 40 bytes,
  corresponding to the source-side `4 + sizeof(ChooseMoveStruct)` hypothesis.
  Reject lengths 4–39 and 41, rather than treating 16/17 as structurally
  complete. Match all bytes across two engine-source snapshots.
- Require command19 original header `[1] == doubles == 0`, `[2] == 0`
  (`NoPpNumber` false) and `[3] == 0` (reserved). This is deliberately
  restricted to auto-eligible wild singles; legitimate other requests defer.
- Preserve R2's payload move/PP binding at offsets 4–15 and source-only
  provenance limitations. 16–39 are opaque, snapshot-equality-only bytes.
- Update old shortened mock ChooseMove fixtures, add negative boundary tests,
  independently reject all three contradictory header fields and detect
  every byte of the previously truncated opaque tail changing after legality.
- Validate real source-only Fight -> full-40 Move continuity and keep all
  native / manual / no-switch / production flags false.

## Local tests (generated fixtures, never native)

- GCC `-std=c11 -O2 -Wall -Wextra -Werror -pedantic`: **1,601 assertions,
  zero failures**.
- GCC address/undefined behavior sanitizers: **1,601 assertions, zero failures**.
- Targeted scratch-copy safety mutants: **6/6 rejected** (five by explicit
  tests and one compiler rejection), including 16-byte prefix admission,
  wrong 39-byte length, dropping header[2]/[3] guards, ignoring payload tail,
  and shrinking capacity to 32.

## Outstanding, NOT fixed by R3

Host-backed request/lease authenticity, eventual lease replay memory, ticket
expiration or reset, post-read legality recheck, real manual controller
handoff, exact ROM source/ABI identity and original PP causality. Combining
R6 source-only approvals still requires a new independent combined review.
Formal native Smart Auto-Battle acceptance **0/20**, production **0%**.
