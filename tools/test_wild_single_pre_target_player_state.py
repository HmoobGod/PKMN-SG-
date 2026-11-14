#!/usr/bin/env python3
"""Player0 source-LAB first-stage player state continuity, synthetic only.

This test inspects the live added C source in the disposable patch, plus
negative state mutations. No protected original ROM/save/emulator is opened.
"""
from dataclasses import dataclass, replace
from pathlib import Path
import re
import unittest

PATCH=Path(__file__).resolve().parents[1]/"source-first"/"wild-single-lab.patch"
CAPTURE=(
    "u16 preTargetPlayerSpecies = gBattleMons[battler].species;",
    "u16 preTargetPlayerHp = gBattleMons[battler].hp;",
    "u32 preTargetPlayerStatus1 = gBattleMons[battler].status1;",
    "enum Ability preTargetPlayerAbility = gBattleMons[battler].ability;",
    "enum Item preTargetPlayerItem = gBattleMons[battler].item;",
    "u32 preTargetTaunt = gBattleMons[battler].volatiles.tauntTimer;",
    "u32 preTargetDisable = gBattleMons[battler].volatiles.disableTimer;",
    "u32 preTargetEncore = gBattleMons[battler].volatiles.encoreTimer;",
    "u32 preTargetTorment = gBattleMons[battler].volatiles.tormentTimer;",
)
COMPARE=(
    "gBattleMons[battler].species != preTargetPlayerSpecies ||",
    "gBattleMons[battler].hp != preTargetPlayerHp ||",
    "gBattleMons[battler].status1 != preTargetPlayerStatus1 ||",
    "gBattleMons[battler].ability != preTargetPlayerAbility ||",
    "gBattleMons[battler].item != preTargetPlayerItem ||",
    "gBattleMons[battler].volatiles.tauntTimer != preTargetTaunt ||",
    "gBattleMons[battler].volatiles.disableTimer != preTargetDisable ||",
    "gBattleMons[battler].volatiles.encoreTimer != preTargetEncore ||",
    "gBattleMons[battler].volatiles.tormentTimer != preTargetTorment)",
)
ARRAYS=(
    ("3","preTargetPlayerTypes","types"),
    ("MAX_MON_INNATES_INTERNAL","preTargetPlayerInnates","innates"),
    ("MAX_MON_ITEMS_INTERNAL","preTargetPlayerItems","items"),
)


def added(diff):
    if not diff.startswith("--- a/src/battle_controller_player.c\n"
                           "+++ b/src/battle_controller_player.c\n"):
        raise ValueError("wrong C patch destination")
    return "\n".join(x[1:] for x in diff.splitlines()
                     if x.startswith("+") and not x.startswith("+++"))


def player_gate_valid(diff):
    try:
        src=added(diff)
        st=src.index("static bool32 SourceFirstWildSingleMove(")
        en=src.index("u32 proposedSlot = MAX_MON_MOVES;", st)
        raw=src[st:en]
        if re.search(r"(?m)^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b",raw):
            return False
        code=re.sub(r"/\*.*?\*/","",raw,flags=re.S)
        code=re.sub(r"//[^\n]*","",code)
        helper=code.index("GetBattlerMoveTargetType(battler, move)")
        next_helper=code.index("CanTargetBattler(battler, foe, move)")
        skip=code.index("if (!canTarget)\n            continue;")
        reply=code.index("*reply = slot;",skip)
        if not (helper<next_helper<skip<reply):
            return False
        for c in CAPTURE:
            if code.count(c)!=1 or code.index(c)>helper:
                return False
        for c in COMPARE:
            if code.count(c)!=1 or not next_helper<code.index(c)<skip:
                return False
        for length,name,field in ARRAYS:
            freeze=(f"for (poolSlot = 0; poolSlot < {length}; poolSlot++)\n"
                    f"        {name}[poolSlot] = gBattleMons[battler].{field}[poolSlot];")
            check=(f"for (poolSlot = 0; poolSlot < {length}; poolSlot++)\n"
                   "            {\n"
                   f"                if (gBattleMons[battler].{field}[poolSlot] != {name}[poolSlot])\n"
                   "                    return FALSE;\n"
                   "            }")
            if freeze not in code or check not in code:
                return False
            if not(code.index(freeze)<helper<code.index(check)<skip):
                return False
            if code.count(f"{name}[poolSlot]")!=2:
                return False
        pattern=(r"if\s*\(!verifyReply\)\s*\{\s*"
                 r"if\s*\(\s*gBattleMons\[battler\]\.species\s*!=\s*preTargetPlayerSpecies\s*\|\|"
                 r".*?gBattleMons\[battler\]\.volatiles\.tormentTimer\s*!=\s*preTargetTorment\s*\)"
                 r"\s*return\s+FALSE;")
        guards=list(re.finditer(pattern,code,re.S))
        if len(guards)!=1 or not(next_helper<guards[0].start()<guards[0].end()<skip):
            return False
        if any(t in code[guards[0].start():skip] for t in
               ("|| TRUE","|| 1","&& FALSE","&& 0")):
            return False
        if any(x in code for x in ("B_ACTION_USE_ITEM","B_ACTION_SWITCH",
                                   "B_ACTION_RUN","gBattleMons[foe].moves")):
            return False
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class Player:
    species:int=25
    hp:int=94
    status1:int=0
    ability:int=8
    item:int=11
    taunt:int=0
    disable:int=0
    encore:int=0
    torment:int=0
    types:tuple=(13,0,0)
    innates:tuple=(6,7,0)
    items:tuple=(11,0,0)


def survive_helper(before,after):
    return before==after


class FirstStagePlayerContinuity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch=PATCH.read_text(encoding="utf-8")

    def test_full_original_player0_source_guard(self):
        self.assertTrue(player_gate_valid(self.patch))

    def test_mutated_capture_and_check_must_fail(self):
        for x in (*CAPTURE,*COMPARE):
            with self.subTest(field=x):
                self.assertFalse(player_gate_valid(
                    self.patch.replace(x,"DISABLED",1)))

    def test_array_truncation_must_fail(self):
        for n,name,field in ARRAYS:
            freeze=f"poolSlot < {n}; poolSlot++)\n+        {name}[poolSlot]"
            check=f"poolSlot < {n}; poolSlot++)\n+            {{\n+                if (gBattleMons[battler].{field}[poolSlot]"
            for x in (freeze,check):
                with self.subTest(expression=x):
                    self.assertIn(x,self.patch)
                    self.assertFalse(player_gate_valid(
                        self.patch.replace(x,x.replace(n,"1",1),1)))

    def test_no_dead_guards_or_tautologies(self):
        x=CAPTURE[0]
        self.assertFalse(player_gate_valid(self.patch.replace(
            x,"#if 0\n+    "+x+"\n+    #endif",1)))
        x=COMPARE[0]
        self.assertFalse(player_gate_valid(self.patch.replace(
            x,"/* "+x+" */",1)))
        x="if (!verifyReply)\n+        {\n+            if (gBattleMons[battler].species"
        self.assertIn(x,self.patch)
        self.assertFalse(player_gate_valid(self.patch.replace(
            x,x.replace("if (!verifyReply)","if (FALSE && !verifyReply)"),1)))

    def test_any_first_stage_state_drift_fails(self):
        original=Player()
        self.assertTrue(survive_helper(original,original))
        for k,v in (("species",26),("hp",93),("status1",1),
                    ("ability",9),("item",12),("taunt",2),
                    ("disable",1),("encore",1),("torment",1),
                    ("types",(13,11,0)),("innates",(6,8,0)),
                    ("items",(11,0,24))):
            with self.subTest(state=k):
                self.assertFalse(survive_helper(original,replace(original,**{k:v})))

    def test_no_auto_items_or_enemy_ai(self):
        s=added(self.patch)
        for banned in ("B_ACTION_USE_ITEM","B_ACTION_SWITCH","B_ACTION_RUN",
                       "gBattlerControllerFuncs[foe] =",
                       "gBattleMons[foe].moves","gBattleMons[foe].pp"):
            self.assertNotIn(banned,s)


if __name__=="__main__":
    unittest.main()
