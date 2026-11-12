# Exact modified-ROM: battle-end and cancellation safety blocker

Checkpoint: 2026-11-12. SOURCE LAB and read-only private replay only. No new
hybrid native hook installed, no Current ROM/save edit, no main merge.

After two earlier authenticated natural wild fixtures (11 original player0
automatic native move submissions/commits; nine observed own-PP deductions),
a separate fresh no-button native emulator probe of the same exact modified
ROM SHA256 4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44
confirmed that quiet action traces are NOT terminal proof. A naturally
triggered wild single was entered on the original unmodified save via
normal overworld movement; no guest memory/ROM writes or button presses
were made after entering the wild encounter. An original player move
submission occurred and PP decreased, then three contiguous 350-frame
windows had zero traced native player action/menu markers. Yet in every
final quiet snapshot original battle flags remained 4, battler count 2,
actor0 pending word zero, and the original controller/overworld terminal
transition was not demonstrated. A separate disposable acknowledgment
probe using one brief A input after quiet did not produce a new action
or battle flags clearing; it is diagnostic only, NOT a no-input acceptance
trace. Original protected Current and save were re-hashed unchanged.

This is NOT sufficient to assert a freeze or outcome: more engine instruction
and actual screen/callback observation are required. The tested headless
mGBA host supplies a dummy/no screenshot renderer, and terminal/outcome
callback PC remains unauthenticated. Silent native callbacks may reflect
an outcome script, UI acknowledgment state, or a genuine stalled path.

A new source-only gate stops auto reply when native gBattleOutcome != 0.
It must compile cleanly on pinned upstream source, and a synthetic mutation
test must reject removal of this check. tools/trace_exact_terminal_gate.c
captures read-only battle flags, battler count, pending and own four PP
through bounded guest instruction stepping. tools/verify_exact_terminal_gate.py
and tests refuse to treat quiet or zero pending as a completed battle.
Even eventual clear flags are insufficient without authenticated native
terminal and original overworld callback instruction evidence.

Previously unmatched two of eight second-fixture submitted moves versus
six own-PP debits remain UNCLASSIFIED. Do not equate reply/slot commit
with full PP-consuming move execution, invent reasons, or add PP deltas
to incomplete action snapshots. Separate original execution/cancellation
witness is still needed for move-specific classification.

Formal playable acceptance 0/20; native player-only three-turn and
second-wild observations remain research successes, not production.
Maintain no enemy/NPC-partner AI modification, manual fallback safety,
no auto bag/capture/Master Ball, no uncertified trainer/doubles,
Struggle or forced-switch actions, and keep Current and save immutable.

Next: derive and pin exact modified-ROM battle-outcome and overworld
callback original PC/witness, collect no-input battle-end evidence and
rejected/cancelled per-action PP milestones, repeat more independent
wild encounters; only then consider a bounded exact native hybrid hook.
