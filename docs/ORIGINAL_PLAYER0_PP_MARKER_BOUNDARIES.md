# Original actor0 PP marker triage: manual and overworld barriers

## Reproduced public evidence attribution gap
PR85's syntactic PP window stayed open after the original manual-menu
marker (kind8) or a watched Main inBattle->0 transition (kind2).
A later PP write could therefore look like a candidate for an older
automatic player0 emitter even though the game switched to manual input
or was leaving the battle. Two emitters without any lifecycle
separation were likewise assigned to the most recent emitter only,
without disclosing overlap ambiguity.

This is a *source-only hypothesis* flaw, NOT proof of any original PP
cancellation. Repair on a new isolated descendant; parent PR85 remains
unchanged and review-pending.

## Conservative witness boundary semantics
- Scan validated public original CPU event steps for manual-menu or
  inBattle-clear barriers. Close an open automatic marker window even
  if another watcher at the same CPU step precedes the barrier row.
- PP changes after a barrier and before another emitter are unattributed.
  Before-first-emitter changes remain a distinct counter.
- Back-to-back original emitters without a witnessed lifecycle boundary
  mark both windows as overlapping/AMBIGUOUS, not a unique request.
- A controller-completion marker alone does NOT close a window:
  legitimate original move execution may debit PP afterward.
- A single Thumb STRB writer after a marker is still only UNVERIFIED;
  unknown and overlapping cases remain unclassified. Do not infer a
  unique engine request, move/target legality or actual cancellation.

All negative tests use generated Python fake event rows and the
existing strict original CPU schema verifier. No original Current
ROM, save, savestate, modified game, private emulator or CPU trace
is read/staged/hashed/executed. Protected main/source-first and
approved heads unchanged; no merge, auto items/capture or enemy/NPC
AI changes. Native original acceptance 0/20, production 0%, old PP
causes 0/2. Fresh Claude exact-head review required.
