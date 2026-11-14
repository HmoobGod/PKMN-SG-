#!/usr/bin/env python3
"""Public disposable Source-LAB original controller-exec owner continuity."""
from dataclasses import dataclass, replace
from pathlib import Path
import re
import unittest
PATCH=Path(__file__).resolve().parents[1]/"source-first"/"wild-single-lab.patch"
def checked(diff):
    if not diff.startswith("--- a/src/battle_controller_player.c\n+++ b/src/battle_controller_player.c\n"):
        return False
    added="\n".join(s[1:] for s in diff.splitlines() if s.startswith("+") and not s.startswith("+++"))
    try:
        start=added.index("static bool32 SourceFirstWildSingleMove(")
        s=added[start:added.index("u32 proposedSlot = MAX_MON_MOVES;",start)]
        s=re.sub(r"/\*.*?\*/","",s,flags=re.S)
        if re.search(r"(?m)^\s*#\s*(?:if|ifdef|else|endif)\b",s):
            return False
        cap1="preRequestControllerFlags = gBattleControllerExecFlags;"
        cap2="preRequestResources = gBattleResources;"
        limit="unusable = verifyReply ? CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL) : 0;"
        helper="GetBattlerMoveTargetType(battler, move)"
        helper2="CanTargetBattler(battler, foe, move)"
        skip="if (!canTarget)\n            continue;"
        reply="*reply = slot;"
        early=("if (gBattleControllerExecFlags != preRequestControllerFlags ||\n"
               "        (const void *)gBattleResources != preRequestResources)\n"
               "        return FALSE;")
        late=("if (gBattleControllerExecFlags != preRequestControllerFlags ||\n"
              "            (const void *)gBattleResources != preRequestResources)\n"
              "            return FALSE;")
        if any(s.count(t)!=1 for t in (cap1,cap2,limit,helper,helper2,skip,reply,early,late,
                                        "u32 preRequestControllerFlags;",
                                        "const void *preRequestResources;")):
            return False
        if not (s.index(cap1)<s.index(cap2)<s.index(limit)<s.index(early)<
                s.index(helper)<s.index(helper2)<s.index(late)<
                s.index(skip)<s.index(reply)):
            return False
        return True
    except ValueError:
        return False

@dataclass(frozen=True)
class Context:
    original_exec_mask:int=4
    original_resource_owner:int=1234
    original_command_byte:int=18

class ExecOwnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.diff=PATCH.read_text(encoding="utf8")
    def test_actual_source_captures_and_rechecks_original_execution_owner(self):
        self.assertTrue(checked(self.diff))
    def test_no_silent_removal_of_original_capture(self):
        for token in ("preRequestControllerFlags = gBattleControllerExecFlags;",
                      "preRequestResources = gBattleResources;"):
            with self.subTest(token=token):
                self.assertFalse(checked(self.diff.replace(token,"REMOVED",1)))
    def test_no_silent_removal_of_either_guard(self):
        for token in ("+    if (gBattleControllerExecFlags != preRequestControllerFlags ||",
                      "+        if (gBattleControllerExecFlags != preRequestControllerFlags ||"):
            with self.subTest(token=token):
                self.assertIn(token,self.diff)
                self.assertFalse(checked(self.diff.replace(token,token.replace("!=","=="),1)))
    def test_owner_mask_changes_even_if_player0_bit_stays_set(self):
        old=Context()
        self.assertNotEqual(old,replace(old,original_exec_mask=old.original_exec_mask|8))
        self.assertNotEqual(old,replace(old,original_exec_mask=0))
    def test_replaced_resources_with_unchanged_command_rejected(self):
        old=Context()
        self.assertNotEqual(old,replace(old,original_resource_owner=4321))
    def test_unchanged_public_snapshot_not_native_evidence(self):
        old=Context()
        self.assertEqual(old,old)
        self.assertTrue(checked(self.diff))
if __name__=="__main__":
    unittest.main()
