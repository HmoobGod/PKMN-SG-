# R7 R6 — interrupted-Fight and callback-reentrancy repair (source-only)

**DRAFT / REVIEW HOLD. No original game code was patched, run, or installed.**

Parent: R7 R5 PR148, exact SHA `85bcbf5ac1cec902e8033aa005aa62be6c2d0c6a`.
Independent Claude verdict on parent: REQUEST CHANGES, B1 interrupted Fight→human command→auto Move, B2 unpinned epoch and busy guards. Original R7 R4 PR123 approval and all other approved heads remain unchanged.

## Changes

- On *any* rejection, interruption, or anomalous defer while an auto Fight ticket is pending, retire the ticket **and** set the per-epoch `manual_locked` barrier. Neither a later ChooseAction nor a human-initiated ChooseMove can use the old auto ticket. The consumed-request ledger remains intact.
- After an auto Fight request id `n`, the only auto Move candidate is a command-19 request with id `n+1`, no intervening rejected/deferred planner call, within the same epoch. `UINT32_MAX` and gaps are rejected. **This is a source-only strict fail-closed ordering assumption, NOT proof of how original ROM request IDs are assigned.**
- Without a pending Fight ticket, a lack of valid move or temporarily unavailable legality remains a retryable source-model defer; other anomalies lock the entire epoch. This trades availability for safety after controller anomalies.
- Re-entrancy of plan, verified manual-takeover, or verified epoch-advance callbacks sets a sticky violation and locks the session. After a callback returns, the outer operation checks the violation before committing any lease, ticket, or boundary reset. The only recovery is a separate successful verified *higher* epoch transition.
- A source-model epoch bound is enforced at the **first original-engine read**, and again before final commit. A new epoch cannot rearm merely because the host provided another lease.
- Boundary to epoch `UINT32_MAX` is refused to preserve a possible next verified transition. Existing host-supplied boundary evidence must still equal exactly 1.

## New regression evidence (synthetic host only)

- Direct `17 (auto Fight req101) → 17 (human cancel/reopen req102) → 19 (human ChooseMove req103)` is refused; lock, ticket retirement, no lease consume, no guest action.
- 17→19 with skipped request ID also refuses even without an observed intermediate callback.
- Engine epoch 73 with session epoch 72 and **no** pending ticket refuses before legality.
- Re-entrant callbacks for planner/legality, manual takeover and epoch-advance cannot commit inner or outer automatic actions, nor silently reset a session.
- Original 64-entry ledger, strict host return checks, no-auto-switch/item/capture scope, manual-lock, and valid higher-epoch rearm are still tested.

Local source-only checks on these C sources: 2,308 cumulative mock C assertions (including 1,913 unchanged original adapter assertions), GCC and Clang `-std=c11 -O2 -Wall -Wextra -Werror -pedantic` passed; GCC ASan and UBSan passed. Local targeted scratch mutants: **18/18 caught**; targeted mutants are not an exhaustive proof. Existing CI workflow runs both adapter and lifecycle tests and denies forbidden game-artifact extensions.

## Uncertified and prohibited claims

No actual original-controller request ID source, official source-to-ROM ABI identity, engine legality, in-game manual controller, native automatic Switch exclusion, actor0 PP cause, battle outcome, or overworld return is certified here. The `R7Session` and callback evidence are host-owned; a dishonest, racing, or resetting host can bypass source-only checks. The module makes **proposals only**; there is **no guest write/emission**. `manual_locked` and `manual_defer_requested` are **not** a functioning manual menu. Original native acceptance **0/20**; production **0%**. Do not merge, install or release; do not upload private ROM/save, RAM/CPU traces, screenshots or emulator binaries. Fresh independent exact-head source/test/security review is mandatory.

## Independent review request

Re-run the original 17→17→19 hostile sequence, request-id-gap case, no-ticket cross-epoch case and all three callback re-entrancy tests. Mutate each pending-ticket lock path, request ID strict successor, the read-time and commit-time epoch guards together, and each busy guard. Review the new `quarantine()` side effects and legitimate retry behavior. Confirm no success flags imply native acceptance, no parser out-of-bounds or private artifacts, and that the exact SHA matches this new child branch.


## Independent PR149 exact-head review — 2026-11-16, REQUEST CHANGES (test coverage only)

Claude confirmed the source-only B1/B2 repairs but found two mutation-surviving gaps in
PR149 head `307e0521e4a817fd9c7ac0e59a3c0215fdf01339`:

1. A pending Fight ticket must lock and retire on **both** otherwise-benign Move
   deferral reasons (`R7_NO_ENGINE_LEGALITY`, `R7_NO_VALID_MOVE`). The
   original test never exercised their pending-ticket path.
2. No-ticket anomalous deferrals must lock and **deny the next valid request**
   for `R7_BAD_API`, `R7_BAD_ENGINE_READ`, `R7_UNSUPPORTED_SCOPE`,
   `R7_BAD_LEASE`, `R7_ORIGINAL_REQUEST_CHANGED`, and
   `R7_STAGE_CONTINUITY_FAILED`. In particular the read failure, drift, and
   doubles-path mutants must not remain uncaught. Conversely, no-ticket
   `R7_NO_ENGINE_LEGALITY` and `R7_NO_VALID_MOVE` must remain retriable.
   Reentrant-epoch rearm now also checks a new-epoch source-only Fight.

This isolated R2 child changes **only this documentation and
`test_session_lifecycle.c`**. Production C, header, engine adapter, CI workflow
and all protected heads are unchanged. The request-ID `n+1` assumption,
host-supplied boundary evidence, replay-ledger limitations and lack of a real
native ROM/menu/PP witness remain unresolved. Fresh independent Claude
exact-head source/test/security review is required, including deliberate
mutation of the pending-ticket OR clause and each anomaly-reason whitelist.
Any passing tests are synthetic, **not** native acceptance (0/20; production 0%).
