# Public original actor0 action-marker / PP candidate join

## Why this is needed
The existing original opcode/PP recorder separately counts actor0 move
emission, reply, validator, slot/move/target commit, completion, and PP
byte-write evidence. Independently seeing all these markers does not
prove they belong to one action, that a move or target was legal, or
that the original engine issued or consumed a unique request.

This source-only analyzer uses the strict already-tested original
CPU event auditor and PR89 player0 battle-epoch / PP-window triage.
Every candidate window is capped by the earliest manual/field/reentry
boundary or next emitter (even if the next emitter was denied).
Only ONE marker of each of reply, original validator, move-slot,
move-ID, target commit and completion can be present, with strictly
increasing reply->validator->slot->move->target CPU steps.
Completion is required after reply but may fall before OR after the
syntactic PP-byte debit; both are valid *research* hypotheses.
Exactly one pinned original Thumb STRB byte writer is required after
the target-commit step, and no other PP changes can occur in that
window. Overlapping emitter windows cannot be uniquely attributed.

The result is explicitly labelled UNVERIFIED. Marker presence is not
semantic dynamic legality, does not reveal move-ID/target identity,
and cannot authenticate actual engine-issued one-use requests,
PP execution intent, cancellation, battle completion, or gameplay.

Only public generated fake CPU rows used in tests; no private
Current ROM, save, savestate, original modified game, emulator or
private original CPU trace staged/read/hashed/executed. This is
hosted Python source-only evidence; GNU ARM compiler not applicable.
No protected main/source-first, approved heads, enemy/NPC partner AI,
manual fallback, items/capture or merges. Formal native 0/20,
production 0%, historical PP cause classifications 0/2.
Fresh independent Claude exact-head review required.
