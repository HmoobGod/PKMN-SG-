# Original controller execution mask and resource-owner continuity (PUBLIC LAB)

The existing player-only disposable wild-single source patch checks
that the original controller is active and captures original header
bytes, all move menu move IDs and PP. A separate original controller
event can still change another execution-mask bit or swap the original
gBattleResources pointer while leaving player0 active and the
ChooseMove opcode unchanged. This can cause a staged auto proposal to
be mistaken for the current request; there is no certified engine epoch.

Snapshot the full public-source gBattleControllerExecFlags mask and
gBattleResources identity at each original player0 request stage before
calling engine move-limitations or targeting helpers. Require both
identical immediately AFTER CheckMoveLimitations and after targeting
helpers BEFORE skipping ineligible moves or replying to the engine.
On drift return FALSE to the normal manual controller input path.
Read-only fields; no writes to execution mask/resources.

Original upstream source exposes gBattleControllerExecFlags in
include/battle.h at pinned public source commit
3f4d90aa8f8bc50054c817d7bd59fcdfcfb4933d.
New focused public static/mutation tests and exact-head Source CI plus
pinned disposable PUBLIC GNU ARM compilation are mandatory. This
does not prove an authentic original modified-ROM one-use request,
original dynamic legality, PP cancellation or gameplay. It only
tightens the source-LAB failure policy.

No private original Current ROM/save/savestate, original modified
game, emulator or original CPU trace read/staged/hashed/executed.
Player0 only; manual fallback retained; no enemy/NPC partner AI,
automatic items/capture or protected/approved heads changed. DRAFT,
unmerged, exact-head independent Claude review required. Native
0/20, production 0%, historic PP causes 0/2.
