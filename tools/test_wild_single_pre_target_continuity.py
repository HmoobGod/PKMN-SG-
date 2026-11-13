#!/usr/bin/env python3
"""Source-only player0 first-stage target-helper TOCTOU regression.

No private ROM/save/CPU run, no opponent AI modification. This checks that
an original ChooseAction proposal cannot be silently attributed to a changed
turn or party after GetBattlerMoveTargetType()/CanTargetBattler().
"""
from dataclasses import dataclass, replace
from pathlib import Path
import unittest

PATCH = Path(__file__).resolve().parents[1] / "source-first" / "wild-single-lab.patch"

FREEZE = (
    "u16 preTargetTurn = gBattleTurnCounter;",
    "u8 preTargetPlayerParty = gBattlerPartyIndexes[battler];",
    "u8 preTargetFoeParty = gBattlerPartyIndexes[foe];",
)
CHECK = (
    "gBattleTurnCounter != preTargetTurn ||",
    "gBattlerPartyIndexes[battler] != preTargetPlayerParty ||",
    "gBattlerPartyIndexes[foe] != preTargetFoeParty ||",
)


def added_source(diff: str) -> str:
    if not diff.startswith("--- a/src/battle_controller_player.c\n"
                           "+++ b/src/battle_controller_player.c\n"):
        raise ValueError("source patch target changed")
    return "\n".join(x[1:] for x in diff.splitlines()
                     if x.startswith("+") and not x.startswith("+++"))


def guarded_proposal(diff: str) -> bool:
    try:
        text = added_source(diff)
        start = text.index("static bool32 SourceFirstWildSingleMove(")
        # The source function signature is unchanged context, not a "+".
        # Bound added lines at the next added first-stage local declaration.
        finish = text.index("u32 proposedSlot = MAX_MON_MOVES;", start)
        body = text[start:finish]
        capture = body.index(FREEZE[0])
        target = body.index("GetBattlerMoveTargetType(battler, move)")
        after = body.index("if (!verifyReply && (!SourceFirstWildSingleOwner(battler) ||")
        emit = body.index("*reply = slot; // Record proposal")
        if not all(body.count(x) == 1 for x in (*FREEZE, *CHECK)):
            return False
        if not (capture < target < after < emit):
            return False
        if not (all(body.index(x) < target for x in FREEZE) and
                all(after < body.index(x) < emit for x in CHECK)):
            return False
        if "if (!verifyReply && (!SourceFirstWildSingleOwner(battler) ||" not in body:
            return False
        if "if (verifyReply && !SourceFirstWildLeaseSnapshotMatches(battler))" not in body:
            return False
        if "B_ACTION_USE_ITEM" in body or "B_ACTION_SWITCH" in body:
            return False
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class Request:
    owner: int = 0
    opponent: int = 1
    turn: int = 7
    owner_party: int = 0
    foe_party: int = 0
    player_active: bool = True
    in_battle: bool = True
    terminal: bool = False
    command: str = "CHOOSEACTION"
    slot: int = 1
    pp: int = 8


def stage_fight(before: Request, after_target: Request):
    # Narrow model of the new additional check; real source also checks
    # native owner/command/target/move, final snapshot and dynamic legality.
    if before.owner != 0 or before.opponent != 1 or before.pp == 0:
        return None
    if not (before.player_active and before.in_battle and not before.terminal and
            after_target.player_active and after_target.in_battle and
            not after_target.terminal and before.command == after_target.command ==
            "CHOOSEACTION" and before.owner == after_target.owner and
            before.opponent == after_target.opponent):
        return None
    if ((before.turn, before.owner_party, before.foe_party) !=
            (after_target.turn, after_target.owner_party, after_target.foe_party)):
        return None
    return ("FIGHT", before.slot)


class PlayerProposalTargetContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.diff = PATCH.read_text(encoding="utf-8")

    def test_live_source_guard(self):
        self.assertTrue(guarded_proposal(self.diff))

    def test_each_guard_removed_or_weakened(self):
        for line in (*FREEZE, *CHECK):
            with self.subTest(line=line):
                self.assertFalse(guarded_proposal(self.diff.replace(line, "GONE", 1)))
        for needle in ("if (!verifyReply && (!SourceFirstWildSingleOwner(battler) ||",
                       "if (verifyReply && !SourceFirstWildLeaseSnapshotMatches(battler))"):
            with self.subTest(needle=needle):
                self.assertFalse(guarded_proposal(self.diff.replace(needle, "if (FALSE &&", 1)))

    def test_guard_must_precede_target_helper_and_fight_emit(self):
        source = self.diff
        header = "+        u16 preTargetTurn = gBattleTurnCounter;\n"
        after_target = "+        if (!verifyReply && (!SourceFirstWildSingleOwner(battler) ||\n"
        self.assertIn(header, source)
        self.assertIn(after_target, source)
        self.assertFalse(guarded_proposal(source.replace(header, "", 1)))
        self.assertFalse(guarded_proposal(source.replace(after_target, "", 1)))

    def test_no_turn_drift_from_target_helper(self):
        state = Request()
        self.assertEqual(stage_fight(state, state), ("FIGHT", 1))
        for val in (6, 8, 0):
            with self.subTest(turn=val):
                self.assertIsNone(stage_fight(state, replace(state, turn=val)))

    def test_no_owner_or_foe_party_drift_from_target_helper(self):
        state = Request()
        for changes in ({"owner_party": 1}, {"foe_party": 1},
                        {"owner_party": 1, "foe_party": 1}):
            with self.subTest(changes=changes):
                self.assertIsNone(stage_fight(state, replace(state, **changes)))

    def test_terminal_inactive_or_replaced_command_still_fallback(self):
        state = Request()
        for change in ({"terminal": True}, {"in_battle": False},
                       {"player_active": False}, {"command": "CHOOSEMOVE"},
                       {"owner": 1}, {"opponent": 0}):
            with self.subTest(change=change):
                self.assertIsNone(stage_fight(state, replace(state, **change)))

    def test_no_enemy_hidden_moves_items_or_ai_writes_added(self):
        s = added_source(self.diff)
        for forbidden in ("gBattleMons[foe].moves", "gBattleMons[foe].pp",
                          "gBattleMons[foe].items", "gBattleMons[foe].innates",
                          "gBattlerControllerFuncs[foe] =",
                          "B_ACTION_USE_ITEM", "B_ACTION_SWITCH",
                          "B_ACTION_RUN"):
            self.assertNotIn(forbidden, s)


if __name__ == "__main__":
    unittest.main()
