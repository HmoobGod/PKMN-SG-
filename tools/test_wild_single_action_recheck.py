#!/usr/bin/env python3
"""Fail-closed first-stage Fight proposal checks on the disposable source-LAB patch.

Static regression/mutation tests and a limited synthetic model only. They cannot
establish a genuine modified-ROM engine-issued epoch, CPU reply, PP or win.
"""
from dataclasses import dataclass, replace
from pathlib import Path
import unittest

PATCH = Path(__file__).resolve().parents[1] / "source-first" / "wild-single-lab.patch"

def added_source(text):
    if not text.startswith("--- a/src/battle_controller_player.c\n+++ b/src/battle_controller_player.c\n"):
        raise ValueError("untrusted patch target")
    return "\n".join(line[1:] for line in text.splitlines()[2:]
                     if line.startswith("+") and not line.startswith("+++"))

POST_TARGET = """        if (!verifyReply && (!SourceFirstWildSingleOwner(battler) ||
            gBattleResources == NULL ||
            gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEACTION ||
            GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT) != foe ||
            gBattleMons[battler].moves[slot] != move ||
            gBattleMons[battler].pp[slot] == 0))
            return FALSE;"""
BEFORE_FIGHT = """        if (SourceFirstWildLeaseSnapshotMatches(battler) &&
            gBattleResources != NULL &&
            gBattleResources->bufferA[battler][0] == CONTROLLER_CHOOSEACTION)
        {
            BtlController_EmitTwoReturnValues(battler, B_COMM_TO_ENGINE, B_ACTION_USE_MOVE, 0);
            BtlController_Complete(battler);
            return;
        }
        SourceFirstInvalidateWildLease();"""

def contract(patch):
    try:
        s = added_source(patch)
        chooser = s.index("static bool32 SourceFirstWildSingleMove(")
        target = s.index("!CanTargetBattler(battler, foe, move)", chooser)
        gate = s.index(POST_TARGET, chooser)
        move_reply = s.index("*reply = slot | (foe << 8);", chooser)
        proposal = s.index("*reply = slot; // Record proposal", chooser)
        arm = s.index("SourceFirstArmWildLease(battler);", proposal)
        frozen = s.index("sSourceFirstWildLease.proposedSlot = proposedSlot;", arm)
        after_arm = s.index(BEFORE_FIGHT, arm)
        next_selector = s.index("void PlayerHandleChooseMove(", after_arm)
        return (target < gate < move_reply < proposal < arm < frozen < after_arm < next_selector
                and s.count("CheckMoveLimitations(") == 1
                and s.count("sSourceFirstWildLease.armed = FALSE;") == 2
                and s.count("SourceFirstWildLeaseSnapshotMatches(battler)") == 4
                and "B_ACTION_USE_ITEM" not in s and "B_ACTION_SWITCH" not in s)
    except (ValueError, AssertionError):
        return False

@dataclass(frozen=True)
class State:
    active: bool = True
    in_battle: bool = True
    terminal: bool = False
    wild_single: bool = True
    actor: int = 0
    foe: int = 1
    opcode: str = "CHOOSEACTION"
    move: int = 33
    pp: int = 5
    slot: int = 0
    snapshot: int = 12

def safe_proposal(start, after_target, pre_emit):
    def active(s):
        return (s.active and s.in_battle and not s.terminal and
                s.wild_single and s.actor == 0 and s.foe == start.foe and
                s.opcode == "CHOOSEACTION")
    if not active(start) or not active(after_target) or not active(pre_emit):
        return None
    if (after_target.move, after_target.pp, after_target.slot) != (start.move, start.pp, start.slot):
        return None
    if after_target.pp <= 0 or after_target.move == 0:
        return None
    if pre_emit != start:
        return None
    return ("FIGHT", start.slot)

class TestActionRecheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch = PATCH.read_text()
    def test_contract(self):
        self.assertTrue(contract(self.patch))
    def test_mutate_remove_target_gate(self):
        self.assertFalse(contract(self.patch.replace("+        " + POST_TARGET.lstrip().splitlines()[0],
              "+        if (FALSE && (!SourceFirstWildSingleOwner(battler) ||", 1)))
    def test_mutate_remove_pre_emit_gate(self):
        self.assertFalse(contract(self.patch.replace("+        if (SourceFirstWildLeaseSnapshotMatches(battler) &&",
              "+        if (TRUE &&", 1)))
    def test_mutate_pre_emit_command(self):
        self.assertFalse(contract(self.patch.replace(
            "+            gBattleResources->bufferA[battler][0] == CONTROLLER_CHOOSEACTION)",
            "+            gBattleResources->bufferA[battler][0] == CONTROLLER_CHOOSEMOVE)", 1)))
    def test_patch_scope_player_controller_only(self):
        self.assertEqual(self.patch.count("+++ b/src/battle_controller_player.c"), 1)
    def test_clean_first_stage(self):
        s = State()
        self.assertEqual(safe_proposal(s,s,s), ("FIGHT",0))
    def test_target_command_replaced(self):
        s=State()
        self.assertIsNone(safe_proposal(s, replace(s,opcode="CHOOSEMOVE"), s))
    def test_target_actor_changed(self):
        s=State()
        self.assertIsNone(safe_proposal(s,replace(s,actor=1),s))
    def test_target_foe_changed(self):
        s=State()
        self.assertIsNone(safe_proposal(s,replace(s,foe=0),s))
    def test_target_move_changed(self):
        s=State()
        self.assertIsNone(safe_proposal(s,replace(s,move=44),s))
    def test_target_pp_exhausted(self):
        s=State()
        self.assertIsNone(safe_proposal(s,replace(s,pp=0),s))
    def test_target_terminal(self):
        s=State()
        self.assertIsNone(safe_proposal(s,replace(s,terminal=True),s))
    def test_pre_emit_command_stale(self):
        s=State()
        self.assertIsNone(safe_proposal(s,s,replace(s,opcode="CHOOSEMOVE")))
    def test_pre_emit_new_turn_snapshot(self):
        s=State()
        self.assertIsNone(safe_proposal(s,s,replace(s,snapshot=13)))
    def test_pre_emit_pp_change(self):
        s=State()
        self.assertIsNone(safe_proposal(s,s,replace(s,pp=4)))
    def test_pre_emit_lost_owner(self):
        s=State()
        self.assertIsNone(safe_proposal(s,s,replace(s,active=False)))
    def test_no_second_stage_use_after_denial(self):
        s=State()
        self.assertIsNone(safe_proposal(s,replace(s,terminal=True),s))
        self.assertEqual(safe_proposal(s,s,s),("FIGHT",0))
if __name__ == "__main__":
    unittest.main()
