#!/usr/bin/env python3
"""Source-only first-stage foe identity/typing continuity regression.

The approved player-only disposable source-LAB remains a research fixture.
No private ROM/save, emulator, or original-game CPU is read or executed.
"""
from dataclasses import dataclass, replace
from pathlib import Path
import re
import unittest

PATCH = Path(__file__).resolve().parents[1] / "source-first" / "wild-single-lab.patch"
CAPTURE = (
    "u16 preTargetFoeSpecies = gBattleMons[foe].species;",
    "u16 preTargetFoeHp = gBattleMons[foe].hp;",
    "u32 preTargetFoeStatus1 = gBattleMons[foe].status1;",
    "enum Ability preTargetFoeAbility = gBattleMons[foe].ability;",
    "enum Type preTargetFoeTypes[3];",
    "preTargetFoeTypes[poolSlot] = gBattleMons[foe].types[poolSlot];",
)
RECHECK = (
    "gBattleMons[foe].species != preTargetFoeSpecies ||",
    "gBattleMons[foe].hp != preTargetFoeHp ||",
    "gBattleMons[foe].status1 != preTargetFoeStatus1 ||",
    "gBattleMons[foe].ability != preTargetFoeAbility)",
    "gBattleMons[foe].types[poolSlot] != preTargetFoeTypes[poolSlot]",
)


def added_source(diff):
    if not diff.startswith("--- a/src/battle_controller_player.c\n"
                           "+++ b/src/battle_controller_player.c\n"):
        raise ValueError("wrong original player source target")
    return "\n".join(line[1:] for line in diff.splitlines()
                     if line.startswith("+") and not line.startswith("+++"))


def guarded_foe_proposal(diff):
    try:
        code = added_source(diff)
        start = code.index("static bool32 SourceFirstWildSingleMove(")
        finish = code.index("u32 proposedSlot = MAX_MON_MOVES;", start)
        raw = code[start:finish]
        if re.search(r"(?m)^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b", raw):
            return False
        body = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)
        body = re.sub(r"//[^\n]*", "", body)
        helper = body.index("GetBattlerMoveTargetType(battler, move)")
        helper2 = body.index("CanTargetBattler(battler, foe, move)")
        skip = body.index("if (!canTarget)\n            continue;")
        proposal = body.index("*reply = slot;", skip)
        if not (helper < helper2 < skip < proposal):
            return False
        if any(body.count(x) != 1 for x in (*CAPTURE, *RECHECK)):
            return False
        if any(body.index(x) > helper for x in CAPTURE):
            return False
        if any(not (helper2 < body.index(x) < skip) for x in RECHECK):
            return False
        freeze_loop = ("for (poolSlot = 0; poolSlot < 3; poolSlot++)\n"
                       "        preTargetFoeTypes[poolSlot] = gBattleMons[foe].types[poolSlot];")
        if freeze_loop not in body or body.index(freeze_loop) > helper:
            return False
        gate = re.search(
            r"if\s*\(!verifyReply\)\s*\{\s*"
            r"if\s*\(\s*gBattleMons\[foe\]\.species\s*!=\s*preTargetFoeSpecies\s*\|\|\s*"
            r"gBattleMons\[foe\]\.hp\s*!=\s*preTargetFoeHp\s*\|\|\s*"
            r"gBattleMons\[foe\]\.status1\s*!=\s*preTargetFoeStatus1\s*\|\|\s*"
            r"gBattleMons\[foe\]\.ability\s*!=\s*preTargetFoeAbility\s*\)\s*"
            r"return\s+FALSE;\s*"
            r"for\s*\(poolSlot\s*=\s*0;\s*poolSlot\s*<\s*3;\s*poolSlot\+\+\)\s*"
            r"\{\s*if\s*\(gBattleMons\[foe\]\.types\[poolSlot\]\s*!=\s*"
            r"preTargetFoeTypes\[poolSlot\]\)\s*return\s+FALSE;\s*\}\s*\}",
            body, re.S)
        if gate is None or not (helper2 < gate.start() < gate.end() < skip):
            return False
        if any(v in body[gate.start():gate.end()] for v in ("|| TRUE", "|| 1", "&& FALSE", "&& 0")):
            return False
        return "B_ACTION_USE_ITEM" not in body and "gBattleMons[foe].moves" not in body
    except ValueError:
        return False


@dataclass(frozen=True)
class Foe:
    species: int = 6
    hp: int = 55
    status1: int = 0
    ability: int = 8
    types: tuple = (10, 0, 0)


def proposal_survives_helper(before, after):
    return before == after


class FoeContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch = PATCH.read_text(encoding="utf-8")

    def test_actual_player_lab_patch_guard(self):
        self.assertTrue(guarded_foe_proposal(self.patch))

    def test_capture_and_recheck_removal_detected(self):
        for item in (*CAPTURE, *RECHECK):
            with self.subTest(item=item):
                self.assertFalse(guarded_foe_proposal(
                    self.patch.replace(item, "REMOVED", 1)))

    def test_dead_or_disabled_guard_detected(self):
        for before, after in (
            ("if (!verifyReply)\n+        {\n+            if (gBattleMons[foe].species",
             "if (FALSE && !verifyReply)\n+        {\n+            if (gBattleMons[foe].species"),
            (RECHECK[0], "/* "+RECHECK[0]+" */"),
            (CAPTURE[0], "#if 0\n+    "+CAPTURE[0]+"\n+    #endif"),
            ("poolSlot < 3; poolSlot++)\n+        preTargetFoeTypes",
             "poolSlot < 1; poolSlot++)\n+        preTargetFoeTypes"),
            ("poolSlot < 3; poolSlot++)\n+            {\n+                if (gBattleMons[foe].types",
             "poolSlot < 1; poolSlot++)\n+            {\n+                if (gBattleMons[foe].types"),
        ):
            with self.subTest(before=before):
                self.assertIn(before, self.patch)
                self.assertFalse(guarded_foe_proposal(
                    self.patch.replace(before, after, 1)))

    def test_drift_after_target_helper_rejected_for_ineligible_slot(self):
        old = Foe()
        self.assertTrue(proposal_survives_helper(old, old))
        for changed in (replace(old, species=7), replace(old, hp=54),
                        replace(old, status1=1), replace(old, ability=9),
                        replace(old, types=(10, 2, 0)),
                        replace(old, types=(10, 0, 3))):
            with self.subTest(changed=changed):
                self.assertFalse(proposal_survives_helper(old, changed))

    def test_player_only_no_foe_hidden_moves_or_controller_mutation(self):
        code = added_source(self.patch)
        for banned in ("gBattleMons[foe].moves", "gBattleMons[foe].pp",
                       "gBattlerControllerFuncs[foe] =", "B_ACTION_USE_ITEM",
                       "B_ACTION_SWITCH", "B_ACTION_RUN"):
            self.assertNotIn(banned, code)


if __name__ == "__main__":
    unittest.main()
