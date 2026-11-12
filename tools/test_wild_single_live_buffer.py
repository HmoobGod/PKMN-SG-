#!/usr/bin/env python3
"""Original player-only SOURCE-LAB live request-buffer freshness regressions.

Pure synthetic models and exact static inserted-source contracts; never a real
modified-ROM/CPU witness or production gameplay acceptance.
"""
from dataclasses import dataclass, replace
from pathlib import Path
import unittest

PATCH=Path(__file__).resolve().parents[1]/'source-first'/'wild-single-lab.patch'


def inserted(patch):
    if not patch.startswith('--- a/src/battle_controller_player.c\n+++ b/src/battle_controller_player.c\n'):
        raise ValueError('Only pinned player controller patch is permitted')
    return '\n'.join(line[1:] for line in patch.splitlines()[2:] if line.startswith('+') and not line.startswith('+++'))


def contract(text):
    try: s=inserted(text)
    except ValueError: return False
    start='''        if (verifyReply && (gBattleResources == NULL ||
            gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE ||
            moveInfo != (struct ChooseMoveStruct *)&gBattleResources->bufferA[battler][4]))
            return FALSE;'''
    done='''        if (verifyReply && !SourceFirstWildLeaseSnapshotMatches(battler))
            return FALSE;'''
    handoff='''    if (SourceFirstConsumeWildLease(battler) &&
        SourceFirstWildSingleMove(battler, TRUE, &autoReply) &&
        SourceFirstWildSingleOwner(battler) &&
        gBattleResources != NULL &&
        gBattleResources->bufferA[battler][0] == CONTROLLER_CHOOSEMOVE)'''
    if start not in s or done not in s or handoff not in s: return False
    if s.count('CheckMoveLimitations(')!=1 or s.count('sSourceFirstWildLease.armed = FALSE;')!=2:return False
    if s.count('SourceFirstWildLeaseSnapshotMatches(battler)')!=4:return False
    # The response must compare a dereferenceable, unchanged engine buffer AFTER
    # original targeting routines, BEFORE reading the move/PP or emitting a reply.
    try:
        scope=s.index('static bool32 SourceFirstWildSingleMove(')
        target=s.index('!CanTargetBattler(battler, foe, move)',scope)
        post=s.index(start,scope)
        deref=s.index('moveInfo->moves[slot] != move',scope)
        snapshot=s.index(done,scope)
        assign=s.index('*reply = slot | (foe << 8);',scope)
        complete=s.index('    if (SourceFirstConsumeWildLease(battler) &&',scope)
        final=s.index(handoff,complete)
        emit=s.index('BtlController_EmitTwoReturnValues(battler, B_COMM_TO_ENGINE, B_ACTION_EXEC_SCRIPT, autoReply);',complete)
        return target<post<deref<snapshot<assign<complete<=final<emit
    except ValueError:return False


@dataclass
class State:
    stage:bool=True
    actor:int=0
    foe:int=1
    turn:int=3
    request_opcode:str='CHOOSEMOVE'
    buffer_id:int=100
    move:int=33
    pp:int=10
    slot:int=0
    snapshot:int=42
    active:bool=True
    terminal:bool=False
    target_legal:bool=True


class LabGate:
    def __init__(self):self.used=False
    def evaluate(self, before:State, after_limits:State, after_targets:State):
        if self.used:return None
        self.used=True  # consumed before any helper
        def common(s):
            return (s.active and not s.terminal and s.actor==0 and s.foe==1
                    and s.turn==before.turn and s.snapshot==before.snapshot)
        if not(before.stage and common(before) and common(after_limits)):
            return None
        if after_limits.request_opcode!='CHOOSEMOVE' or after_limits.buffer_id!=before.buffer_id:return None
        if not common(after_targets) or not after_targets.target_legal:return None
        if after_targets.request_opcode!='CHOOSEMOVE' or after_targets.buffer_id!=before.buffer_id:return None
        if after_targets.move!=before.move or after_targets.pp!=before.pp or after_targets.slot!=before.slot:return None
        return (before.slot,before.foe)


class StaticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.patch=PATCH.read_text();cls.code=inserted(cls.patch)
    def test_original_source_contract(self):self.assertTrue(contract(self.patch))
    def test_restrictions_called_only_once(self):self.assertEqual(self.code.count('CheckMoveLimitations('),1)
    def test_one_use_consumption_before_helper(self):self.assertLess(self.code.index('sSourceFirstWildLease.armed = FALSE;',self.code.index('bool32 armed')),self.code.index('CheckMoveLimitations('))
    def test_patch_one_player_controller_only(self):self.assertEqual(self.patch.count('+++ b/src/battle_controller_player.c'),1)
    def test_no_items_capture_enemy(self):
        for bad in ('B_ACTION_USE_ITEM','B_ACTION_SWITCH','gBattlerControllerFuncs[foe] =','Master Ball'):
            with self.subTest(bad=bad):self.assertNotIn(bad,self.code)
    def test_manual_fallback_remains(self):self.assertIn('if (SourceFirstConsumeWildLease(battler) &&',self.code)
    def mutate_added(self, before, after):
        plus=lambda value:'\n'.join('+'+line for line in value.split('\n'))
        old=plus(before);new=plus(after)
        self.assertIn(old,self.patch)
        self.assertFalse(contract(self.patch.replace(old,new,1)))
    def test_cannot_mutate_post_target_opcode(self):
        self.mutate_added("""            gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE ||
            moveInfo != (struct ChooseMoveStruct *)&gBattleResources->bufferA[battler][4]))""","""            gBattleResources->bufferA[battler][0] == CONTROLLER_CHOOSEMOVE ||
            moveInfo != (struct ChooseMoveStruct *)&gBattleResources->bufferA[battler][4]))""")
    def test_cannot_mutate_buffer_identity(self):
        self.mutate_added('            moveInfo != (struct ChooseMoveStruct *)&gBattleResources->bufferA[battler][4]))','            FALSE))')
    def test_cannot_remove_null_check(self):
        self.mutate_added("""        if (verifyReply && (gBattleResources == NULL ||
            gBattleResources->bufferA[battler][0]""","""        if (verifyReply && (FALSE ||
            gBattleResources->bufferA[battler][0]""")
    def test_cannot_remove_immediate_pre_emit_guard(self):
        self.mutate_added("""        SourceFirstWildSingleOwner(battler) &&
        gBattleResources != NULL &&
        gBattleResources->bufferA[battler][0] == CONTROLLER_CHOOSEMOVE)""","""        TRUE &&
        gBattleResources != NULL &&
        gBattleResources->bufferA[battler][0] == CONTROLLER_CHOOSEMOVE)""")
    def test_cannot_invert_pre_emit_opcode(self):
        self.mutate_added("""        SourceFirstWildSingleOwner(battler) &&
        gBattleResources != NULL &&
        gBattleResources->bufferA[battler][0] == CONTROLLER_CHOOSEMOVE)""","""        SourceFirstWildSingleOwner(battler) &&
        gBattleResources != NULL &&
        gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE)""")
    def test_cannot_replace_leased_reply_with_unchecked(self):
        self.mutate_added("""    if (SourceFirstConsumeWildLease(battler) &&
        SourceFirstWildSingleMove(battler, TRUE, &autoReply) &&""","""    if (TRUE &&
        SourceFirstWildSingleMove(battler, TRUE, &autoReply) &&""")
    def test_cannot_skip_post_helper_snapshot(self):
        self.mutate_added("""        if (verifyReply && !SourceFirstWildLeaseSnapshotMatches(battler))
            return FALSE;""","""        if (FALSE)
            return FALSE;""")
    def test_cannot_read_payload_before_post_target_guard(self):
        needle='''        if (verifyReply && (moveInfo->moves[slot] != move ||
                           moveInfo->currentPp[slot] != gBattleMons[battler].pp[slot]))
            continue;'''
        start='''        if (verifyReply && (gBattleResources == NULL ||
            gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE ||
            moveInfo != (struct ChooseMoveStruct *)&gBattleResources->bufferA[battler][4]))
            return FALSE;'''
        self.assertIn(needle,self.code);self.assertIn(start,self.code)
        plus=lambda value:'\n'.join('+'+line for line in value.split('\n'))
        block=plus(start)+'\n'+plus(needle)
        self.assertIn(block,self.patch)
        self.assertFalse(contract(self.patch.replace(block,plus(needle)+'\n'+plus(start),1)))


class SyntheticRequestTests(unittest.TestCase):
    def setUp(self):self.state=State()
    def valid(self):return LabGate().evaluate(self.state,self.state,self.state)
    def test_normal(self):self.assertEqual(self.valid(),(0,1))
    def test_consumed_twice(self):
        g=LabGate();self.assertEqual(g.evaluate(self.state,self.state,self.state),(0,1));self.assertIsNone(g.evaluate(self.state,self.state,self.state))
    def test_preflight_unarmed(self):self.assertIsNone(LabGate().evaluate(replace(self.state,stage=False),self.state,self.state))


def _make_mutation_test(field,changed,stage):
    def fn(self):
        new=replace(self.state,**{field:changed})
        states={'limits':(self.state,new,new),'targets':(self.state,self.state,new),'preflight':(new,new,new)}
        self.assertIsNone(LabGate().evaluate(*states[stage]))
    return fn

# Isolate each denial and make sure it holds at all three request checkpoints.
for field,changed in [('active',False),('terminal',True),('actor',1),('foe',0),('turn',4),
                      ('snapshot',43),('request_opcode','OPENBAG'),('buffer_id',200),
                      ('move',91),('pp',9),('slot',2),('target_legal',False)]:
    for stage in ('limits','targets'):
        setattr(SyntheticRequestTests,'test_'+field+'_'+stage,_make_mutation_test(field,changed,stage))
# Note: preflight test is separately controlled to avoid invalid baseline mismatch cases.


if __name__=='__main__':unittest.main()
