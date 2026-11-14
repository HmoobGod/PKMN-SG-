# Public original player0 request copy: after-POST_PC observation boundary

## Gap established in parent PR80
PR80's read-only 44-byte request copy collector returns at the original
POST_PC marker **before** that guest instruction is executed. Consequently
its successful record cannot say what instruction executes immediately
after the copy, whether pending/request-pointer context transitions, or
whether the engine retires a one-use player request. A completed copy is
not evidence of native move consumption, legality, PP debit/cancellation
or battle outcome.

## Isolated source-only follow-on
The new optional header `tools/alternate_mgba_postpc_context_probe.h`
consumes the parent collector's unmodified `Proof` and the still-paused
CPU. It fails closed before executing if the copy is incomplete, actor
is not zero, ROM opcode sampled at POST_PC differs from the parent's
PRE-step halfword, CPU PC/SP/LR/frame differ, original pointer or pending
changed, source/destination 44 bytes drifted, or host callbacks are
missing. The attempted flag permits at most ONE call per output ticket;
this is a local probe guard, **not** a guaranteed one-use engine epoch.

Only after preflight, it executes **one** guest CPU instruction and
records next PC, frame, request buffer pointer and pending word. Either
pointer/pending change is `context_changed_unclassified` (unknown),
not automatically a cancellation or approval. A poststep rollback or
source/destination drift fails the probe. Regardless of all observations,
`engine_one_use_certified`, `native_pp_cause_certified` and
`production_authorized` remain zero.

The dedicated C test includes the actual parent C fake observer, generates
44 fake Thumb STRB stores, pauses at fake POST_PC, changes the fake
callback to step once, and tests valid successor, pending/pointer drift,
modified copied byte, frame rollback, same PC successor, and seven
preflight corruptions that must never step. Fake `0x4718` and successor
`POST_PC+2` are fabricated, not real original instruction provenance.

## Nonpromotion and future evidence
No original modified-ROM, Current ROM, save, savestate, private trace or
emulator is opened, hashed, staged or executed; only **PUBLIC FAKE CPU**
tests are run. This source-only continuation cannot prove an actual
engine-owned one-use player0 request, original dynamic move/target
legality, the two historical PP cancellation/debit causes, original
result decision PC, overworld return, or manual fail-closed behavior.
Future original-game testing requires separate explicit owner
authorization and exact modified-ROM instruction attestation.

No edit to PR80, its source-approved ancestors, main/source-first,
enemy/NPC AI or gameplay binaries. Draft/unmerged pending independent
Claude exact-head source/test/security review and exact-head Source CI.

Formal original native 0/20; production 0%; historical PP causes 0/2.
