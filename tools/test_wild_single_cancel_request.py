#!/usr/bin/env python3
"""Source-lab cancellation and party-binding regression gates.

Synthetic model tests do not assert native ROM or CPU behavior. The important
runtime compile/apply check is the pinned disposable GNU ARM lab workflow.
"""
from dataclasses import dataclass
from pathlib import Path
import unittest

PATCH = Path(__file__).resolve().parents[1] / "source-first" / "wild-single-lab.patch"


def inserted(text):
    if not text.startswith("--- a/src/battle_controller_player.c\n+++ b/src/battle_controller_player.c\n"):
        raise ValueError("unexpected target")
    return "\n".join(line[1:] for line in text.splitlines()[2:] if line.startswith("+"))


def gate(patch):
    if not patch:
        return False
    text = inserted(patch)
    chunk = patch.split(" static void PlayerBufferRunCommand(enum BattlerId battler)", 1)
    if len(chunk) != 2:
        return False
    dispatch = chunk[1].split("static void CompleteOnBattlerSpritePosX_0", 1)[0]
    required = [
        "static void SourceFirstInvalidateWildLease(void);",
        "gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE",
        "SourceFirstInvalidateWildLease();",
        "sSourceFirstWildLease.partyIndex = gBattlerPartyIndexes[battler];",
        "gBattlerPartyIndexes[battler] != sSourceFirstWildLease.partyIndex",
        "bool32 armed = sSourceFirstWildLease.armed;",
        "sSourceFirstWildLease.armed = FALSE;",
        "SourceFirstConsumeWildLease(battler) &&",
        "SourceFirstWildSingleMove(battler, TRUE, &autoReply)",
        "unusable = verifyReply ? CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL) : 0;",
        "gBattleOutcome != 0", "!gMain.inBattle",
        "gBattlersCount != 2 || battler != 0",
        "gBattlerBattleController[battler] != BATTLE_CONTROLLER_PLAYER",
        "!IsBattleControllerActiveOnLocal(battler)",
        "gBattleResources->bufferA[battler][0] !=",
        "!CanTargetBattler(battler, foe, move)",
    ]
    return (
        all(s in text for s in required)
        and dispatch.find("gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE")
        < dispatch.find("SourceFirstInvalidateWildLease();")
        < dispatch.find("sPlayerBufferCommands[gBattleResources->bufferA[battler][0]](battler)")
        and text.count("sSourceFirstWildLease.armed = FALSE;") == 2
        and "SourceFirstInvalidateWildLease();" in patch.split(" static void PlayerHandleChooseAction(enum BattlerId battler)", 1)[1]
        and text.index("sSourceFirstWildLease.armed = FALSE;")
        < text.index("if (!armed || battler != sSourceFirstWildLease.owner ||")
    )


@dataclass
class DisposableLeaseModel:
    armed: bool = False
    owner: int = -1
    foe: int = -1
    party: int = -1
    moves: tuple = ()
    pp: tuple = ()
    cancelled: int = 0

    def receive(self, command, battler):
        if command != "CHOOSEMOVE":
            self.armed = False
            self.cancelled += 1

    def action(self, battler, foe=1, party=0, moves=(33, 0, 0, 0), pp=(10, 0, 0, 0), eligible=True):
        self.armed = False
        if not eligible or battler != 0:
            return False
        self.armed, self.owner, self.foe, self.party = True, battler, foe, party
        self.moves, self.pp = tuple(moves), tuple(pp)
        return True

    def choose(self, battler, foe=1, party=0, moves=(33, 0, 0, 0), pp=(10, 0, 0, 0),
               selected=0, legal_mask=0, in_battle=True, outcome=0, active=True,
               wild_single=True, target_ok=True, request_ok=True):
        was_armed = self.armed
        self.armed = False    # Must consume even if validation fails.
        if not (was_armed and self.owner == battler and self.foe == foe and self.party == party
                and self.moves == tuple(moves) and self.pp == tuple(pp)
                and battler == 0 and in_battle and outcome == 0 and active
                and wild_single and target_ok and request_ok
                and 0 <= selected < 4 and moves[selected] != 0 and pp[selected] > 0
                and not (legal_mask & (1 << selected))):
            return None
        return (selected, foe)


class StaticContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PATCH.read_text(encoding="utf-8")
        cls.added = inserted(cls.source)

    def test_real_patch(self): self.assertTrue(gate(self.source))
    def test_dispatch_move_exemption_tamper(self): self.assertFalse(gate(self.source.replace("!= CONTROLLER_CHOOSEMOVE", "== CONTROLLER_CHOOSEMOVE", 1)))
    def test_dispatch_order_tamper(self):
        a="+        if (gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE)\n+            SourceFirstInvalidateWildLease();"
        self.assertFalse(gate(self.source.replace(a, a.split("\n")[1]+"\n"+a.split("\n")[0],1)))
    def test_party_bind_absent(self): self.assertFalse(gate(self.source.replace("sSourceFirstWildLease.partyIndex = gBattlerPartyIndexes[battler];", "sSourceFirstWildLease.partyIndex = 0;")))
    def test_party_change_tamper(self): self.assertFalse(gate(self.source.replace("gBattlerPartyIndexes[battler] != sSourceFirstWildLease.partyIndex", "FALSE")))
    def test_one_use_tamper(self): self.assertFalse(gate(self.source.replace("sSourceFirstWildLease.armed = FALSE;", "sSourceFirstWildLease.armed = TRUE;")))
    def test_engine_ownership_tamper(self): self.assertFalse(gate(self.source.replace("!IsBattleControllerActiveOnLocal(battler)", "FALSE")))
    def test_terminal_tamper(self): self.assertFalse(gate(self.source.replace("gBattleOutcome != 0", "FALSE")))
    def test_doubles_tamper(self): self.assertFalse(gate(self.source.replace("gBattlersCount != 2 || battler != 0", "FALSE")))
    def test_move_limit_tamper(self): self.assertFalse(gate(self.source.replace("unusable = verifyReply ? CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL) : 0;", "unusable = 0;")))
    def test_target_tamper(self): self.assertFalse(gate(self.source.replace("!CanTargetBattler(battler, foe, move)", "FALSE")))
    def test_no_forbidden_gameplay(self):
        for fragment in ("B_ACTION_USE_ITEM", "B_ACTION_SWITCH", "B_ACTION_RUN", "Master Ball", "gBattlerControllerFuncs[foe] ="):
            with self.subTest(fragment=fragment): self.assertNotIn(fragment, self.added)


class SyntheticCancellationModel(unittest.TestCase):
    def setUp(self): self.m = DisposableLeaseModel()
    def test_simple_legal_action(self):
        self.assertTrue(self.m.action(0)); self.assertEqual(self.m.choose(0), (0,1))
    def test_no_double_consume(self): self.m.action(0); self.m.choose(0); self.assertIsNone(self.m.choose(0))
    def test_cancel_item(self): self.m.action(0); self.m.receive("CHOOSEITEM",0); self.assertIsNone(self.m.choose(0))
    def test_cancel_switch(self): self.m.action(0); self.m.receive("CHOOSEPOKEMON",0); self.assertIsNone(self.m.choose(0))
    def test_cancel_battle_end(self): self.m.action(0); self.m.receive("END",0); self.assertIsNone(self.m.choose(0))
    def test_cancel_other_player_controller(self): self.m.action(0); self.m.receive("INTRO",2); self.assertIsNone(self.m.choose(0))
    def test_consume_fresh_move_request(self): self.m.action(0); self.m.receive("CHOOSEMOVE",0); self.assertEqual(self.m.choose(0),(0,1))
    def test_manual_after_no_action(self): self.assertIsNone(self.m.choose(0))
    def test_wrong_actor(self): self.m.action(0); self.assertIsNone(self.m.choose(2))
    def test_wrong_target(self): self.m.action(0); self.assertIsNone(self.m.choose(0,foe=2))
    def test_party_changed(self): self.m.action(0); self.assertIsNone(self.m.choose(0,party=1))
    def test_party_changed_same_moves(self): self.m.action(0,moves=(33,33,0,0)); self.assertIsNone(self.m.choose(0,party=2,moves=(33,33,0,0)))
    def test_pp_changed(self): self.m.action(0); self.assertIsNone(self.m.choose(0,pp=(9,0,0,0)))
    def test_move_changed(self): self.m.action(0); self.assertIsNone(self.m.choose(0,moves=(34,0,0,0)))
    def test_disabled(self): self.m.action(0); self.assertIsNone(self.m.choose(0,legal_mask=1))
    def test_encore_choice_mask(self): self.m.action(0,moves=(33,34,0,0),pp=(10,10,0,0)); self.assertIsNone(self.m.choose(0,moves=(33,34,0,0),pp=(10,10,0,0),selected=1,legal_mask=2))
    def test_pp_zero(self): self.m.action(0); self.assertIsNone(self.m.choose(0,pp=(0,0,0,0)))
    def test_stale_overworld(self): self.m.action(0); self.assertIsNone(self.m.choose(0,in_battle=False))
    def test_terminal(self): self.m.action(0); self.assertIsNone(self.m.choose(0,outcome=1))
    def test_inactive_controller(self): self.m.action(0); self.assertIsNone(self.m.choose(0,active=False))
    def test_doubles(self): self.m.action(0); self.assertIsNone(self.m.choose(0,wild_single=False))
    def test_target_denied(self): self.m.action(0); self.assertIsNone(self.m.choose(0,target_ok=False))
    def test_opcode_denied(self): self.m.action(0); self.assertIsNone(self.m.choose(0,request_ok=False))
    def test_terminal_consumes_lease(self):
        self.m.action(0); self.assertIsNone(self.m.choose(0,outcome=1)); self.assertIsNone(self.m.choose(0,outcome=0))
    def test_rearm_resets_previous(self):
        self.m.action(0,party=0); self.m.action(0,party=2); self.assertIsNone(self.m.choose(0,party=0))
    def test_invalid_action_does_not_arm(self): self.assertFalse(self.m.action(0,eligible=False)); self.assertIsNone(self.m.choose(0))
    def test_enemy_cannot_arm(self): self.assertFalse(self.m.action(1)); self.assertIsNone(self.m.choose(1))


if __name__ == "__main__":
    unittest.main()
