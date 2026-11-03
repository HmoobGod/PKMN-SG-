# Revision 16266R4 — request-scoped lease reference model

This is a **research-only, ROM-free C state machine**. It does not implement automatic Smart AI or modify the game. The model cannot produce positive player ownership or complete move/target legality evidence. The Current ROM/save and experimental 16266 ROM remain unchanged.

## Contract

Two different native requests can carry the same 44-byte contents. Track a new request by an observed original engine buffer-A copy event, **not** a payload hash, pointer, pending bit, opcode, or cache byte. The model increments a monotonic host-local generation on an eligible actor-0 opcode19 copy; any other actor-0 buffer-A event invalidates the previous lease. Original completion/cancellation closes the matching lease; stale mismatched completion fails closed. Other-battler copies cannot create an actor-0 lease. Duplicate claim fails. Epoch exhaustion poisons permanently rather than wrapping.

`sg_lease_claim_model` evaluates **hypothetical** positive requirements for fresh engine copy, exclusive player ownership, complete move and target legality, and exclusive native emission. None of these positive certificates currently exists in the 16266 scorer. Supplying true booleans in a standalone test is **not** engine authorization. The code is never linked into the game, has no native emitter call, and cannot produce gameplay commands.

## Tests

```sh
python3 tools/test_choice_lease.py
# Optional, previously saved local reports only:
python3 tools/replay_choice_lease.py /private/SoulGold_16266_Lifecycle_Evidence.json
```

C model tested with optimized and UBSan host compilation. Synthetic tests deny missing certificates, stale epochs, duplicate claims, wrong actor/controller/context, invalid move/target, zero PP, untrusted copies, cancellation/replacement, invalid terminal and sequence overflow. The optional replayer uses the previously merged observer validator first, then maps recorded copy/completion events into this dry-run model. It **does not** claim any lease. Its seeded request is explicitly modeled because the original enqueue occurred before attaching the observer. Private reports stay local and are not embedded in GitHub.

## Remaining blockers

1. Prove a safe engine-bound observer of actual original buffer-A copies with actor/session provenance, link behavior, preservation of native register/memory state, and stack/IRQ budget.
2. Prove exclusive player ownership and complete move/target/restriction authority without side-effecting validator calls or unauthorized hidden opponent reads. NPC-partner and trainer doubles remain separately uncertified.
3. Integrate only after original engine rejection/confirmation semantics, exactly-once submission and real natural battle tests are independently certified.

No gameplay changes, no Current ROM promotion, no phone certification. Native automatic acceptance **0/20**; experimental ROM revision remains **16266**.
