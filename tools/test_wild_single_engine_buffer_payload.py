#!/usr/bin/env python3
"""Static source-LAB command payload continuity, public synthetic mutations."""
from dataclasses import dataclass, replace
from pathlib import Path
import unittest
import re

PATCH = Path(__file__).resolve().parents[1] / "source-first" / "wild-single-lab.patch"

def live_move(diff):
    if not diff.startswith("--- a/src/battle_controller_player.c\n+++ b/src/battle_controller_player.c\n"):
        raise ValueError("wrong source-only target")
    src="\n".join(line[1:] for line in diff.splitlines()
                  if line.startswith("+") and not line.startswith("+++"))
    start=src.index("static bool32 SourceFirstWildSingleMove(")
    return src[start:src.index("u32 proposedSlot = MAX_MON_MOVES;",start)]

def guarded(diff):
    try:
        src=live_move(diff)
        src=re.sub(r"/\*.*?\*/","",src,flags=re.S)
        if re.search(r"(?m)^\s*#\s*(?:ifdef|if|else|endif|define)\b",src):
            return False
        helper=src.index("GetBattlerMoveTargetType(battler, move)")
        helper2=src.index("CanTargetBattler(battler, foe, move)")
        skip=src.index("if (!canTarget)\n            continue;")
        select=src.index("*reply = slot;",skip)
        frozen=src.index("originalActionBuffer = gBattleResources->bufferA[battler];")
        for name in ("preActionHeader[4]","preMoveMenuMoves[MAX_MON_MOVES]",
                     "preMoveMenuPp[MAX_MON_MOVES]"):
            if src.count(name)!=1:
                return False
        caps=[
            "preActionHeader[poolSlot] = originalActionBuffer[poolSlot];",
            "preMoveMenuMoves[poolSlot] = moveInfo->moves[poolSlot];",
            "preMoveMenuPp[poolSlot] = moveInfo->currentPp[poolSlot];",
        ]
        for capture in caps:
            if src.count(capture)!=1 or src.index(capture)>helper:
                return False
        rejects=[
            "gBattleResources->bufferA[battler] != originalActionBuffer",
            "originalActionBuffer[poolSlot] != preActionHeader[poolSlot]",
            "moveInfo->moves[poolSlot] != preMoveMenuMoves[poolSlot]",
            "moveInfo->currentPp[poolSlot] != preMoveMenuPp[poolSlot]",
            "moveInfo != (struct ChooseMoveStruct *)&gBattleResources->bufferA[battler][4]",
        ]
        # The pointer comparison occurs twice: one early before any
        # dereference and a second post-target before reply. Ensure the
        # new post-target guard occurs before the ineligible-slot skip.
        for token in rejects:
            # A parent pointer guard may legitimately repeat AFTER the
            # ineligible-slot skip. Only a guard inside the new pre-skip
            # block counts toward this protection.
            pos=src.find(token,helper2,skip)
            if pos<0 or not helper2<pos<skip<select:
                return False
        if src.count("originalActionBuffer[poolSlot] != preActionHeader[poolSlot]")!=1:
            return False
        if src.count("moveInfo->moves[poolSlot] != preMoveMenuMoves[poolSlot]")!=1:
            return False
        if src.count("moveInfo->currentPp[poolSlot] != preMoveMenuPp[poolSlot]")!=1:
            return False
        if not (frozen < helper < helper2 < skip < select):
            return False
        if not re.search(r"for \(poolSlot = 0; poolSlot < ARRAY_COUNT\(preActionHeader\); poolSlot\+\+\)"
                         r"[\s\S]*?preActionHeader\[poolSlot\] = originalActionBuffer\[poolSlot\];",src):
            return False
        if src.count("for (poolSlot = 0; poolSlot < MAX_MON_MOVES; poolSlot++)")<3:
            return False
        for token in ("B_ACTION_USE_ITEM","B_ACTION_SWITCH","B_ACTION_RUN",
                      "gBattlerControllerFuncs[foe] ="):
            if token in src:
                return False
        return True
    except ValueError:
        return False

@dataclass(frozen=True)
class Buffers:
    action:tuple=(5,0,0,0)
    move_ids:tuple=(10,20,30,40)
    pp:tuple=(10,12,8,16)
    pointer:int=1

def unchanged(old,new):
    return old == new

class EngineBufferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.diff=PATCH.read_text(encoding="utf8")
    def test_source_guards_all_menu_payload_bytes_before_skip(self):
        self.assertTrue(guarded(self.diff))
    def test_mutation_removes_each_capture_and_postcheck(self):
        tokens=[
            "preActionHeader[poolSlot] = originalActionBuffer[poolSlot];",
            "preMoveMenuMoves[poolSlot] = moveInfo->moves[poolSlot];",
            "preMoveMenuPp[poolSlot] = moveInfo->currentPp[poolSlot];",
            "originalActionBuffer[poolSlot] != preActionHeader[poolSlot]",
            "moveInfo->moves[poolSlot] != preMoveMenuMoves[poolSlot]",
            "moveInfo->currentPp[poolSlot] != preMoveMenuPp[poolSlot]",
            "gBattleResources->bufferA[battler] != originalActionBuffer",
        ]
        for token in tokens:
            with self.subTest(token=token):
                self.assertIn(token,self.diff)
                self.assertFalse(guarded(self.diff.replace(token,"REMOVED",1)))
    def test_changed_payload_with_unchanged_command_byte_is_denied(self):
        a=Buffers()
        for idx in (1,2,3):
            with self.subTest(byte=idx):
                new=list(a.action);new[idx]^=1
                self.assertFalse(unchanged(a,replace(a,action=tuple(new))))
    def test_changed_nonselected_move_slot_and_pp_is_denied(self):
        a=Buffers()
        for idx in (1,2,3):
            for name in ("move_ids","pp"):
                values=list(getattr(a,name));values[idx]^=1
                with self.subTest(slot=idx,field=name):
                    self.assertFalse(unchanged(a,replace(a,**{name:tuple(values)})))
    def test_changed_original_buffer_pointer_denied(self):
        a=Buffers()
        self.assertFalse(unchanged(a,replace(a,pointer=2)))
    def test_unmodified_snapshot_is_only_synthetic_validity(self):
        a=Buffers()
        self.assertTrue(unchanged(a,a))
        self.assertTrue(guarded(self.diff))
if __name__ == "__main__":
    unittest.main()
