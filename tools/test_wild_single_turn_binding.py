#!/usr/bin/env python3
"""Fail-closed original engine turn/opponent continuity source-LAB regressions.

Tests are SOURCE-ONLY; a monotonic turn counter is NOT an engine-issued
request epoch, and synthetic model passes do NOT establish native ROM gameplay.
"""
from dataclasses import dataclass, replace
from pathlib import Path
import unittest

PATCH=Path(__file__).resolve().parents[1]/'source-first'/'wild-single-lab.patch'

def added(patch):
    if not patch.startswith('--- a/src/battle_controller_player.c\n+++ b/src/battle_controller_player.c\n'):
        return None
    return '\n'.join(l[1:] for l in patch.splitlines()[2:] if l.startswith('+') and not l.startswith('+++'))

def contract_ok(patch):
    s=added(patch)
    if s is None:return False
    expect=(
        'u16 turnCounter;', 'u8 foePartyIndex;', 'enum Type foeTypes[3];',
        'sSourceFirstWildLease.turnCounter = gBattleTurnCounter;',
        'sSourceFirstWildLease.foePartyIndex = gBattlerPartyIndexes[sSourceFirstWildLease.foe];',
        'sSourceFirstWildLease.foeTypes[slot] = gBattleMons[sSourceFirstWildLease.foe].types[slot];',
        'gBattleTurnCounter != sSourceFirstWildLease.turnCounter',
        'gBattlerPartyIndexes[sSourceFirstWildLease.foe] != sSourceFirstWildLease.foePartyIndex',
        'sSourceFirstWildLease.foeTypes[slot] != gBattleMons[sSourceFirstWildLease.foe].types[slot]',
        'move == MOVE_STRUGGLE',
        'CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL)',
        'SourceFirstConsumeWildLease(battler) &&',
        'SourceFirstWildSingleMove(battler, TRUE, &autoReply)',
        'GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT) != sSourceFirstWildLease.foe',
        'if (verifyReply && slot != sSourceFirstWildLease.proposedSlot)',
        'gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE',
        'sSourceFirstWildLease.armed = FALSE;',
    )
    if not all(x in s for x in expect): return False
    if s.count('gBattleTurnCounter != sSourceFirstWildLease.turnCounter') != 2:return False
    if s.count('CheckMoveLimitations(')!=1:return False
    if s.count('move == MOVE_STRUGGLE')!=1:return False
    if not (s.index('sSourceFirstWildLease.turnCounter = gBattleTurnCounter;') < s.index('sSourceFirstWildLease.armed = TRUE;')):return False
    if not (s.index('bool32 armed = sSourceFirstWildLease.armed;') < s.index('sSourceFirstWildLease.armed = FALSE;',s.index('bool32 armed = sSourceFirstWildLease.armed;')) < s.index('if (!armed ||')):return False
    if not (s.index('gBattleTurnCounter != sSourceFirstWildLease.turnCounter',s.index('unusable = verifyReply ?')) > s.index('CheckMoveLimitations(')):return False
    if not (s.index('if (verifyReply && slot != sSourceFirstWildLease.proposedSlot)') < s.index('move == MOVE_STRUGGLE') < s.index('B_ACTION_EXEC_SCRIPT, autoReply')):return False
    if not (s.index('SourceFirstConsumeWildLease(battler) &&') < s.index('SourceFirstWildSingleMove(battler, TRUE, &autoReply)')):return False
    if any(x in s for x in ('B_ACTION_USE_ITEM','B_ACTION_SWITCH','B_ACTION_RUN','gBattleMons[foe].moves','Master Ball','Random(')):return False
    return True

@dataclass(frozen=True)
class State:
    owner:int=0
    foe:int=1
    inBattle:bool=True
    active:bool=True
    terminal:bool=False
    turn:int=4
    party:int=0
    foeParty:int=0
    foeTypes:tuple=(11,0,0)
    moves:tuple=(33,44,0,0)
    pp:tuple=(20,20,0,0)
    legal:tuple=(True,True,False,False)
    limited:int=0
    command:str='CHOOSEMOVE'

class Lease:
    def __init__(self):self.proposal=None
    def arm(self,s):
        self.proposal=None
        if s.owner!=0 or s.foe!=1 or not s.inBattle or not s.active or s.terminal:return False
        for slot,move in enumerate(s.moves):
            if move not in (0,165) and s.pp[slot]>0 and s.legal[slot]:
                self.proposal=(replace(s,command='CHOOSEMOVE',limited=0),slot)
                return True
        return False
    def cancel(self):self.proposal=None
    def choose(self,s):
        p,self.proposal=self.proposal,None
        if p is None:return None
        old,slot=p
        if s.owner!=0 or s.foe!=1 or s.command!='CHOOSEMOVE' or not s.active or not s.inBattle or s.terminal:return None
        if any(getattr(s,x)!=getattr(old,x) for x in ('owner','foe','turn','party','foeParty','foeTypes','moves','pp')):return None
        if (s.limited & (1<<slot)) or s.moves[slot] in (0,165) or not s.legal[slot] or not s.pp[slot]:return None
        return slot,s.foe

class PatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.patch=PATCH.read_text()
    def test_exact_target(self):self.assertTrue(self.patch.startswith('--- a/src/battle_controller_player.c'))
    def test_contract(self):self.assertTrue(contract_ok(self.patch))
    def test_no_second_source_path(self):self.assertEqual(self.patch.count('+++ b/src/'),1)
    def test_no_private_images(self):self.assertNotIn('.gba',added(self.patch));self.assertNotIn('.sav',added(self.patch))
    def test_lab_only(self):self.assertIn('SOURCE-FIRST LAB ONLY',self.patch)
    def corrupt(self,before,after):
        self.assertIn(before,self.patch)
        self.assertFalse(contract_ok(self.patch.replace(before,after,1)),before)
    def test_no_turn_snapshot_regression(self):self.corrupt('sSourceFirstWildLease.turnCounter = gBattleTurnCounter;', 'sSourceFirstWildLease.turnCounter = 0;')
    def test_turn_consume_regression(self):self.corrupt('gBattleTurnCounter != sSourceFirstWildLease.turnCounter', 'FALSE')
    def test_turn_post_limitations_regression(self):
        x=self.patch.rindex('gBattleTurnCounter != sSourceFirstWildLease.turnCounter')
        self.assertFalse(contract_ok(self.patch[:x]+'FALSE'+self.patch[x+len('gBattleTurnCounter != sSourceFirstWildLease.turnCounter'):]))
    def test_foe_party_snapshot_regression(self):self.corrupt('sSourceFirstWildLease.foePartyIndex = gBattlerPartyIndexes[sSourceFirstWildLease.foe];','sSourceFirstWildLease.foePartyIndex = 0;')
    def test_foe_party_check_regression(self):self.corrupt('gBattlerPartyIndexes[sSourceFirstWildLease.foe] != sSourceFirstWildLease.foePartyIndex','FALSE')
    def test_foe_types_snapshot_regression(self):self.corrupt('sSourceFirstWildLease.foeTypes[slot] = gBattleMons[sSourceFirstWildLease.foe].types[slot];','sSourceFirstWildLease.foeTypes[slot] = 0;')
    def test_foe_types_check_regression(self):self.corrupt('sSourceFirstWildLease.foeTypes[slot] != gBattleMons[sSourceFirstWildLease.foe].types[slot]','FALSE')
    def test_struggle_block_regression(self):self.corrupt('move == MOVE_STRUGGLE','move == MOVE_NONE')
    def test_struggle_before_reply(self):self.assertLess(added(self.patch).index('move == MOVE_STRUGGLE'),added(self.patch).index('B_ACTION_EXEC_SCRIPT, autoReply'))
    def test_no_new_auto_paths(self):
        for x in ('B_ACTION_USE_ITEM','B_ACTION_SWITCH','B_ACTION_RUN','Master Ball','Random('): self.assertNotIn(x,added(self.patch))

class ModelTests(unittest.TestCase):
    def setUp(self):self.s=State();self.lease=Lease();self.assertTrue(self.lease.arm(self.s))
    def test_unchanged_turn(self):self.assertEqual(self.lease.choose(self.s),(0,1))
    def test_replay_with_advanced_turn(self):self.assertIsNone(self.lease.choose(replace(self.s,turn=5)))
    def test_older_turn(self):self.assertIsNone(self.lease.choose(replace(self.s,turn=3)))
    def test_changed_foe_party(self):self.assertIsNone(self.lease.choose(replace(self.s,foeParty=1)))
    def test_changed_foe_first_type(self):self.assertIsNone(self.lease.choose(replace(self.s,foeTypes=(12,0,0))))
    def test_changed_foe_second_type(self):self.assertIsNone(self.lease.choose(replace(self.s,foeTypes=(11,2,0))))
    def test_changed_foe_third_type(self):self.assertIsNone(self.lease.choose(replace(self.s,foeTypes=(11,0,18))))
    def test_wrong_battler(self):self.assertIsNone(self.lease.choose(replace(self.s,owner=1)))
    def test_terminal(self):self.assertIsNone(self.lease.choose(replace(self.s,terminal=True)))
    def test_stale_field(self):self.assertIsNone(self.lease.choose(replace(self.s,inBattle=False)))
    def test_request_no_longer_active(self):self.assertIsNone(self.lease.choose(replace(self.s,active=False)))
    def test_intervening_other_controller_request(self):self.lease.cancel();self.assertIsNone(self.lease.choose(self.s))
    def test_not_reusable_after_failure(self):self.lease.choose(replace(self.s,turn=5));self.assertIsNone(self.lease.choose(self.s))
    def test_not_reusable_after_success(self):self.lease.choose(self.s);self.assertIsNone(self.lease.choose(self.s))
    def test_rearm_after_turn(self):self.lease.choose(replace(self.s,turn=5));fresh=replace(self.s,turn=5);self.assertTrue(self.lease.arm(fresh));self.assertEqual(self.lease.choose(fresh),(0,1))
    def test_first_move_is_struggle_second_valid(self):
        x=replace(self.s,moves=(165,44,0,0))
        self.assertTrue(self.lease.arm(x));self.assertEqual(self.lease.choose(x),(1,1))
    def test_only_struggle_never_auto(self):
        x=replace(self.s,moves=(165,0,0,0))
        self.assertFalse(self.lease.arm(x));self.assertIsNone(self.lease.choose(x))
    def test_final_slot_becomes_struggle(self):self.assertIsNone(self.lease.choose(replace(self.s,moves=(165,44,0,0))))
    def test_frozen_slot_becomes_disabled(self):self.assertIsNone(self.lease.choose(replace(self.s,limited=1)))
    def test_unrelated_slot_disabled(self):self.assertEqual(self.lease.choose(replace(self.s,limited=2)),(0,1))
    def test_no_implicit_slot_switch(self):self.assertIsNone(self.lease.choose(replace(self.s,legal=(False,True,False,False))))
    def test_foe_changed(self):self.assertIsNone(self.lease.choose(replace(self.s,foe=2)))
    def test_changed_party(self):self.assertIsNone(self.lease.choose(replace(self.s,party=1)))
    def test_command_replaced(self):self.assertIsNone(self.lease.choose(replace(self.s,command='CHOOSEPOKEMON')))
    def test_changed_move_pp(self):self.assertIsNone(self.lease.choose(replace(self.s,pp=(19,20,0,0))))

if __name__=='__main__':unittest.main()
