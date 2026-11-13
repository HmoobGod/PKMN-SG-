# SOURCE-FIRST LAB: player0 first-stage target-helper continuity guard

Experimental player-owned wild-single source patch ONLY. This draft is
stacked directly on the unchanged source-first/rom-identity exact head
`655d2430c5891c12bbf4bc526b9f98f1468d433b`. It is NOT merged into
main or installed in the protected Current ROM/save. PR26 and all previously
Claude-approved exact heads are unchanged.

## Concrete stale-request defect

The existing experimental two-stage flow chooses a candidate slot during
`CONTROLLER_CHOOSEACTION`, calls `GetBattlerMoveTargetType` and
`CanTargetBattler` (potentially stateful helpers), then arms a snapshot
of the **post-helper** player/foe context. Previously, it could
silently adopt a DIFFERENT turn or party index if a helper changed that
identity during candidate selection, because the snapshot was taken
after the change. Rechecking that post-change snapshot alone does not
prove the candidate was chosen for the same pre-target request.

## Narrow fail-closed fix

Before entering the candidate move loop, freeze ONE read-only identity
baseline for the entire original player0 ChooseAction proposal:
`gBattleTurnCounter`, `gBattlerPartyIndexes[battler]` and
`gBattlerPartyIndexes[foe]`. Never retake that baseline per slot.
After either targeting helper, and BEFORE an ineligible candidate can
advance to another slot or Fight is staged, reject the whole proposal
if any of those original identities drifted. Fall through to
the unchanged original manual controller path; never silently switch
a move/target, use an item/capture, or alter enemy/NPC partner AI.

The existing second-stage snapshot and native move limitations check,
one-use `SourceFirstConsumeWildLease`, exact wild-single owner,
terminal/inBattle rejection, original controller fallback and no
uncertified doubles are unchanged. The additional checks are only
read-only first-stage continuity guards. No foe hidden moves, PP,
items or innates are accessed.

## Evidence and missing acceptance

Mutation-sensitive source tests parse live (comment-stripped) C patch text;
reject `#if 0`, commented-out checks/freezes, tautologies, retaken
per-slot baselines and skip-before-check reorderings. Both source CI
and the disposable GNU ARM build workflow run these tests before
accepting a compile. Model tests additionally check synthetic
turn/own-party/foe-party changes, terminal/inactive/wrong-owner rejection
and hidden opponent-state isolation. The exact pinned upstream source
compile GitHub Action is enabled on this PR; it creates ONLY a public
disposable lab ROM and uploads text build logs, NEVER any protected
Current ROM or save. Any compile failure blocks the draft.

This does not establish an original modified-ROM player0 engine-issued
request epoch, dynamic effective legality, PP cancellation, battle
terminal, owner-local replay, or production Smart Auto-Battle. Actual
native acceptance stays 0/20 (0%), production 0%, historical PP
unmatched 0/2. Keep DRAFT/unmerged, source/test/security review required.
