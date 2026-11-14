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
    """Fail closed unless live C guards protect one entire proposal.

    Inspect the added C text rather than a Python-only behavior model. Reject
    any conditional compilation in this small guard region, remove comments,
    and require an unweakened conditional BEFORE the ineligible-slot continue.
    """
    try:
        import re

        text = added_source(diff)
        start = text.index("static bool32 SourceFirstWildSingleMove(")
        finish = text.index("u32 proposedSlot = MAX_MON_MOVES;", start)
        raw = text[start:finish]
        # The patch has no conditional compilation inside this source function.
        # Reject it rather than mistaking '#if 0' dead code for a live guard.
        if re.search(r"(?m)^\s*#\s*(?:if|ifdef|ifndef|elif|else|endif)\b", raw):
            return False
        body = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)
        body = re.sub(r"//[^\n]*", "", body)

        loop = body.index("for (slot = 0; slot < MAX_MON_MOVES; slot++)")
        target = body.index("GetBattlerMoveTargetType(battler, move)")
        second_helper = body.index("CanTargetBattler(battler, foe, move)")
        guard = body.index("if (!verifyReply && (!SourceFirstWildSingleOwner(battler) ||")
        guard_end = body.index("))\n            return FALSE;", guard)
        eligible_skip = body.index("if (!canTarget)\n            continue;", guard_end)
        emit = body.index("*reply = slot;", eligible_skip)
        if not (loop < target < second_helper < guard < guard_end <
                eligible_skip < emit):
            return False

        # Every identity is read exactly ONCE before the move loop, then
        # compared exactly ONCE inside the mandatory post-helper guard.
        for name, decl, check in zip(
                ("preTargetTurn", "preTargetPlayerParty", "preTargetFoeParty"),
                FREEZE, CHECK):
            if body.count(name) != 2 or body.count(decl) != 1:
                return False
            if body.count(check) != 1:
                return False
            if not (body.index(decl) < loop < guard < body.index(check) < guard_end):
                return False
        guard_text = body[guard:guard_end]
        if not all(line in guard_text for line in CHECK):
            return False
        # Presence alone is not enough if the conditional is neutralized.
        if re.search(r"&&\s*(?:0|FALSE)\b|\|\|\s*(?:1|TRUE)\b", guard_text):
            return False
        if not all(body.count(x) == 1 for x in (*FREEZE, *CHECK)):
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
        header = "+    u16 preTargetTurn = gBattleTurnCounter;\n"
        after_target = "+        if (!verifyReply && (!SourceFirstWildSingleOwner(battler) ||\n"
        self.assertIn(header, source)
        self.assertIn(after_target, source)
        self.assertFalse(guarded_proposal(source.replace(header, "", 1)))
        self.assertFalse(guarded_proposal(source.replace(after_target, "", 1)))

    def test_guard_rejects_comments_preprocessor_and_tautologies(self):
        # All five failure modes from independent exact-head review.
        for line in (*FREEZE, *CHECK):
            with self.subTest(commented=line):
                self.assertFalse(guarded_proposal(
                    self.diff.replace(line, "/* " + line + " */", 1)))
        mutations = (
            (CHECK[0], "/* " + CHECK[0] + " */"),
            (FREEZE[0], "/* " + FREEZE[0] + " */"),
            (FREEZE[0], "#if 0\n+        " + FREEZE[0] + "\n+        #endif"),
            (CHECK[0], CHECK[0].replace(" ||", " && 0 ||")),
            (CHECK[0], CHECK[0].replace(" ||", " || 1 ||")),
        )
        for needle, poison in mutations:
            with self.subTest(poison=poison):
                self.assertNotEqual(needle, poison)
                self.assertFalse(guarded_proposal(self.diff.replace(needle, poison, 1)))

    def test_single_freeze_outside_slot_loop_and_never_retaken(self):
        loop = "+    for (slot = 0; slot < MAX_MON_MOVES; slot++)\n"
        freeze = "+    u16 preTargetTurn = gBattleTurnCounter;\n"
        self.assertIn(loop, self.diff)
        self.assertIn(freeze, self.diff)
        # Move the capture back inside the loop (the original B1 defect).
        marker = "+    u8 preTargetFoeParty = gBattlerPartyIndexes[foe];\n"
        self.assertIn(marker, self.diff)
        self.assertLess(self.diff.index(marker), self.diff.index(loop, self.diff.index(marker)))
        # The move/PP pool freeze may legitimately occupy the gap between
        # original identity freeze and candidate loop on stacked LAB work.
        stripped = self.diff.replace(freeze, "", 1)
        start = stripped.index("static bool32 SourceFirstWildSingleMove(")
        loop_pos = stripped.index(loop, start)
        relocated = (stripped[:loop_pos + len(loop)] +
                     "+        u16 preTargetTurn = gBattleTurnCounter;\n" +
                     stripped[loop_pos + len(loop):])
        self.assertFalse(guarded_proposal(relocated))
        # A second baseline assignment after a target helper masks drift.
        helper = "+        canTarget = !(GetBattlerMoveTargetType(battler, move) != TARGET_SELECTED ||\n"
        self.assertIn(helper, self.diff)
        neutralized = self.diff.replace(
            helper, helper + "+        preTargetTurn = gBattleTurnCounter;\n", 1)
        self.assertFalse(guarded_proposal(neutralized))

    def test_post_helper_guard_must_precede_ineligible_continue(self):
        skip = "+        if (!canTarget)\n+            continue;\n"
        self.assertIn(skip, self.diff)
        self.assertTrue(guarded_proposal(self.diff))
        early = self.diff.replace(
            skip, "", 1).replace(
            "+        /* Source-LAB action proposal:",
            skip + "+        /* Source-LAB action proposal:", 1)
        self.assertFalse(guarded_proposal(early))

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
                          "gBattlerControllerFuncs[foe] =",
                          "B_ACTION_USE_ITEM", "B_ACTION_SWITCH",
                          "B_ACTION_RUN"):
            self.assertNotIn(forbidden, s)
        # A passive read of foe items/innates is required to prevent target
        # helper drift. The safety rule is NO OPPONENT WRITES, not no reads.
        import re
        for who in ("foe", "sSourceFirstWildLease.foe"):
            for field in ("items", "innates"):
                pat = (r"gBattleMons\\["+re.escape(who)+r"\\]\\."+field+
                       r"\\[[^\\]\\n]+\\]\\s*(?:=(?!=)|[+*/%&|^-]=|\\+\\+|--)")
                self.assertIsNone(re.search(pat,s))


if __name__ == "__main__":
    unittest.main()
