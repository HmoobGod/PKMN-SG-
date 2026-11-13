#!/usr/bin/env python3
"""Player-owned move/PP pool continuity before Fight (public source-LAB only).

C patch structural regression + negative mutation and synthetic, immutable
player-owned moves/PP fixtures. Never opens or executes a private game file.
"""
from pathlib import Path
from dataclasses import dataclass, replace
import re
import unittest

PATCH = Path(__file__).resolve().parents[1] / "source-first" / "wild-single-lab.patch"
CAPTURE = (
    "preTargetMoves[poolSlot] = gBattleMons[battler].moves[poolSlot];",
    "preTargetPP[poolSlot] = gBattleMons[battler].pp[poolSlot];",
)
COMPARE = (
    "gBattleMons[battler].moves[poolSlot] != preTargetMoves[poolSlot]",
    "gBattleMons[battler].pp[poolSlot] != preTargetPP[poolSlot]",
)
LOOP = "for (slot = 0; slot < MAX_MON_MOVES; slot++)"
POOL_LOOP = "for (poolSlot = 0; poolSlot < MAX_MON_MOVES; poolSlot++)"


def added_source(patch):
    lines = patch.splitlines()
    if lines[:2] != ["--- a/src/battle_controller_player.c",
                     "+++ b/src/battle_controller_player.c"]:
        raise ValueError("Unexpected C patch target")
    return "\n".join(line[1:] for line in lines[2:]
                     if line.startswith("+") and not line.startswith("+++"))


def guarded_pool(patch):
    try:
        added = added_source(patch)
        start = added.index("static bool32 SourceFirstWildSingleMove(")
        end = added.index("u32 proposedSlot = MAX_MON_MOVES;", start)
        raw = added[start:end]
        # Do not mistake disabled preprocessor branches for live protection.
        if re.search(r"(?m)^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b", raw):
            return False
        text = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)
        text = re.sub(r"//[^\n]*", "", text)

        move_loop = text.index(LOOP)
        first_helper = text.index("GetBattlerMoveTargetType(battler, move)")
        second_helper = text.index("CanTargetBattler(battler, foe, move)")
        identity_gate = text.index("if (!verifyReply && (!SourceFirstWildSingleOwner(battler)")
        skip = text.index("if (!canTarget)\n            continue;")
        proposal = text.index("*reply = slot;")
        if not (move_loop < first_helper < second_helper < identity_gate < skip < proposal):
            return False

        # A single whole-move-pool baseline before any candidate can run helpers.
        capture_pattern = (
            r"if\s*\(!verifyReply\)\s*\{\s*"
            r"for\s*\(poolSlot\s*=\s*0;\s*poolSlot\s*<\s*MAX_MON_MOVES;\s*poolSlot\+\+\)\s*\{\s*"
            r"preTargetMoves\[poolSlot\]\s*=\s*gBattleMons\[battler\]\.moves\[poolSlot\];\s*"
            r"preTargetPP\[poolSlot\]\s*=\s*gBattleMons\[battler\]\.pp\[poolSlot\];\s*\}\s*\}"
        )
        snapshot = re.search(capture_pattern, text, re.S)
        if snapshot is None or not (snapshot.end() < move_loop):
            return False

        # Require the real C guard after target helpers and BEFORE candidate skip.
        check_pattern = (
            r"if\s*\(!verifyReply\)\s*\{\s*"
            r"for\s*\(poolSlot\s*=\s*0;\s*poolSlot\s*<\s*MAX_MON_MOVES;\s*poolSlot\+\+\)\s*\{\s*"
            r"if\s*\(gBattleMons\[battler\]\.moves\[poolSlot\]\s*!=\s*preTargetMoves\[poolSlot\]\s*\|\|\s*"
            r"gBattleMons\[battler\]\.pp\[poolSlot\]\s*!=\s*preTargetPP\[poolSlot\]\)\s*"
            r"return\s+FALSE;\s*\}\s*\}"
        )
        checks = list(re.finditer(check_pattern, text, re.S))
        if len(checks) != 1 or not (second_helper < checks[0].start() <
                                    checks[0].end() < identity_gate):
            return False
        if any(text.count(line) != 2 for line in (POOL_LOOP,)):
            return False
        if any(text.count(line) != 1 for line in (*CAPTURE, *COMPARE)):
            return False
        for var in ("preTargetMoves", "preTargetPP"):
            if text.count(var) != 3:  # declaration, assignment, comparison
                return False
        guard = text[checks[0].start(): checks[0].end()]
        if re.search(r"&&\s*(?:0|FALSE)\b|\|\|\s*(?:1|TRUE)\b", guard):
            return False
        if any(x in text for x in ("gBattleMons[foe].pp", "gBattleMons[foe].moves",
                                  "B_ACTION_USE_ITEM", "B_ACTION_SWITCH")):
            return False
        return True
    except (ValueError, IndexError):
        return False


@dataclass(frozen=True)
class PlayerPool:
    moves: tuple = (33, 44, 55, 66)
    pp: tuple = (8, 6, 5, 3)
    turn: int = 4
    owner_party: int = 0
    foe_party: int = 0


def proposal_survives(before, after):
    """Minimal negative model: source guard never silently reselects slots."""
    return before == after


class TestPreTargetPoolContinuity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch = PATCH.read_text(encoding="utf-8")

    def test_real_source_has_proposal_wide_read_only_guard(self):
        self.assertTrue(guarded_pool(self.patch))

    def test_each_capture_or_comparison_must_remain_live(self):
        for line in (*CAPTURE, *COMPARE):
            for changed in ("GONE;", "/* " + line + " */"):
                with self.subTest(line=line, changed=changed):
                    self.assertFalse(guarded_pool(self.patch.replace(line, changed, 1)))

    def test_preprocessor_dead_code_never_qualifies(self):
        line = CAPTURE[0]
        mutated = self.patch.replace(line, "#if 0\n+        " + line + "\n+        #endif", 1)
        self.assertFalse(guarded_pool(mutated))

    def test_weakened_check_or_skipped_snapshot_rejected(self):
        for before, after in (
            (COMPARE[0], COMPARE[0] + " || 1"),
            (COMPARE[1], COMPARE[1] + " && 0"),
            ("if (!verifyReply)\n+        {\n+            for (poolSlot",
             "if (0 && !verifyReply)\n+        {\n+            for (poolSlot"),
        ):
            with self.subTest(after=after):
                self.assertFalse(guarded_pool(self.patch.replace(before, after, 1)))

    def test_pool_scan_cannot_be_reduced_to_single_move(self):
        self.assertFalse(guarded_pool(
            self.patch.replace("poolSlot < MAX_MON_MOVES", "poolSlot < 1")))

    def test_no_later_slot_promoted_after_prior_helper_mutates_it(self):
        state = PlayerPool()
        self.assertTrue(proposal_survives(state, state))
        for mutated in (replace(state, moves=(33, 99, 55, 66)),
                        replace(state, pp=(8, 4, 5, 3)),
                        replace(state, moves=(99, 44, 55, 66)),
                        replace(state, pp=(8, 6, 5, 0))):
            with self.subTest(mutated=mutated):
                self.assertFalse(proposal_survives(state, mutated))

    def test_other_original_identity_drift_still_rejected(self):
        state = PlayerPool()
        for mutated in (replace(state, turn=5), replace(state, owner_party=2),
                        replace(state, foe_party=3)):
            self.assertFalse(proposal_survives(state, mutated))

    def test_no_opponent_hidden_pool_read_or_actions(self):
        added = added_source(self.patch)
        for forbidden in ("gBattleMons[foe].pp", "gBattleMons[foe].moves",
                          "gBattlerControllerFuncs[foe] =", "B_ACTION_USE_ITEM",
                          "B_ACTION_SWITCH", "B_ACTION_RUN"):
            self.assertNotIn(forbidden, added)


if __name__ == "__main__":
    unittest.main()
