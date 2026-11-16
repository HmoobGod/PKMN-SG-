# R7 R6: persistent one-use request ledger and fail-closed ticket quarantine

**SOURCE-ONLY RESEARCH MODEL.** This module has not been linked into the uploaded ROM, has not executed inside original gameplay, and provides **zero native acceptance evidence** (formal **0/20**, production **0%**). It never emits a game command, switches a Pokémon, uses items, captures Pokémon, modifies guest memory, or invokes the original manual menu.

## Purpose

`lifecycle_adapter.h/.c` wraps the previously reviewed `r7_plan` as an independent **stateful** entry point. The earlier primitive accepts caller-created `R7Lease` structs; a new caller-owned lease could replay the same request ID. R7 R6 retains up to 64 consumed request IDs within a pinned battle epoch in `R7Lifecycle`, disallowing a replay despite a fresh lease. Its result includes a separate `R7LifecycleReason` while preserving `R7Plan`'s no-action sentinels and zero certification flags.

The wrapper calls an original-request callback once, internally supplies its pinned snapshot as the primitive's first read, invokes the legality callback, and obtains the primitive's second original-request read. The **read → legality → read** order is preserved; the wrapper does not accept non-1 callback success values. It advances the ledger **only after** a successful source-only Fight or Move proposal and consumed local lease. A rejected proposal never creates or consumes a successful ledger entry.

## Sticky manual-defer barrier

After *any* primitive defer with a readable epoch, any duplicate request ID, any missing callback after activation, any invalid engine read after activation, an explicit abandonment, a 64-request ledger overflow, or an observed epoch advance, the session becomes **quarantined**. While quarantined, calls always return a `R7_DEFER` plan with `R7_NO_ACTION`, `R7_NO_SLOT` and `manual_defer_requested=1`, and do not invoke an original command again. A prior pending Fight ticket is retained, not quietly discarded.

An observed new epoch alone does not resume automatic moves. `r7_lifecycle_rearm` requires all of:

- The previous epoch match and a strictly newer proposed epoch.
- Host-reported original battle finished, original controller rearmed and original response queue empty, each **exactly 1**.
- A fresh original-request read returning **exactly 1**, with matching new epoch, player battler 0, command 17 and wild-single non-partner scope.

Only then are the ledger, ticket and quarantine cleared for a new epoch. **Those booleans are external host assertions, not authenticated native witnesses.** There is no safe time-based expiry, and no same-epoch automatic reset. An honest original-engine integration must independently prove the battle outcome, controller ownership, empty response queue and return to human control before interpreting this rearm as safe. The new epoch cannot inherit a previous battle's request IDs as authenticated engine identity without further proof.

## Scope and non-goals

This is a wrapper around the unchanged `r7_plan` model, not a reviewed combined R5/R6/R7 native integration. Direct calls to `r7_plan` bypass this wrapper; a future native installer must enforce the entry-point boundary, persistence, and real original-engine provenance and must **not** rely on caller booleans. Process restart or state reinitialization could bypass the ledger, so persistence/engine-issued request identity remain unproved. `manual_defer_requested` is **not** evidence that a visible, controllable original menu exists. A real game must demonstrate player0-only legality, PP causality, no forced Switch response, and a human-usable menu independently.

## Tests (generated inputs only)

```sh
cc -std=c11 -O2 -Wall -Wextra -Werror -pedantic \
  review/r5/source-first/player0_fail_closed_guard.c \
  review/r7/engine_adapter.c review/r7/lifecycle_adapter.c \
  review/r7/test_lifecycle_adapter.c -o /tmp/r7-lifecycle
/tmp/r7-lifecycle
```

The independent new suite covers: Fight→Move within one epoch; duplicate Fight and Move replay with a new local lease; sticky quarantine after defer; pending ticket retention; epoch transition without silent reset; hostile recovery evidence; strict non-1 callback results; callback-induced request drift; ledger overflow; manual abandonment; and certification flags remaining zero even on successful mock proposals. The inherited `test_engine_adapter.c` remains unchanged.

**No ROM, save, RAM dump, CPU trace, emulator binary, screenshot or private game information belongs in this source-only PR.** All merges, installation and releases remain prohibited without separate authorization.
