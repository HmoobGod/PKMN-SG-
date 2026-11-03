# 16266R5 — Request copier entry vs completed buffer-A copy

**Scope:** Source-only/static study and correction of the existing observer claims. No native hook, gameplay patch, automatic choice, new native emulator replay, or ROM/save write.

## Important correction to R3/R4 historical wording

The original `tools/probe_choice_lifecycle.py` sets its `copy` debugger breakpoint at **0x0806B370**, the **entry** to the original request-copy function. Its callback reads the *source buffer* before the original routine branches or copies bytes. The old ledger calls the 11 later events “observed native buffer-A copies.” The actual supported observation is **11 attempted buffer-A opcode19 copier entries**, plus independently logged subsequent native reply/completion/consumer events. Those latter observed events remain useful; the old trace does **not** observe the original A-byte-loop exit.

The original saved request in each process is seeded from an already-running game state. Its enqueue is unobserved. The original 17-lifetime / 11-reply / 6-accepted / 4-rejected / 1-cancelled correlation totals are not new execution or proof of post-copy completion.

## Candidate native path boundary (static, SHA-pinned)

Using both the unmodified Current ROM and the exact experimental16266 ROM, `tools/check_copy_postloop.py` verifies the same 104-byte original native copier window: **SHA256 c3d3181837d0aaf69fc471c4f5598870257c622c81bca9771a5d96d45850ab57**. It decodes the Thumb conditional/unconditional branches, move and buffer-literal operands, byte loads/stores, count comparisons, loop backedges and return.

For **non-link**, **direction0 buffer-A**, **positive count** reaching the original loop, the **0x0806B3C6** instruction is a *candidate post-A-loop observation point*: control falls through from the terminating byte-count comparison after the prior store. It is more specific than entry0x0806B370 or shared epilogue0x0806B3A6, which can be reached from empty/invalid/link paths. The A-loop starts0x0806B3BC. The link-mode alternate path begins0x0806B3C8; the B-copy loop uses0x0806B39C.

This is **static instruction structure only**. It is not evidence that a runtime PC hit occurred; an entry/exit pair must be correlated to one original invocation and checked against correct actor, input length, buffer pointers, actual memory writes, session and no nested/interrupt confusion. An arbitrary hit at the candidate PC is not engine request authority. The shared return is not a completion proof.

## Fail-closed replay correction

`tools/replay_choice_lease.py` now treats historical breakpoints as **attempts**, passes `original_copy_executed=False` to the unshipped R4 reference model, and opens **zero leases**. Its six previously recorded private JSON reports all passed: **6 seeded pre-observer requests, 11 entry attempts, 11 original native reply lifetimes, zero certified copy witnesses, zero authorized leases**. No original-input data was copied into GitHub.

Offline checks: eight public synthetic Thumb-decoder methods; five public synthetic entry-only replay methods; pinned Current/16266 static anchor PASS; sixteen distinct private-window branch/instruction/literal perturbations rejected. These tests do not constitute fresh native execution or hardware behavior.

## Future permitted investigation (no auto-emission)

1. Instrument *original* entry and post-A-loop boundaries read-only, recording a bounded invocation identity: r0 actor, direction0, 44-byte original source, buffer destination, non-link mode, actual completed writes, preserved machine state and correct pending request.
2. Validate cancel/Encore/Disable/repeat/PP0 recovery with a truly paired engine request and the existing original consumer, not just duplicated bytes or flags. Specifically exercise trainer doubles and authentic wild singles; NPC-partner control remains excluded.
3. Prove exclusive player ownership and complete move+target+choice-item/trait legality without extra side-effecting native validators or unauthorized enemy-field reads. Only then reconsider a real automatic adapter.

**Still disabled:** native automatic Smart AI0/20, capture/automatic items, NPC-partner auto. Human manual/held-B paths unchanged; no phone certification or Current promotion. Latest experimental ROM revision remains **16266**. Historical source-only checklist100% is not a playable-completion percentage.
