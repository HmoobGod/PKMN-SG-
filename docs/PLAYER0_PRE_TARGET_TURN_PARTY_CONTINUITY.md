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

Immediately after choosing the move at a loop slot, freeze three
read-only values: original `gBattleTurnCounter`, player0's original
`gBattlerPartyIndexes[battler]`, and original foe party index
`gBattlerPartyIndexes[foe]`. After targeting helpers, but BEFORE
staging Fight or emitting an engine command, reject the entire
first-stage automatic proposal if any value changed. Fall through to
the unchanged original manual controller path; never silently switch
a move/target, use an item/capture, or alter enemy/NPC partner AI.

The existing second-stage snapshot and native move limitations check,
one-use `SourceFirstConsumeWildLease`, exact wild-single owner,
terminal/inBattle rejection, original controller fallback and no
uncertified doubles are unchanged. The additional checks are only
read-only first-stage continuity guards. No foe hidden moves, PP,
items or innates are accessed.

## Evidence and missing acceptance

Mutation-sensitive source tests check presence/ordering of all three
frozen values and all three post-target comparisons, with synthetic
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
