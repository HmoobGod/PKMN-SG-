# Native choice lifecycle — 16266 evidence follow-up

No shipped-code or ROM change. These are local mGBA observations, not independently reproduced acceptance or permission certificates. Human confirmation remains required; automatic Smart AI acceptance stays0/20.

## Boundaries measured

The tracer follows actor0 through original engine paths:

1. Buffer-A opcode19 copied by0x0806B370: a new observed move request.
2. Native emitter0x0806BD80 called once for subcommand10.
3. Buffer-B reply copied by0x0806B370: six bytes, with the submitted payload matching the emitter argument.
4. Non-link completion at0x0806261C: actor pending bit clear and run callback restored to0x080619D5.
5. Original consumer calls its restriction check and returns at0x08094330.
6. On return0, the observed slot/move/target commit markers occur in order. On return1, they do not occur for that request.

The validation call site is shared by battlers. The tracer checks actor r0 against the consumer's r6 at check entry and filters the return/commit markers to actor0. A return from the opponent must not be attributed to the player's last submission.

Request IDs in these reports are **host observation counters**, incremented at a new observed opcode19 copy. They are not native fields, cryptographic tokens or permission receipts. Each process starts from an already-queued request in a saved hook state; that first request is seeded explicitly. Its original enqueue is not observed.

## Six fresh processes

| Case | Requests including seeded request | Submitted | Native result |
|---|---:|---:|---|
| Confirm | 2 | 1 | 1 accepted |
| B-cancel and re-enter | 3 | 2 | 1 cancellation, then1 accepted |
| Late Disable fixture | 3 | 2 | 1 rejected, then1 accepted |
| Late Encore fixture | 3 | 2 | 1 rejected, then1 accepted |
| Late repeat restriction fixture | 3 | 2 | 1 rejected, then1 accepted |
| Late PP0 fixture | 3 | 2 | 1 rejected, then1 accepted |

Totals: **17 request lifetimes** (6 seeded,11 observed new requests), **11 submissions**, **11 matching reply copies**, **11 completions**, **6 accepted**, **4 rejected**, **1 cancellation**. Every submitted lifetime has exactly one emitter, reply copy and completion in these runs. Accepted requests have all three commit markers; rejected and cancelled requests have none. The final open request in each process is left waiting, not counted as a submission.

Confirm and cancel use ordinary buttons. Late restrictions are explicit mutations of disposable own-battler RAM; the subsequent rejection and recovery are native engine behavior. No command buffer, request field, PC or native function call is injected by the tracer. This is one fixture, not natural Disable timing or general gameplay certification.

## Identical contents do not identify a request

All11 observed new move requests are44-byte copies in this pinned version. After cancel, Disable, Encore and repeat rejection, the first recovered request's44-byte contents have the same SHA256 as the seeded request. They are different native requests despite identical payloads. PP0 changes the visible PP payload, so that recovery differs.

A payload hash, pointer, opcode and pending-bit value therefore cannot serve as a unique choice-epoch token. The observer's serial IDs distinguish the actual new copy events; attaching those host IDs to a future ROM proposal would not make them engine authority.

## Cache timing remains limited

The cached restriction byte is0 at the first recovered request copy in all four late-restriction fixtures. Later requests sometimes update it. This supplies a concrete reason to keep the cache negative-only: a clear byte did not prevent native rejection. The live Disable/Encore/repeat/PP checks already serve a different role in the preview. No natural-restriction freshness claim follows.

## Reproduce with private inputs

```
LD_LIBRARY_PATH=/private/runtime:/private/compat python3 tools/probe_choice_lifecycle.py --case cancel --rom /private/SoulGold_16266.gba --save /private/Soulgold.sav --state /private/genuine_wild_hook.ss --bridge /private/mgba_bridge_16187.so --runtime /private/libmgba.so.0.10 --output build/lifecycle/cancel.json
```

Cases: confirm, cancel, late_disable, late_encore, late_repeat, late_pp0. The source pins all five input identities and checks the private debugger ABI before installing callbacks. Source hashes, timestamps, elapsed times and event records are retained in the reports. Public CI has no private inputs and does not execute this probe.

## Consequence for the adapter

Keep a proposal local to the current request; do not retain a recommendation across cancellation or a new request just because the payload matches. A future synchronous adapter should preserve the original one-reply/one-completion path and native rejection recovery. These observations test that protocol for existing human-confirmed choices; they do not authorize an automatic adapter.

Further static research identified a stored move-lock read from `*[0x02001ABC] + 0x17C + 2*actor` in the native validator. Its applicability depends on effective choice-item or trait checks, not just a nonzero stored move. That condition is not yet modeled by the preview. An unconditional stored-lock filter would risk rejecting legal recommendations, and invoking the side-effecting validator an extra time is not a valid shortcut. Effective lock classification and complete target/ownership permission remain open.

## A recovery flag is not an epoch either

The tracer also records the actor0 byte at `*[0x02001ABC] + 0x17`, which the observed rejection path clears with mask0x10. In these runs it is0 at the first submission,0x10 at recovery after all four constructed rejections, and0x30 at the subsequent turn request. Confirm/cancel controls reach0x20 at the next turn. Thus the recovery bit persists into the next observed turn. It cannot be treated as a unique request ID or assumed to clear automatically every turn. This is a scoped observation, not a complete interpretation of the byte.

Further original-code inspection traces the choice-item predicate through additional item-suppression and ability/trait checks. The ability path can inspect other active battlers' suppression flags. It has not been cleared for a new scorer call under the no-hidden-foe-read contract. No extra helper call or unconditional stored-lock filter is added here.

## Local receipt hashes

These identify the retained local reports; hashes do not make the runs independent.

| Case | SHA256 |
|---|---|
| cancel | f19dcfe2051f5b75c26a67fcd8b4bd5d9532770c20a46628ee7e3ec5c9e23724 |
| confirm | 20fd64514ba83b26ff9e62bec08989831971234fb19c8453ca0ee7fdbe2fb427 |
| late_disable | 1b16d3d4e5744678be3702f48636da79fc9ac646724f1f82ce35ce201404e6ec |
| late_encore | 46816b9a85f7ae0f6b5bd4ab502816aa7ec6b145440154b1674874075b9d47a0 |
| late_pp0 | 50b16f1a9e979431aeba39c250d7fdf561a3b4ddac8c0c297e083a5c18becb5c |
| late_repeat | c8604f6203e5bf3155fb77c16dd0df4a4a781e6b3aaa741b95cca47556c30684 |
