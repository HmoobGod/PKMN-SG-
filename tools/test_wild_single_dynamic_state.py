#!/usr/bin/env python3
"""Synthetic and source-mutation regression checks for the disposable player-only lab.

Not a native modified-ROM replay or proof of actual engine authorization.
"""
from dataclasses import dataclass, field, replace
from pathlib import Path
import unittest

PATCH = Path(__file__).resolve().parents[1]/'source-first'/'wild-single-lab.patch'


def added(patch):
    if not patch.startswith('--- a/src/battle_controller_player.c\n+++ b/src/battle_controller_player.c\n'):
        raise ValueError('wrong source target')
    return '\n'.join(x[1:] for x in patch.splitlines()[2:]
                     if x.startswith('+') and not x.startswith('+++'))


def contract_ok(patch):
    try:
        s = added(patch)
    except ValueError:
        return False
    required = (
        'enum Ability ability;', 'enum Ability innates[MAX_MON_INNATES_INTERNAL];',
        'enum Item items[MAX_MON_ITEMS_INTERNAL];', 'enum Item item;',
        'enum Type types[3];',
        'u32 tauntTimer;', 'u32 disableTimer;', 'u32 encoreTimer;', 'u32 tormentTimer;',
        'u16 foeSpecies;', 'u16 foeHp;', 'u32 foeStatus1;', 'enum Ability foeAbility;',
        'sSourceFirstWildLease.ability = gBattleMons[battler].ability;',
        'sSourceFirstWildLease.item = gBattleMons[battler].item;',
        'sSourceFirstWildLease.tauntTimer = gBattleMons[battler].volatiles.tauntTimer;',
        'sSourceFirstWildLease.disableTimer = gBattleMons[battler].volatiles.disableTimer;',
        'sSourceFirstWildLease.encoreTimer = gBattleMons[battler].volatiles.encoreTimer;',
        'sSourceFirstWildLease.tormentTimer = gBattleMons[battler].volatiles.tormentTimer;',
        'sSourceFirstWildLease.foeSpecies = gBattleMons[sSourceFirstWildLease.foe].species;',
        'sSourceFirstWildLease.foeHp = gBattleMons[sSourceFirstWildLease.foe].hp;',
        'sSourceFirstWildLease.foeStatus1 = gBattleMons[sSourceFirstWildLease.foe].status1;',
        'sSourceFirstWildLease.foeAbility = gBattleMons[sSourceFirstWildLease.foe].ability;',
        'sSourceFirstWildLease.items[slot] = gBattleMons[battler].items[slot];',
        'sSourceFirstWildLease.innates[slot] = gBattleMons[battler].innates[slot];',
        'sSourceFirstWildLease.types[slot] = gBattleMons[battler].types[slot];',
        'gBattleMons[battler].ability != sSourceFirstWildLease.ability',
        'gBattleMons[battler].item != sSourceFirstWildLease.item',
        'gBattleMons[battler].volatiles.tauntTimer != sSourceFirstWildLease.tauntTimer',
        'gBattleMons[battler].volatiles.disableTimer != sSourceFirstWildLease.disableTimer',
        'gBattleMons[battler].volatiles.encoreTimer != sSourceFirstWildLease.encoreTimer',
        'gBattleMons[battler].volatiles.tormentTimer != sSourceFirstWildLease.tormentTimer',
        'gBattleMons[sSourceFirstWildLease.foe].species != sSourceFirstWildLease.foeSpecies',
        'gBattleMons[sSourceFirstWildLease.foe].hp != sSourceFirstWildLease.foeHp',
        'gBattleMons[sSourceFirstWildLease.foe].status1 != sSourceFirstWildLease.foeStatus1',
        'gBattleMons[sSourceFirstWildLease.foe].ability != sSourceFirstWildLease.foeAbility',
        'sSourceFirstWildLease.items[slot] != gBattleMons[battler].items[slot]',
        'sSourceFirstWildLease.innates[slot] != gBattleMons[battler].innates[slot]',
        'sSourceFirstWildLease.types[slot] != gBattleMons[battler].types[slot]',
        'if (verifyReply && (!SourceFirstWildSingleOwner(battler) ||',
        'gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE',
        'unusable = verifyReply ? CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL) : 0;',
        'if (verifyReply && slot != sSourceFirstWildLease.proposedSlot)',
        'sSourceFirstWildLease.armed = FALSE;',
        'SourceFirstInvalidateWildLease();',
        'B_ACTION_USE_MOVE, 0', 'B_ACTION_EXEC_SCRIPT, autoReply',
    )
    if not all(v in s for v in required):
        return False
    if s.count('CheckMoveLimitations(') != 1:
        return False
    if s.index('CheckMoveLimitations(') > s.index('if (verifyReply && (!SourceFirstWildSingleOwner(battler) ||'):
        return False
    if s.index('if (verifyReply && (!SourceFirstWildSingleOwner(battler) ||') > s.index('for (slot = 0; slot < MAX_MON_MOVES; slot++)',s.index('unusable = verifyReply ?')):
        return False
    if s.index('SourceFirstConsumeWildLease(battler) &&') > s.index('SourceFirstWildSingleMove(battler, TRUE, &autoReply)'):
        return False
    if any(k in s for k in ('B_ACTION_USE_ITEM','B_ACTION_SWITCH','B_ACTION_RUN','Master Ball','Random(')):
        return False
    return True

@dataclass(frozen=True)
class State:
    owner: int = 0
    foe: int = 1
    party: int = 0
    species: int = 25
    hp: int = 50
    status1: int = 0
    ability: int = 9
    innates: tuple = (20, 21, 0)
    items: tuple = (44, 0, 0)
    item: int = 44
    types: tuple = (13, 13, 0)
    tauntTimer: int = 0
    disableTimer: int = 0
    encoreTimer: int = 0
    tormentTimer: int = 0
    foeSpecies: int = 16
    foeHp: int = 20
    foeStatus1: int = 0
    foeAbility: int = 2
    moves: tuple = (33, 34, 0, 0)
    pp: tuple = (20, 10, 0, 0)
    inBattle: bool = True
    terminal: bool = False
    activeRequest: bool = True
    requestOpcode: str = 'CHOOSEMOVE'
    legalTargets: tuple = (True, True, False, False)
    restrictions: int = 0

class Lease:
    def __init__(self):
        self.staged = None
        self.slot = None
    def arm(self, data):
        self.staged = None
        if data.owner != 0 or data.foe != 1 or not data.activeRequest or not data.inBattle or data.terminal:
            return False
        for i,move in enumerate(data.moves):
            if move and data.pp[i] and data.legalTargets[i]:
                self.staged = replace(data,requestOpcode='CHOOSEMOVE',restrictions=0)
                self.slot = i
                return True
        return False
    def cancel(self):
        self.staged = None
    def reply(self,data):
        staged,self.staged = self.staged,None
        if staged is None:
            return None
        if data.owner != 0 or data.foe != 1 or data.terminal or not data.inBattle or not data.activeRequest or data.requestOpcode!='CHOOSEMOVE':
            return None
        if any(getattr(data,k)!=getattr(staged,k) for k in (
            'owner','foe','party','species','hp','status1','ability','innates','items','item','types',
            'tauntTimer','disableTimer','encoreTimer','tormentTimer','foeSpecies','foeHp',
            'foeStatus1','foeAbility','moves','pp')):
            return None
        if data.restrictions & (1<<self.slot) or not data.legalTargets[self.slot]:
            return None
        return (self.slot,data.foe)

class PatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.patch=PATCH.read_text()
    def test_valid_source(self):self.assertTrue(contract_ok(self.patch))
    def test_only_pinned_file(self):self.assertEqual(self.patch.count('+++ b/src/battle_controller_player.c'),1)
    def test_no_proprietary_bytes(self):self.assertNotIn('.gba',added(self.patch));self.assertNotIn('.sav',added(self.patch))
    def test_only_source_lab(self):self.assertIn('SOURCE-FIRST LAB ONLY',self.patch)
    def test_no_enemy_controller_modification(self):self.assertNotIn('+++ b/src/battle_controller_opponent.c',self.patch)
    def test_avoid_side_effecting_preflight(self):self.assertEqual(added(self.patch).count('CheckMoveLimitations('),1)
    def test_recheck_after_engine_limitations(self):
        a=added(self.patch); self.assertLess(a.index('unusable = verifyReply ? CheckMoveLimitations('),a.index('if (verifyReply && (!SourceFirstWildSingleOwner(battler) ||'))
    def test_pending_lease_consumed_before_move(self):
        a=added(self.patch); self.assertLess(a.index('SourceFirstConsumeWildLease(battler) &&'),a.index('SourceFirstWildSingleMove(battler, TRUE, &autoReply)'))
    def test_no_item_capture_switch(self):
        for word in ('B_ACTION_USE_ITEM','B_ACTION_SWITCH','Master Ball'):
            self.assertNotIn(word,added(self.patch))

    def mutation(self,from_,to):
        self.assertIn(from_,self.patch)
        self.assertFalse(contract_ok(self.patch.replace(from_,to,1)),from_)

    def test_recheck_ownership_mutation(self):self.mutation('if (verifyReply && (!SourceFirstWildSingleOwner(battler) ||','if (FALSE && (!SourceFirstWildSingleOwner(battler) ||')
    def test_limit_mask_mutation(self):self.mutation('MOVE_LIMITATIONS_ALL','0')
    def test_frozen_slot_mutation(self):self.mutation('if (verifyReply && slot != sSourceFirstWildLease.proposedSlot)','if (FALSE)')
    def test_innates_mutation(self):self.mutation('sSourceFirstWildLease.innates[slot] != gBattleMons[battler].innates[slot]','FALSE')
    def test_held_items_mutation(self):self.mutation('sSourceFirstWildLease.items[slot] != gBattleMons[battler].items[slot]','FALSE')
    def test_types_mutation(self):self.mutation('sSourceFirstWildLease.types[slot] != gBattleMons[battler].types[slot]','FALSE')
    def test_foe_identity_mutation(self):self.mutation('gBattleMons[sSourceFirstWildLease.foe].species != sSourceFirstWildLease.foeSpecies','FALSE')
    def test_taunt_mutation(self):self.mutation('gBattleMons[battler].volatiles.tauntTimer != sSourceFirstWildLease.tauntTimer','FALSE')
    def test_encore_mutation(self):self.mutation('gBattleMons[battler].volatiles.encoreTimer != sSourceFirstWildLease.encoreTimer','FALSE')
    def test_disable_mutation(self):self.mutation('gBattleMons[battler].volatiles.disableTimer != sSourceFirstWildLease.disableTimer','FALSE')
    def test_torment_mutation(self):self.mutation('gBattleMons[battler].volatiles.tormentTimer != sSourceFirstWildLease.tormentTimer','FALSE')
    def test_ability_mutation(self):self.mutation('gBattleMons[battler].ability != sSourceFirstWildLease.ability','FALSE')
    def test_foe_hp_mutation(self):self.mutation('gBattleMons[sSourceFirstWildLease.foe].hp != sSourceFirstWildLease.foeHp','FALSE')

class SyntheticRequestTests(unittest.TestCase):
    def setUp(self):self.state=State();self.lease=Lease();self.assertTrue(self.lease.arm(self.state))
    def test_normal_reply(self):self.assertEqual(self.lease.reply(self.state),(0,1))
    def test_repeat_reply_denied(self):self.lease.reply(self.state);self.assertIsNone(self.lease.reply(self.state))
    def test_no_lease(self):self.lease.cancel();self.assertIsNone(self.lease.reply(self.state))
    def test_rearm_after_cancel(self):self.lease.cancel();self.assertTrue(self.lease.arm(self.state));self.assertEqual(self.lease.reply(self.state),(0,1))
    def test_choose_move_no_retarget(self):self.assertIsNone(self.lease.reply(replace(self.state,foe=2)))
    def test_wrong_owner(self):self.assertIsNone(self.lease.reply(replace(self.state,owner=1)))
    def test_no_active_request(self):self.assertIsNone(self.lease.reply(replace(self.state,activeRequest=False)))
    def test_stale_main(self):self.assertIsNone(self.lease.reply(replace(self.state,inBattle=False)))
    def test_terminal(self):self.assertIsNone(self.lease.reply(replace(self.state,terminal=True)))
    def test_other_command(self):self.assertIsNone(self.lease.reply(replace(self.state,requestOpcode='CHOOSEITEM')))
    def test_restriction_slot0(self):self.assertIsNone(self.lease.reply(replace(self.state,restrictions=1)))
    def test_restriction_slot1_only(self):self.assertEqual(self.lease.reply(replace(self.state,restrictions=2)),(0,1))
    def test_no_target(self):self.assertIsNone(self.lease.reply(replace(self.state,legalTargets=(False,True,False,False))))
    def test_pp_change(self):self.assertIsNone(self.lease.reply(replace(self.state,pp=(19,10,0,0))))
    def test_move_change(self):self.assertIsNone(self.lease.reply(replace(self.state,moves=(34,34,0,0))))
    def test_party_change(self):self.assertIsNone(self.lease.reply(replace(self.state,party=1)))
    def test_hp_change(self):self.assertIsNone(self.lease.reply(replace(self.state,hp=49)))
    def test_status1_change(self):self.assertIsNone(self.lease.reply(replace(self.state,status1=2)))
    def test_species_change(self):self.assertIsNone(self.lease.reply(replace(self.state,species=26)))
    def test_ability_change(self):self.assertIsNone(self.lease.reply(replace(self.state,ability=8)))
    def test_passive_ability_change(self):self.assertIsNone(self.lease.reply(replace(self.state,innates=(21,20,0))))
    def test_held_item_change(self):self.assertIsNone(self.lease.reply(replace(self.state,items=(0,44,0))))
    def test_legacy_item_change(self):self.assertIsNone(self.lease.reply(replace(self.state,item=0)))
    def test_type_change(self):self.assertIsNone(self.lease.reply(replace(self.state,types=(13,0,0))))
    def test_taunt_timer_change(self):self.assertIsNone(self.lease.reply(replace(self.state,tauntTimer=1)))
    def test_disable_timer_change(self):self.assertIsNone(self.lease.reply(replace(self.state,disableTimer=1)))
    def test_encore_timer_change(self):self.assertIsNone(self.lease.reply(replace(self.state,encoreTimer=1)))
    def test_torment_timer_change(self):self.assertIsNone(self.lease.reply(replace(self.state,tormentTimer=1)))
    def test_foe_species_change(self):self.assertIsNone(self.lease.reply(replace(self.state,foeSpecies=25)))
    def test_foe_hp_change(self):self.assertIsNone(self.lease.reply(replace(self.state,foeHp=19)))
    def test_foe_status_change(self):self.assertIsNone(self.lease.reply(replace(self.state,foeStatus1=2)))
    def test_foe_ability_change(self):self.assertIsNone(self.lease.reply(replace(self.state,foeAbility=5)))
    def test_after_failure_cannot_repeat(self):self.lease.reply(replace(self.state,tauntTimer=1));self.assertIsNone(self.lease.reply(self.state))
    def test_after_failed_slot_fallback_denied(self):self.lease.reply(replace(self.state,restrictions=1));self.assertIsNone(self.lease.reply(replace(self.state,restrictions=2)))
    def test_failed_action_under_terminal(self):self.lease.cancel();self.assertFalse(self.lease.arm(replace(self.state,terminal=True)))
    def test_failed_action_unauthorized_actor(self):self.lease.cancel();self.assertFalse(self.lease.arm(replace(self.state,owner=1)))
    def test_failed_action_inactive_request(self):self.lease.cancel();self.assertFalse(self.lease.arm(replace(self.state,activeRequest=False)))
    def test_no_moves(self):self.lease.cancel();self.assertFalse(self.lease.arm(replace(self.state,moves=(0,0,0,0))))
    def test_zero_pp(self):self.lease.cancel();self.assertFalse(self.lease.arm(replace(self.state,pp=(0,0,0,0))))
    def test_no_eligible_targets(self):self.lease.cancel();self.assertFalse(self.lease.arm(replace(self.state,legalTargets=(False,False,False,False))))
    def test_second_slot_frozen(self):
        self.lease.cancel();fresh=replace(self.state,moves=(0,34,0,0),pp=(0,10,0,0))
        self.assertTrue(self.lease.arm(fresh));self.assertEqual(self.lease.reply(fresh),(1,1))
    def test_second_slot_later_disabled_no_retarget(self):
        self.lease.cancel();fresh=replace(self.state,moves=(0,34,33,0),pp=(0,10,10,0),legalTargets=(False,True,True,False))
        self.assertTrue(self.lease.arm(fresh));self.assertIsNone(self.lease.reply(replace(fresh,restrictions=2)))
    def test_rearm_after_state_change(self):
        self.lease.reply(replace(self.state,ability=7));fresh=replace(self.state,ability=7)
        self.assertTrue(self.lease.arm(fresh));self.assertEqual(self.lease.reply(fresh),(0,1))

if __name__=='__main__':unittest.main()
