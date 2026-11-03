# Revision 16266R4 — request-scoped lease reference model

**R8 correction (November 3, 2026):** The R7 live copier shows pending bit0 is still clear on completed original 44-byte actor0 copy and becomes set 23 guest instructions later. The research-only model now uses **STAGED** for the completed copy; it becomes **OPEN** only after `sg_lease_on_original_pending` sees the matching original actor0 pending transition and same request, so model claims before pending are impossible. This does not supply an engine-owned epoch, exclusive player ownership, move/target legality or native emitter permission. See [R8_PENDING_OWNER_CONTEXT.md](R8_PENDING_OWNER_CONTEXT.md).


**R5 correction:** The historical R4 optional replayer passed `original_copy_executed=True` for records taken at the **0x0806B370 copier entry**. Those records did not observe post-loop completion. The R5 replayer now passes `False`, yielding six valid historical ledgers but **zero certified copy events and zero leases**. R4's C lease tests remain valid as *hypothetical* unit tests, not runtime authority. See [R5_COPY_BOUNDARY.md](R5_COPY_BOUNDARY.md).

This is a **research-only, ROM-free C state machine**. It does not implement automatic Smart AI or modify the game. The model cannot produce positive player ownership or complete move/target legality evidence. The Current ROM/save and experimental 16266 ROM remain unchanged.

## Contract

Two different native requests can carry the same 44-byte contents. Track a new request by an observed original engine buffer-A copy event, **not** a payload hash, pointer, pending bit, opcode, or cache byte. The model increments a monotonic host-local generation on a completed actor-0 opcode19 copy and stages the lease; only a paired later pending event can open it. Any other actor-0 buffer-A event invalidates the previous lease. Original completion/cancellation closes the matching lease; stale mismatched completion fails closed. Other-battler copies cannot create an actor-0 lease. Duplicate claim fails. Epoch exhaustion poisons permanently rather than wrapping.

`sg_lease_claim_model` evaluates **hypothetical** positive requirements for fresh engine copy, exclusive player ownership, complete move and target legality, and exclusive native emission. None of these positive certificates currently exists in the 16266 scorer. Supplying true booleans in a standalone test is **not** engine authorization. The code is never linked into the game, has no native emitter call, and cannot produce gameplay commands.

## Tests

```sh
python3 tools/test_choice_lease.py
# Optional, previously saved local reports only:
python3 tools/replay_choice_lease.py /private/SoulGold_16266_Lifecycle_Evidence.json
```

C model tested with optimized and UBSan host compilation (R8: 104 assertions in each configuration). Synthetic tests deny missing certificates, stale epochs, duplicate claims, wrong actor/controller/context, invalid move/target, zero PP, untrusted copies, cancellation/replacement, invalid terminal and sequence overflow. The optional replayer uses the previously merged observer validator first, then maps recorded copy/completion events into this dry-run model. It **does not** claim any lease. Its seeded request is explicitly modeled because the original enqueue occurred before attaching the observer. Private reports stay local and are not embedded in GitHub.

## Remaining blockers

1. Prove a safe engine-bound observer of actual original buffer-A copies with actor/session provenance, link behavior, preservation of native register/memory state, and stack/IRQ budget.
2. Prove exclusive player ownership and complete move/target/restriction authority without side-effecting validator calls or unauthorized hidden opponent reads. NPC-partner and trainer doubles remain separately uncertified.
3. Integrate only after original engine rejection/confirmation semantics, exactly-once submission and real natural battle tests are independently certified.

No gameplay changes, no Current ROM promotion, no phone certification. Native automatic acceptance **0/20**; experimental ROM revision remains **16266**.
