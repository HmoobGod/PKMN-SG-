# Actor0 PP attribution and original Main inBattle ownership barriers

## Concrete source-only defect in parent PR86
The PR86 public observer treats a kind6 original actor0 emitter as a
fresh PP-attribution window even if a kind2 Main.inBattle->0 watcher is
recorded on the SAME original CPU step (in either row order), or after
an observed battle exit with no later inBattle re-entry. Those emitters
cannot be treated as reliable current battle requests in a read-only
original CPU evidence report.

## Isolated fail-closed fix
After the inherited strict original v3 CPU schema audit, precompute
manual/field exit boundary steps and Main inBattle 0->nonzero re-entry
steps. Never open a PP window on either boundary step; if Main has
exited, refuse all later emitter windows until a genuine watched
nonzero inBattle transition appears at an EARLIER step. Also deny a
marker whose own captured context reports inBattle=0. Record denied
markers separately, do not quietly relabel them a valid auto epoch.
Completion markers do not close PP attribution because a real PP
debit may occur after completion. Move legality, ownership and PP
cancellation remain unverified. The existing parser remains passive
and cannot perform actions.

Public synthetic mutation tests cover same-step exit and re-entry in
both permissible watcher row orderings, stale post-exit emitters,
positive future-step re-entry and inBattle-zero emitter without a
watched exit. Host Python Source CI only; no public GNU ARM applicable.

No Current ROM/save/savestate, private modified original game, owner
emulator or original CPU trace read, hashed, staged or executed. No
protected branches, independently approved heads, enemy/NPC AI,
auto items/capture or manual fallback touched, no merge. Native 0/20,
production 0%, historical PP causes 0/2. Fresh independent Claude
exact-head source/test/security review mandatory.
