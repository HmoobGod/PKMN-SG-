#!/usr/bin/env python3
"""Conservative post-restriction/target validation of disposable source LAB.

Synthetic source and model checks only; never promotes custom modified ROM.
"""
from dataclasses import dataclass,replace
from pathlib import Path
import unittest

PATCH=Path(__file__).resolve().parents[1]/'source-first'/'wild-single-lab.patch'

def inserted(patch):
    if not patch.startswith('--- a/src/battle_controller_player.c\n+++ b/src/battle_controller_player.c\n'):
        raise ValueError('wrong upstream source target')
    return '\n'.join(x[1:] for x in patch.splitlines()[2:] if x.startswith('+') and not x.startswith('+++'))

def contract(text):
    try:s=inserted(text)
    except ValueError:return False
    name='SourceFirstWildLeaseSnapshotMatches(battler)'
    limit='unusable = verifyReply ? CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL) : 0;'
    target='!CanTargetBattler(battler, foe, move)'
    late='if (verifyReply && !SourceFirstWildLeaseSnapshotMatches(battler))\n            return FALSE;'
    if s.count(name)!=4 or s.count('CheckMoveLimitations(')!=1:return False
    if 'static bool32 SourceFirstWildLeaseSnapshotMatches(enum BattlerId battler)' not in s:return False
    if s.count('sSourceFirstWildLease.armed = FALSE;') != 2:return False
    if limit not in s or late not in s or target not in s:return False
    if 'if (!armed || battler != sSourceFirstWildLease.owner ||\n        !SourceFirstWildLeaseSnapshotMatches(battler))' not in s:return False
    if not(s.index('sSourceFirstWildLease.armed = FALSE;',s.index('bool32 armed'))
           <s.index('if (!armed || battler != sSourceFirstWildLease.owner ||')
           <s.index(limit)
           <s.index('!SourceFirstWildLeaseSnapshotMatches(battler)',s.index(limit))
           <s.index('for (slot = 0; slot < MAX_MON_MOVES; slot++)',s.index(limit))
           <s.index(target)
           <s.index(late)
           <s.index('*reply = slot | (foe << 8);')):return False
    expected=('!SourceFirstWildSingleOwner(battler)',
              'gBattlerPartyIndexes[battler] != sSourceFirstWildLease.partyIndex',
              'gBattleTurnCounter != sSourceFirstWildLease.turnCounter',
              'gBattleMons[battler].volatiles.encoreTimer != sSourceFirstWildLease.encoreTimer',
              'sSourceFirstWildLease.innates[slot] != gBattleMons[battler].innates[slot]',
              'sSourceFirstWildLease.items[slot] != gBattleMons[battler].items[slot]',
              'sSourceFirstWildLease.foeTypes[slot] != gBattleMons[sSourceFirstWildLease.foe].types[slot]',
              'sSourceFirstWildLease.pp[slot] != gBattleMons[battler].pp[slot]',
              'move == MOVE_STRUGGLE',
              'if (verifyReply && slot != sSourceFirstWildLease.proposedSlot)',
              'SourceFirstConsumeWildLease(battler) &&',
              'B_ACTION_USE_MOVE, 0','B_ACTION_EXEC_SCRIPT, autoReply')
    if not all(e in s for e in expected):return False
    if any(e in s for e in ('B_ACTION_USE_ITEM','B_ACTION_SWITCH','B_ACTION_RUN','Master Ball','Random(')):
        return False
    return True

@dataclass(frozen=True)
class Live:
    owner:int=0
    foe:int=1
    party:int=0
    foe_party:int=0
    active:bool=True
    in_battle:bool=True
    outcome:int=0
    wild_single:bool=True
    command:str='CHOOSEMOVE'
    turn:int=11
    species:int=25
    hp:int=85
    status:int=0
    ability:int=7
    innates:tuple=(1,2,3)
    items:tuple=(11,12,13)
    item:int=11
    types:tuple=(12,1,0)
    timers:tuple=(0,0,0,0)
    foe_species:int=5
    foe_hp:int=40
    foe_status:int=0
    foe_ability:int=9
    foe_types:tuple=(11,0,0)
    moves:tuple=(33,45,0,0)
    pp:tuple=(20,8,0,0)
    restricted:int=0
    target_ok:bool=True

class Mock:
    def __init__(self,s):self.snap=s;self.armed=True
    def matches(self,s):
        if not(s.owner==0 and s.foe==1 and s.active and s.in_battle and s.outcome==0 and
               s.wild_single and s.command=='CHOOSEMOVE'):return False
        keys=('owner','foe','party','foe_party','turn','species','hp','status','ability',
              'innates','items','item','types','timers','foe_species','foe_hp',
              'foe_status','foe_ability','foe_types','moves','pp')
        return all(getattr(s,k)==getattr(self.snap,k) for k in keys)
    def reply(self,pre,after_limits,after_target):
        token,self.armed=self.armed,False
        if not token or not self.matches(pre):return None
        # Original CheckMoveLimitations has already run before second check.
        if not self.matches(after_limits):return None
        slot=0
        if after_limits.restricted & (1<<slot) or after_limits.moves[slot] in (0,165) or not after_limits.pp[slot] or not after_limits.target_ok:return None
        if not self.matches(after_target):return None
        return slot,after_target.foe

class StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.patch=PATCH.read_text()
    def test_contract(self):self.assertTrue(contract(self.patch))
    def test_upstream_one_file_only(self):self.assertEqual(self.patch.count('+++ b/src/'),1)
    def test_no_private_payload(self):self.assertNotIn('.gba',inserted(self.patch));self.assertNotIn('.sav',inserted(self.patch))
    def test_no_bag_switch_capture(self):self.assertTrue(contract(self.patch))
    def test_exact_helper_calls(self):self.assertEqual(inserted(self.patch).count('SourceFirstWildLeaseSnapshotMatches(battler)'),4)
    def test_without_post_limitations_denied(self):
        t=self.patch.replace('+        !SourceFirstWildLeaseSnapshotMatches(battler) ||\n+        gBattleResources == NULL ||','+        gBattleResources == NULL ||',1)
        self.assertNotEqual(t,self.patch)
        self.assertFalse(contract(t))
    def test_without_post_target_denied(self):
        t=self.patch.replace('+        if (verifyReply && !SourceFirstWildLeaseSnapshotMatches(battler))\n+            return FALSE;','',1)
        self.assertNotEqual(t,self.patch)
        self.assertFalse(contract(t))
    def test_without_consumption_denied(self):
        self.assertFalse(contract(self.patch.replace('sSourceFirstWildLease.armed = FALSE;','sSourceFirstWildLease.armed = TRUE;',1)))
    def test_without_helper_fails(self):
        self.assertFalse(contract(self.patch.replace('static bool32 SourceFirstWildLeaseSnapshotMatches(enum BattlerId battler)', 'static bool32 Invalid(enum BattlerId battler)',1)))
    def test_without_restriction_denied(self):
        self.assertFalse(contract(self.patch.replace('CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL)','0',1)))
    def test_without_target_denied(self):
        self.assertFalse(contract(self.patch.replace('!CanTargetBattler(battler, foe, move)','FALSE',1)))
    def test_without_pp_snapshot_denied(self):
        self.assertFalse(contract(self.patch.replace('sSourceFirstWildLease.pp[slot] != gBattleMons[battler].pp[slot]','FALSE',1)))
    def test_without_foe_identity_denied(self):
        self.assertFalse(contract(self.patch.replace('sSourceFirstWildLease.foeTypes[slot] != gBattleMons[sSourceFirstWildLease.foe].types[slot]','FALSE',1)))
    def test_without_one_use_denied(self):
        self.assertFalse(contract(self.patch.replace('if (!armed || battler != sSourceFirstWildLease.owner ||','if (battler != sSourceFirstWildLease.owner ||',1)))

class PhaseTests(unittest.TestCase):
    def setUp(self):self.s=Live();self.l=Mock(self.s)
    def test_unchanged(self):self.assertEqual(self.l.reply(self.s,self.s,self.s),(0,1))
    def test_consumed_on_success(self):self.l.reply(self.s,self.s,self.s);self.assertIsNone(self.l.reply(self.s,self.s,self.s))
    def test_consumed_on_failure(self):self.l.reply(self.s,replace(self.s,turn=12),self.s);self.assertIsNone(self.l.reply(self.s,self.s,self.s))
    def test_disabled_original_slot(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,restricted=1),self.s))
    def test_other_slot_restricted(self):self.assertEqual(self.l.reply(self.s,replace(self.s,restricted=2),self.s),(0,1))
    def test_other_actor(self):self.assertIsNone(self.l.reply(replace(self.s,owner=1),self.s,self.s))
    def test_stale_field(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,in_battle=False),self.s))
    def test_terminal_outcome(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,outcome=1),self.s))
    def test_wrong_request(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,command='CHOOSEPOKEMON'),self.s))
    def test_inactive_original_controller(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,active=False),self.s))
    def test_doubles_never_auto(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,wild_single=False),self.s))
    def test_target_becomes_illegal(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,target_ok=False),self.s))
    def test_post_limit_ability_change(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,ability=12),self.s))
    def test_post_limit_innates_change(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,innates=(1,4,3)),self.s))
    def test_post_limit_item_change(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,item=12),self.s))
    def test_post_limit_timer_change(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,timers=(0,1,0,0)),self.s))
    def test_post_limit_pp_change(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,pp=(19,8,0,0)),self.s))
    def test_post_limit_move_change(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,moves=(44,45,0,0)),self.s))
    def test_post_limit_turn_change(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,turn=12),self.s))
    def test_post_limit_foe_party_change(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,foe_party=1),self.s))
    def test_post_limit_foe_ability_change(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,foe_ability=8),self.s))
    def test_post_target_foe_hp_change(self):self.assertIsNone(self.l.reply(self.s,self.s,replace(self.s,foe_hp=30)))
    def test_post_target_foe_type_change(self):self.assertIsNone(self.l.reply(self.s,self.s,replace(self.s,foe_types=(11,2,0))))
    def test_post_target_player_status_change(self):self.assertIsNone(self.l.reply(self.s,self.s,replace(self.s,status=1)))
    def test_post_target_player_hp_change(self):self.assertIsNone(self.l.reply(self.s,self.s,replace(self.s,hp=70)))
    def test_post_target_target_switch(self):self.assertIsNone(self.l.reply(self.s,self.s,replace(self.s,foe=2)))
    def test_post_target_inbattle_clear(self):self.assertIsNone(self.l.reply(self.s,self.s,replace(self.s,in_battle=False)))
    def test_post_target_request_replaced(self):self.assertIsNone(self.l.reply(self.s,self.s,replace(self.s,command='ITEM')))
    def test_post_target_type_change(self):self.assertIsNone(self.l.reply(self.s,self.s,replace(self.s,types=(11,1,0))))
    def test_post_target_species_change(self):self.assertIsNone(self.l.reply(self.s,self.s,replace(self.s,species=26)))
    def test_no_implicit_second_slot(self):self.assertIsNone(self.l.reply(self.s,replace(self.s,restricted=1),replace(self.s,restricted=1)))
    def test_fresh_rearm_after_denial(self):
        self.l.reply(self.s,replace(self.s,turn=12),self.s)
        t=replace(self.s,turn=12)
        self.assertEqual(Mock(t).reply(t,t,t),(0,1))

if __name__=='__main__':unittest.main()
