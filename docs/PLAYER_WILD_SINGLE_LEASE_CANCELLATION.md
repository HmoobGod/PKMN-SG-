# Player-only wild-single source-LAB: invalidate interrupted requests

Status: **disposable upstream source-LAB candidate, not installed in Current ROM**. The exact privately modified test ROM SHA-256 `4b2585e1…d3ee44` is **not** in this lab. Source-CI and GNU ARM compilation do not certify a playable mod, save compatibility, or engine-owned native epochs.

## Change

The original source-LAB patch held a temporary auto-action lease from `CONTROLLER_CHOOSEACTION` until `CONTROLLER_CHOOSEMOVE`. Previously the lease was reset when a *new ChooseAction* arrived but not when an unrelated controller command interrupted the staged move. This batch adds a no-side-effect cancel call **before dispatch** on every active player controller command other than `CONTROLLER_CHOOSEMOVE`. `PlayerHandleChooseAction` also invokes the same cancellation helper before a fresh proposal. The helper only resets the lab lease flag; it does not emit a reply or intercept existing controller execution.

The lease now snapshots the active **party index** along with owner, opponent, four move IDs and four PP bytes. Consumption is destructive *before* legality probes; if the party slot changed, no automatic move reply is emitted and the existing manual engine path continues. Final move reply still checks `CheckMoveLimitations` with `MOVE_LIMITATIONS_ALL` (covering dynamic restrictions through the source engine), target type and target legality, original ChooseMove command and exposed move-ID/PP consistency. Do not run the limitations probe during ChooseAction preflight because it may have side effects; preflight is intentionally speculative.

## Not certified

This local lease is not an engine-issued request epoch, does not prove that every dynamic effect in the user's custom modified ROM is handled by the upstream code, and cannot ensure all cancellations are observable through player controller dispatch. Only real exact-modified-ROM instruction and request ownership traces can establish these claims. Zero legal moves, missing opcode, non-wild modes, other actors, invalid target, inBattle false, and terminal outcome all **fail closed to the original manual fallback**, not to an invented Struggle or auto item/capture.

The previous 3 natural wild fixtures, 13 original player0 move submissions and 2 PP-unmatched submissions remain historical; no new native CPU replay is claimed. A separate full unattended outcome->field->next-battle certification with all 20 real acceptance tests and independent review is required before Current ROM promotion.

## Validation

1. `python3 tools/test_wild_single_lab_contract.py` and `python3 tools/test_wild_single_cancel_request.py` under Source CI (unit tests use a synthetic state model and mutation/structure checks).
2. The **existing pinned** disposable GNU ARM lab workflow applies `source-first/wild-single-lab.patch` to original upstream SHA `3f4d90aa8f8bc50054c817d7bd59fcdfcfb4933d`, with battle_controller_player.c SHA `deb649e441dd28909ade7053119b4af29450c9686e43000f319149d44c43e594`. The apply check, exact single-file diff gate, and build must pass at the **new exact head** before calling this source-LAB patch build-verified.
3. Preserve `main`, protected Current ROM `7b9ac66d…`, save `8c6cb520…`, foe/NPC partner logic, and all user manual inputs when the contract cannot be proven.
