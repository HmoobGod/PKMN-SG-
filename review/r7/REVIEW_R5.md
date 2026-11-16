# R7 R5 — one-use identity ledger and conservative ticket retirement

Status: DRAFT / SOURCE-ONLY / NOT INSTALLED. No native acceptance (0/20).

Parent: independently Claude-approved R7 R4 PR #123 exact `40ad6131151cb1aa4d5ea0987f32e3dcfc8a8c36`. Parent and earlier approvals remain untouched; this is a standalone child review, not a combination with any R6 sibling draft.

## Changes

1. Adds `session_lifecycle.h/.c` as a wrapper around **unchanged** `r7_plan`. A bounded session-owned 64-entry consumed `{epoch,request_id}` ledger is checked at the first original-buffer read, independent of a caller reissuing a fresh zero-consumed lease. Entries are committed **only after** a successful R7 proposal and consumed lease. A full ledger defers without eviction, callback invocation or guest write.
2. Stores the Fight ticket in the wrapper session, checks the original epoch and retains ticket/ledger across failure. An unrecognized new epoch never clears a pending ticket.
3. Adds a *model-only* verified-boundary API requiring `from_epoch` match, strictly increasing `to_epoch`, original battle closed, original controller idle and an external observer callback returning **exactly 1**. Only this API may reset the session ledger and pending ticket. There is no wall-clock timeout or implicit expiration.
4. Adds a *model-only* verified manual-takeover API requiring an explicit callback to report that the original manual controller has a **controllable menu** for the pending ticket. A successful source-model takeover retires the ticket but **locks the remainder of that epoch to manual**. It does not certify that a native manual-menu path has been found.
5. Public initializer refuses to reinitialize an already initialized session; host-managed memory stability remains a prerequisite. The wrapper keeps its ticket/ledger and the caller lease transactional on any failed proposal.

## Independent verification requested

- Recreate a fresh `{epoch,request_id,consumed=0}` lease after a successful Fight or Move; verify replay is still denied and no legality callback runs.
- Try `r7_session_init` to erase the ledger; verify no reset. Exhaust exactly 64 accepted requests, then confirm the 65th fails without a callback, and no historical ID is evicted.
- Check a pending Fight ticket cannot be silently cleared by a new epoch read, a failed/return-2 boundary callback, equal/decreased epoch, wrong source epoch, missing battle-closed or controller-idle evidence.
- Check accepted manual-takeover callback removes pending ticket but locks further automation for the full epoch; only a verified higher-epoch boundary unlocks it.
- Check failures preserve caller lease, ticket, ledger and manual lock; parent R7 R4 tests and safety/non-certification flags still apply.
- Challenge callbacks that fabricate evidence or mutate session memory; the source-only host callback is not original-engine attestation and the exposed C `R7Session` can still be replaced by a malicious or buggy host. Do **not** certify as tamper-proof one-use semantics.

## Testing and security

Local GCC and Clang `-O2 -std=c11 -Wall -Wextra -Werror -pedantic`, GCC ASan/UBSan: 2,223 cumulative C assertions, zero failures, on generated fake engine records (the baseline contributes 1,913). The new workflow explicitly runs the lifecycle test in addition to the original adapter test.

**No private game data**: no GBA/save, binary/ELF, emulator, EWRAM, PP dumps, CPU traces or screenshots have been used or transferred in the new source-only files. Human inspection still required before public publication. No modification, installation, merge or release.

**Native/production**: 0/20 and 0%. No actual-ROM ABI attestation, engine ownership mapping, functioning original manual UI, automatic forced-switch exclusion or observed original PP causality. Only the existing local host callback contract is modeled; nothing in the code sends an automatic action to the emulator.
