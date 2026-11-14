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


## Isolated follow-up: pre-proposal foe state cannot drift during targeting

The source-LAB two-stage wild-single auto move revalidates a broad player
and foe snapshot at the **ChooseMove** reply. At the earlier ChooseAction
proposal stage, the original target-helper pair may be stateful. The
previous pre-target snapshot froze own move/PP pool, turn and party
identity but **not** the foe's species/HP/status1/ability/3 types before
those helpers ran. An ineligible slot could run a helper that mutated foe
combat identity and then let the next slot be proposed from that altered
state. Arming the lease *after* such a mutation would snapshot the wrong
baseline and mask the first-stage drift.

An independent, read-only foe snapshot is now taken BEFORE the first
target helper, only for the disposable player-owned source-LAB. Every
candidate's helper is followed by an unconditional first-stage comparison
of species, HP, status1, ability and all 3 types **before** the
`if (!canTarget) continue` branch or any Fight reply. Any drift cancels
the automatic proposal and leaves the original engine's manual path.
The second-stage existing snapshot/lease consumption and move legality
checks remain unchanged. No foe moves/PP, hidden items or AI are
read/changed by the new guard.

New source-level mutation tests require each freeze and comparison to
be live, after helpers and before candidate skip; synthetic fixtures
check species/HP/status1/ability/types and no slot reselection.
Source checks + pinned disposable public GNU ARM compile are required
before independent Claude exact-head source/test/security review.
Approved PR51 and protected main/source-first/Current ROM/save remain
unaltered, and pending PR48 source overlap must be reconciled before
any potential integration. No real original modified-ROM gameplay
is exercised or certified. Native acceptance 0/20, production 0%,
historical unmatched PP causes 0/2.


## Isolated follow-up: freeze all first-stage player combat state

Approved source-LAB PR51 froze the player's move/PP pool and actor/turn
before target helper calls; draft PR71 then froze foe combat state.
But original `ChooseAction` did not freeze the player's OTHER combat
state before `GetBattlerMoveTargetType`/`CanTargetBattler`. If a
helper mutates the player's HP, status, innate abilities, items,
types, or volatile timers and an automatic proposal is staged
afterward, the new lease would accept that mutated snapshot as its
baseline. A later slot could be auto-selected after an ineligible
first helper changed effective move legality.

The new disposable source-LAB guard captures player species/HP/status1,
main ability/legacy item, taunt/disable/encore/torment timers, three
types, all innate abilities, and all configured held items ONCE before
any candidate target helper. It rechecks every field AFTER each
helper and BEFORE the candidate's eligibility skip or any Fight
response. Any drift fails closed to the original manual path; it
does not retry with a different move, re-arm the lease, call item/
capture controls or alter an enemy/NPC AI controller. The existing
frozen move/PP pool and foe state from PR51/PR71 remain independent,
plus the original second-stage dynamic restrictions/target rechecks.

Public Python structural mutation tests check actual C code,
per-field capture/rechecks, full 3-type and all innate/item arrays,
order around the target helpers, dead preprocessor guards and
forbidden opponent state reads. Pinned disposable GNU ARM source
patch application and full compile are mandatory. This does not
execute protected Current ROM/save/modified game or authenticate
the original ROM's one-use actor0 engine request. Original native
0/20=0%, production 0%, two historical PP causes 0/2.
