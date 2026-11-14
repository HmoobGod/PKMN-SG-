#!/usr/bin/env python3
"""Source-only foe held-item, innate and volatile continuity guard.
No protected ROM/save, original game, or emulator is read or executed.
Only synthetic state and the disposable player controller patch are tested.
"""
from dataclasses import dataclass, replace
from pathlib import Path
import re
import unittest

PATCH = Path(__file__).resolve().parents[1]/"source-first"/"wild-single-lab.patch"
SCALARS = {
    "preTargetFoeItem": "gBattleMons[foe].item",
    "preTargetFoeTaunt": "gBattleMons[foe].volatiles.tauntTimer",
    "preTargetFoeDisable": "gBattleMons[foe].volatiles.disableTimer",
    "preTargetFoeEncore": "gBattleMons[foe].volatiles.encoreTimer",
    "preTargetFoeTorment": "gBattleMons[foe].volatiles.tormentTimer",
}
ARRAYS = {
    "preTargetFoeItems": ("MAX_MON_ITEMS_INTERNAL", "items"),
    "preTargetFoeInnates": ("MAX_MON_INNATES_INTERNAL", "innates"),
}
LEASE = {
    "foeItem": "item",
    "foeTauntTimer": "volatiles.tauntTimer",
    "foeDisableTimer": "volatiles.disableTimer",
    "foeEncoreTimer": "volatiles.encoreTimer",
    "foeTormentTimer": "volatiles.tormentTimer",
}
WRITE = r"(?:=(?!=)|(?:<<|>>|[+*/%&|^-])=|\+\+|--)"

def source_of(diff):
    if not diff.startswith("--- a/src/battle_controller_player.c\n"
                           "+++ b/src/battle_controller_player.c\n"):
        raise ValueError("wrong C source target")
    return "\n".join(s[1:] for s in diff.splitlines()
                     if s.startswith("+") and not s.startswith("+++"))

def has_foe_guards(diff):
    try:
        src=source_of(diff)
        move=src[src.index("static bool32 SourceFirstWildSingleMove("):
                 src.index("u32 proposedSlot = MAX_MON_MOVES;")]
        arm=src[src.index("static void SourceFirstArmWildLease("):
                src.index("static bool32 SourceFirstWildLeaseSnapshotMatches(")]
        snap=src[src.index("static bool32 SourceFirstWildLeaseSnapshotMatches("):
                 src.index("static bool32 SourceFirstConsumeWildLease(")]
        move=re.sub(r"/\*.*?\*/", "", move, flags=re.S)
        move=re.sub(r"//[^\n]*", "", move)
        if re.search(r"(?m)^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b", move):
            return False
        helper=move.index("GetBattlerMoveTargetType(battler, move)")
        helper2=move.index("CanTargetBattler(battler, foe, move)")
        skip=move.index("if (!canTarget)\n            continue;")
        reply=move.index("*reply = slot;",skip)
        if not helper<helper2<skip<reply:
            return False
        for name,field in SCALARS.items():
            frozen=f"{name} = {field};"
            check=f"{field} != {name}"
            if move.count(frozen)!=1 or move.count(check)!=1:
                return False
            if not(move.index(frozen)<helper<helper2<move.index(check)<skip):
                return False
            if len(re.findall(r"\b"+name+WRITE,move))!=1:
                return False
        for name,(length,field) in ARRAYS.items():
            freeze=(f"for (poolSlot = 0; poolSlot < {length}; poolSlot++)\n"
                    f"        {name}[poolSlot] = gBattleMons[foe].{field}[poolSlot];")
            check=(f"for (poolSlot = 0; poolSlot < {length}; poolSlot++)\n"
                   "            {\n"
                   f"                if (gBattleMons[foe].{field}[poolSlot] != {name}[poolSlot])\n"
                   "                    return FALSE;\n"
                   "            }")
            if freeze not in move or check not in move:
                return False
            if not(move.index(freeze)<helper<helper2<move.index(check)<skip):
                return False
            if len(re.findall(r"\b"+name+r"\[[^\]\n]+\]"+WRITE,move))!=1:
                return False
        if "if (!verifyReply)\n        {\n            if (gBattleMons[foe].item" not in move:
            return False
        if not(helper2<move.index("if (!verifyReply)\n        {\n"
                                    "            if (gBattleMons[foe].item")<skip):
            return False
        for name,field in LEASE.items():
            cap=f"sSourceFirstWildLease.{name} = gBattleMons[sSourceFirstWildLease.foe].{field};"
            chk=f"gBattleMons[sSourceFirstWildLease.foe].{field} != sSourceFirstWildLease.{name}"
            if arm.count(cap)!=1 or snap.count(chk)!=1:
                return False
        for name,field,length in (
            ("foeItems","items","MAX_MON_ITEMS_INTERNAL"),
            ("foeInnates","innates","MAX_MON_INNATES_INTERNAL"),
        ):
            if (f"for (slot = 0; slot < {length}; slot++)\n"
                f"        sSourceFirstWildLease.{name}[slot] = "
                f"gBattleMons[sSourceFirstWildLease.foe].{field}[slot];") not in arm:
                return False
            if (f"sSourceFirstWildLease.{name}[slot] !=\n"
                f"            gBattleMons[sSourceFirstWildLease.foe].{field}[slot]") not in snap:
                return False
        if any(t in src for t in ("B_ACTION_USE_ITEM", "B_ACTION_SWITCH",
                                  "B_ACTION_RUN", "gBattleMons[foe].moves",
                                  "gBattleMons[foe].pp", "gBattlerControllerFuncs[foe] =")):
            return False
        return True
    except ValueError:
        return False

@dataclass(frozen=True)
class FoeEffects:
    item:int=1
    taunt:int=0
    disable:int=0
    encore:int=0
    torment:int=0
    innates:tuple=(3,4,0)
    items:tuple=(1,0)

class SourceFoeEffectsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch=PATCH.read_text(encoding="utf-8")
    def test_actual_source_foe_effects_checked_before_proposal(self):
        self.assertTrue(has_foe_guards(self.patch))
    def test_removing_each_snapshot_field_or_guard_is_denied(self):
        for name,field in SCALARS.items():
            for token in (f"{name} = {field};",f"{field} != {name}"):
                with self.subTest(token=token):
                    self.assertFalse(has_foe_guards(self.patch.replace(token,"REMOVED",1)))
    def test_removing_cross_stage_lease_checks_denied(self):
        for name,field in LEASE.items():
            token=f"gBattleMons[sSourceFirstWildLease.foe].{field} != sSourceFirstWildLease.{name}"
            with self.subTest(token=token):
                self.assertFalse(has_foe_guards(self.patch.replace(token,"REMOVED",1)))
    def test_shortened_arrays_or_forged_rebaseline_denied(self):
        for name,(length,field) in ARRAYS.items():
            before=(f"poolSlot < {length}; poolSlot++)\n+        {name}[poolSlot]")
            self.assertIn(before,self.patch)
            self.assertFalse(has_foe_guards(self.patch.replace(before,before.replace(length,"1"),1)))
            precheck=(f"poolSlot < {length}; poolSlot++)\n+            {{\n"
                      f"+                if (gBattleMons[foe].{field}[poolSlot]")
            self.assertIn(precheck,self.patch)
            self.assertFalse(has_foe_guards(self.patch.replace(precheck,precheck.replace(length,"1"),1)))
            rebaseline=f"+        {name}[0] = gBattleMons[foe].{field}[0];\n"
            anchor="+        /* A targeting helper may mutate an EARLIER or LATER move/PP slot."
            self.assertIn(anchor,self.patch)
            self.assertFalse(has_foe_guards(self.patch.replace(anchor,rebaseline+anchor,1)))
        for name,field in SCALARS.items():
            anchor="+        /* A targeting helper may mutate an EARLIER or LATER move/PP slot."
            self.assertFalse(has_foe_guards(self.patch.replace(
                anchor,f"+        {name} = {field};\n"+anchor,1)))
    def test_dead_first_stage_gate_denied(self):
        token="if (!verifyReply)\n+        {\n+            if (gBattleMons[foe].item"
        self.assertIn(token,self.patch)
        self.assertFalse(has_foe_guards(self.patch.replace(
            token,token.replace("if (!verifyReply)","if (FALSE && !verifyReply)"),1)))
    def test_foe_drift_never_laundered_into_a_fresh_lease(self):
        old=FoeEffects()
        self.assertEqual(old,old)
        for key,value in (("item",5),("taunt",1),("disable",1),
                          ("encore",1),("torment",1),("innates",(3,5,0)),
                          ("items",(1,8))):
            with self.subTest(key=key):
                self.assertNotEqual(old,replace(old,**{key:value}))
if __name__=="__main__":
    unittest.main()
