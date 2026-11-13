# Public-source lab: proposal-wide player-owned move/PP pool continuity

This experimental source patch is STACKED on PR #48 R4 exact
`7c88dfa20b741e021eeade6d34b46283f306178f`, still DRAFT and
unmerged. This draft does not modify that parent, protected
`source-first/rom-identity`, main, Current ROM or save.

## Missed cross-slot stale-proposal case

PR48 R4 already freezes original turn, player party and foe party ONCE
before scanning the candidate slots. It rejects drift after targeting,
including when a slot is rejected. But an earlier targeting helper
could hypothetically change a **different player-owned move or PP slot**
without changing turn/party. If an earlier candidate was ineligible,
the next candidate could be selected from an altered move pool. A
post-helper snapshot taken once the move was chosen would not establish
that the entire candidate pool matched the original ChooseAction input.

## Narrow source-only fix

For original player0 `CONTROLLER_CHOOSEACTION` only, and before *any*
candidate calls `GetBattlerMoveTargetType/CanTargetBattler`, capture
all `MAX_MON_MOVES` original player-owned move IDs and current PP.
After targeting helpers but before any `!canTarget` skip or automatic
Fight proposal, compare the entire live player-owned pool to that
single baseline. Any mismatch returns FALSE and falls into the
original unchanged manual controller. It never silently resets the
baseline, selects another slot, touches enemy hidden moves/PP, or tries
to repair game state.

The second-stage ChooseMove revalidation, native move restriction
checks, one-use LAB staging token, original owner/command/terminal
checks and no uncertified doubles are unchanged. No automatic items,
capture, enemy/NPC-partner AI or new gameplay hooks.

## Evidence limits

New C-source structure/mutation regressions require both read-only
pool snapshots before the slot loop and live full-pool comparisons
AFTER targeting helpers but BEFORE skipping an ineligible slot. They
test omitted/commented/disabled conditions and mutations of earlier
and later move/PP entries. Both the general Source workflow and
the separate pinned public disposable GNU ARM compiler workflow
invoke the new test before claiming success.

A disposable public upstream compilation does not establish source
compatibility with the user's exact modified game, native engine
ownership, first real player0 CPU auto-move, dynamic legality, PP
cancel/debit, native battle outcome, overworld callback or fallback.
A separate independently reviewed owner-authorized exact-ROM replay
would still be required. No private file is read or executed.

Formal modified-ROM acceptance: **0/20 (0%)**.
Production Smart Auto-Battle: **0%**.
Two historical PP-unmatched cases resolved: **0/2**.
Keep DRAFT/unmerged pending new exact-head Source CI, GNU ARM compile
and independent Claude source/test/security review. Parent PR48 R4's
pending verdict does not transfer to this new head.
