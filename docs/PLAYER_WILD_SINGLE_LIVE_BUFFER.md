# Player-owned wild-single live reply-buffer safety (SOURCE-LAB only)

Date: 2026-11-12. Parent dev source-first/rom-identity: `29b73af765136a88bced1c94f225e5e4fcc0a920`.

## Change

The original player-owned disposable source lab already consumes a single-use Fight proposal, retains one frozen move slot, invokes original `CheckMoveLimitations` once at final ChooseMove, checks target eligibility, validates owner/turn/opponent and relevant state snapshots after helper calls, and falls back to original manual selection when unsafe.

The risk addressed here is separate: a modded targeting helper might replace `gBattleResources`, change `bufferA[battler][0]`, or change the ChooseMove payload while the cached `struct ChooseMoveStruct *moveInfo` points at the old request. Before reading cached move/PP fields after targeting helper calls, the lab now requires non-null live resources, an unchanged `CONTROLLER_CHOOSEMOVE` command and exact pointer equality to the current `bufferA[battler]+4` request payload. It also checks owner and command again after the selector returns and just before calling the original player-only reply emitter. If the actor/request is stale or changed, automation emits **no new action**, and the original PlayerHandleChooseMove manual path remains.

The change preserves original source `battle_controller_player.c` only, source-LAB single-player wild battle gating, no automatic items/capture, no enemy/NPC partner AI, no forced switches, Struggle, trainers or doubles, and no modifications of protected Current ROM, save or main. It does not claim a certified engine-issued epoch: an identical replacement request may remain indistinguishable on source-only evidence. Runtime emulator confirmation and original request ownership remain blocked on the unavailable exact modified ROM SHA256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44` and matching pinned host/state. No new original CPU trace, PP cause, outcome decision PC or safe terminal is certified.

## Validation

- Pinned upstream file SHA256 `deb649e441dd28909ade7053119b4af29450c9686e43000f319149d44c43e594` checked and re-patched with `git apply --check`, then applied result compared byte-for-byte.
- New synthetic+mutation tests `tools/test_wild_single_live_buffer.py` (41 checks). Includes cached payload identity and command mutation after original target helper, false player owner, null resource, repeated one-use request, moved request slot, and manual fallback.
- Revised previous `tools/test_wild_single_fixed_proposal.py` static contract to demand both original and new opcode guards; the prior mutation test had masked a removed guard because the new second guard made a single-token `in` check insufficient.
- All six targeted suites: cancellation 39, frozen slot 54, dynamic state 65, turn/target 40, post-helper 46, new live buffer 41 = 285/285, **synthetic/source-only**.
- Exact GitHub Source and GNU ARM lab CI run status must be verified independently at the new source commit. The GNU ARM ROM is disposable and not the user's custom ROM.

## Next evidence needed

Use the exact modified ROM and matching second/third wild states to record in one original CPU run: actor0 action/ChooseMove request and payload bytes, original `0x0809E6BA` PP writer or cancellation for every submission, `gMain.inBattle` clear CPU PC, native outcome decision/store/branch PC, callback1/callback2 and full no-input return to field/next wild. Only then can original request epochs, PP unmatched 2/2, terminal and real 20/20 native acceptance be evaluated. Never splice separate fixture traces or treat compilation as gameplay proof.
