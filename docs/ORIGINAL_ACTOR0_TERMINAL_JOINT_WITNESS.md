# Public action-to-return joint CPU witness research

Separate read-only source investigations already checked player0
emitter/reply/validator/slot/move/target/completion/PP sequence (PR90)
and candidate Main.inBattle/result/callback order (PR87/88). A public
trace could satisfy both independently but for DIFFERENT encounters.
This source-only join requires exactly one engine event-chain candidate,
one syntactically decoded potential outcome byte STRB transition
(bounded to one guessed EWRAM candidate byte), one Main nonzero->0
watch and exactly one 32-bit Thumb STR source/address/ROM-odd callback
pointer write each for callback1 and callback2. All chronology must be
strictly ordered actor0 emit/reply/target/PP/result/Main clear/callback1/
callback2, no manual marker, second emitter, extra result transition or
other Main transition. Completion must be present but may be before
or after PP.

This is a RESEARCH-ONLY necessary ordering pattern, not sufficient
native evidence. Many real legal actions could use other callback
writer instruction forms, other terminal sequences, delays, or
different legitimate PP/result order; nonmatches are UNVERIFIED and
are NOT classified original-game failures. Even a match cannot prove
the guessed byte is actual gBattleOutcome, a real original outcome
decision PC, unique engine-issued actor0 ownership, original dynamic
move/target legality, PP execution vs cancellation, or a callback
actually executing in the overworld. All certification flags are
hard false, native 0/20, production 0%, PP causes 0/2.

Public fake CPU records only. Strict inherited original v3 CPU schema
audit required. All new tests are mutation controls without staging,
reading, hashing or executing protected Current ROM/save/savestate,
modified original game, private emulator or original CPU traces.
Host Python Source CI only; pinned GNU ARM irrelevant. Protected
main/source-first and approved exact PR heads remain unchanged,
player-only/manual fallback protected, no automatic items/capture,
no enemy/NPC AI changes. Remains draft/unmerged until independent
Claude exact-head source/test/security review.
