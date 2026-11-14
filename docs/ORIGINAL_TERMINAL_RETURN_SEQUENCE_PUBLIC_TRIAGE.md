# PUBLIC original outcome / field-return sequence triage

## Gap
Existing PR78/79/82 independently count potential byte outcome writer
PCs and Thumb STR or STMIA callback pointer stores but do not ask whether
their chronological order is compatible with a battle-end-to-overworld
return. Individual matching watcher values alone do not prove the real
gBattleOutcome address, terminal decision or genuine field callback.

## Conservative source-only research
Re-run the strict original C observer event schema auditor on PUBLIC fake
event rows. For each Main.inBattle nonzero->0 edge, require exactly one
candidate outcome-byte 0->nonzero STRB writer seen BEFORE this edge, exactly
one candidate gMain callback1 word STR/STMIA AFTER this edge and exactly
one callback2 word STR/STMIA AFTER callback1. All transitions must occur
on distinct increasing CPU steps with recorded PRE-step register source
values and exact changed RAM address. Missing, multiple, reordered,
manual-menu interruption, resumed battle or unknown opcode/address are
unverified/incomplete, not native failure. Callbacks restricted to odd
ROM-address range; other possible real sources are left UNATTRIBUTED.

The generated Python fake includes positive/negative mutation cases:
result after clear, swapped callback order, duplicate callback1,
bad callback source, manual fallback, resumed battle, untrusted original
CPU field and non-ROM callback pointer. Never label a guessed candidate
byte as the actual engine gBattleOutcome or infer actual overworld
resume from a synthetic watcher sequence.

This runs only on public synthetic input; host Source CI only,
GNU ARM not applicable. NO owner original Current ROM/save/savestate,
modified game, emulator or private CPU trace read/staged/hashed/executed.
Protected main/source-first, approved exact heads, manual fallback,
enemy/NPC AI and no auto items/capture unchanged. Draft unmerged,
independent Claude exact-head review required. Native 0/20,
production 0%, PP historical causes 0/2.
