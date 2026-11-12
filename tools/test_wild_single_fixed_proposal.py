#!/usr/bin/env python3
"""Fail-closed frozen action proposal / dynamic move safety tests.

Synthetic model and static source mutation tests. No native custom ROM evidence.
"""
from dataclasses import dataclass
from pathlib import Path
import unittest

PATCH = Path(__file__).resolve().parents[1] / 'source-first' / 'wild-single-lab.patch'


def added_lines(patch):
    if not patch.startswith('--- a/src/battle_controller_player.c\n+++ b/src/battle_controller_player.c\n'):
        raise ValueError('not pinned upstream controller diff')
    return '\n'.join(x[1:] for x in patch.splitlines()[2:] if x.startswith('+') and not x.startswith('+++'))


def static_contract(source):
    s = added_lines(source)
    needed = [
        'u8 proposedSlot;', 'u16 species;', 'u16 hp;', 'u32 status1;',
        'sSourceFirstWildLease.species = gBattleMons[battler].species;',
        'sSourceFirstWildLease.hp = gBattleMons[battler].hp;',
        'sSourceFirstWildLease.status1 = gBattleMons[battler].status1;',
        'gBattlerPartyIndexes[battler] != sSourceFirstWildLease.partyIndex',
        'sSourceFirstWildLease.proposedSlot >= MAX_MON_MOVES',
        'gBattleMons[battler].species != sSourceFirstWildLease.species',
        'gBattleMons[battler].hp != sSourceFirstWildLease.hp',
        'gBattleMons[battler].status1 != sSourceFirstWildLease.status1',
        'if (verifyReply && slot != sSourceFirstWildLease.proposedSlot)',
        'unusable = verifyReply ? CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL) : 0;',
        '*reply = slot | (foe << 8);',
        '*reply = slot; // Record proposal, without a preliminary move-limitations call.',
        'u32 proposedSlot = MAX_MON_MOVES;',
        'SourceFirstWildSingleMove(battler, FALSE, &proposedSlot) && proposedSlot < MAX_MON_MOVES',
        'SourceFirstArmWildLease(battler);',
        'sSourceFirstWildLease.proposedSlot = proposedSlot;',
        'sSourceFirstWildLease.armed = FALSE;',
        'SourceFirstConsumeWildLease(battler) &&',
        'gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE',
        'gBattleOutcome != 0', '!gMain.inBattle',
        'gBattlerControllerFuncs[battler] = HandleChooseMoveAfterDma3;',
    ]
    # The final fallback line above is unmodified upstream code, so search it in
    # the actual patched controller separately, not only in added diff lines.
    needed.remove('gBattlerControllerFuncs[battler] = HandleChooseMoveAfterDma3;')
    if not all(x in s for x in needed): return False
    if s.count('CheckMoveLimitations(') != 1: return False
    # Both the original post-limit guard and the fresh post-target guard must
    # verify the engine's live CHOOSEMOVE opcode; losing either is unsafe.
    if s.count('gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE') < 2: return False
    if not (s.index('if (verifyReply && slot != sSourceFirstWildLease.proposedSlot)')
            < s.index('if ((unusable & (1u << slot))')
            < s.index('*reply = slot | (foe << 8);')): return False
    if not (s.index('SourceFirstArmWildLease(battler);') <
            s.index('sSourceFirstWildLease.proposedSlot = proposedSlot;') <
            s.index('B_ACTION_USE_MOVE, 0')): return False
    if s.count('sSourceFirstWildLease.armed = FALSE;') != 2: return False
    if not (s.index('bool32 armed = sSourceFirstWildLease.armed;') <
            s.index('sSourceFirstWildLease.armed = FALSE;',s.index('bool32 armed = sSourceFirstWildLease.armed;')) <
            s.index('if (!armed ||')): return False
    if any(x in s for x in ('B_ACTION_USE_ITEM','B_ACTION_SWITCH','Master Ball',
                              'gBattlerControllerFuncs[foe] =','Random(')): return False
    return True


@dataclass
class Stage:
    active: bool=False
    actor: int=0
    target: int=1
    party: int=0
    species: int=25
    hp: int=50
    status1: int=0
    proposed: int=4
    moves: tuple=(33,34,0,0)
    pp: tuple=(10,10,0,0)

    def action(self, moves=(33,34,0,0), pp=(10,10,0,0), actor=0, target=1,
               party=0, species=25, hp=50, status1=0, legal_targets=(True,True,False,False),
               active=True, wild=True, request=True, outcome=0, in_battle=True):
        self.active=False
        if not (active and wild and request and outcome==0 and in_battle and actor==0 and target==1):return False
        slot=next((i for i in range(4) if moves[i]!=0 and pp[i]>0 and legal_targets[i]),None)
        if slot is None: return False
        self.__dict__.update(active=True,actor=actor,target=target,party=party,species=species,
                             hp=hp,status1=status1,proposed=slot,moves=tuple(moves),pp=tuple(pp))
        return True

    def command(self,cmd):
        if cmd!='CHOOSEMOVE':self.active=False

    def reply(self, actor=0,target=1,party=0,species=25,hp=50,status1=0,
              moves=(33,34,0,0),pp=(10,10,0,0),restrictions=0,
              legal_targets=(True,True,False,False),active=True,wild=True,
              request=True,outcome=0,in_battle=True):
        was=self.active;self.active=False
        s=self.proposed
        if not (was and actor==self.actor==0 and target==self.target==1
                and party==self.party and species==self.species and hp==self.hp
                and status1==self.status1 and tuple(moves)==self.moves
                and tuple(pp)==self.pp and active and wild and request
                and outcome==0 and in_battle and 0<=s<4):return None
        if restrictions & (1<<s) or moves[s]==0 or pp[s]==0 or not legal_targets[s]:return None
        return (s,target)


class SourceMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch=PATCH.read_text()

    def test_source_contract(self):self.assertTrue(static_contract(self.patch))
    def test_one_file_diff(self):self.assertEqual(self.patch.count('+++ b/src/battle_controller_player.c'),1)
    def test_explicit_source_lab_only(self):self.assertIn('SOURCE-FIRST LAB ONLY',self.patch)
    def test_scope_no_other_source(self):self.assertNotIn('+++ b/src/battle_controller_opponent.c',self.patch)
    def test_no_private_rom_source(self):self.assertNotIn('.gba',added_lines(self.patch));self.assertNotIn('.sav',added_lines(self.patch))
    def check_mutation(self,old,new):
        self.assertIn(old,self.patch)
        self.assertFalse(static_contract(self.patch.replace(old,new,1)))
    def test_party_mutation(self):self.check_mutation('gBattlerPartyIndexes[battler] != sSourceFirstWildLease.partyIndex','FALSE')
    def test_species_mutation(self):self.check_mutation('gBattleMons[battler].species != sSourceFirstWildLease.species','FALSE')
    def test_hp_mutation(self):self.check_mutation('gBattleMons[battler].hp != sSourceFirstWildLease.hp','FALSE')
    def test_status_mutation(self):self.check_mutation('gBattleMons[battler].status1 != sSourceFirstWildLease.status1','FALSE')
    def test_proposal_bound_mutation(self):self.check_mutation('sSourceFirstWildLease.proposedSlot >= MAX_MON_MOVES','FALSE')
    def test_proposal_binding_mutation(self):self.check_mutation('if (verifyReply && slot != sSourceFirstWildLease.proposedSlot)','if (FALSE)')
    def test_action_output_mutation(self):self.check_mutation('*reply = slot; // Record proposal, without a preliminary move-limitations call.','*reply = 0;')
    def test_proposal_assignment_mutation(self):self.check_mutation('sSourceFirstWildLease.proposedSlot = proposedSlot;','sSourceFirstWildLease.proposedSlot = 0;')
    def test_limit_mask_mutation(self):self.check_mutation('CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL)','0')
    def test_liveness_mutation(self):self.check_mutation('!gMain.inBattle','FALSE')
    def test_terminal_mutation(self):self.check_mutation('gBattleOutcome != 0','FALSE')
    def test_opcode_mutation(self):self.check_mutation('gBattleResources->bufferA[battler][0] != CONTROLLER_CHOOSEMOVE','gBattleResources->bufferA[battler][0] == CONTROLLER_CHOOSEMOVE')
    def test_disarming_mutation(self):self.check_mutation('sSourceFirstWildLease.armed = FALSE;','sSourceFirstWildLease.armed = TRUE;')
    def test_manual_path(self):
        p=Path('/mnt/data/sg_fixed_slot_batch/disposable-patched-controller.c')
        if p.exists():self.assertIn('gBattlerControllerFuncs[battler] = HandleChooseMoveAfterDma3;',p.read_text())


class SyntheticProposalTests(unittest.TestCase):
    def setUp(self):self.stage=Stage()
    def test_slot0_normal(self):self.assertTrue(self.stage.action());self.assertEqual(self.stage.reply(),(0,1))
    def test_choose_second_if_first_empty(self):
        self.assertTrue(self.stage.action(moves=(0,34,0,0),pp=(0,10,0,0)))
        self.assertEqual(self.stage.reply(moves=(0,34,0,0),pp=(0,10,0,0)),(1,1))
    def test_choice_forbids_proposed_but_allows_second(self):
        self.stage.action();self.assertIsNone(self.stage.reply(restrictions=1))
    def test_disable_forbids_slot0(self):
        self.stage.action();self.assertIsNone(self.stage.reply(restrictions=1))
    def test_encore_forbids_slot0(self):
        self.stage.action();self.assertIsNone(self.stage.reply(restrictions=1))
    def test_imprison_forbids_slot0(self):
        self.stage.action();self.assertIsNone(self.stage.reply(restrictions=1))
    def test_target_changed(self):self.stage.action();self.assertIsNone(self.stage.reply(target=2))
    def test_target_invalid_now(self):self.stage.action();self.assertIsNone(self.stage.reply(legal_targets=(False,True,False,False)))
    def test_party_changed(self):self.stage.action();self.assertIsNone(self.stage.reply(party=1))
    def test_species_changed(self):self.stage.action();self.assertIsNone(self.stage.reply(species=26))
    def test_hp_changed(self):self.stage.action();self.assertIsNone(self.stage.reply(hp=49))
    def test_poison_appeared(self):self.stage.action();self.assertIsNone(self.stage.reply(status1=8))
    def test_species_change_same_moves(self):self.stage.action();self.assertIsNone(self.stage.reply(species=150))
    def test_hp_changed_to_zero(self):self.stage.action();self.assertIsNone(self.stage.reply(hp=0))
    def test_pp_changed(self):self.stage.action();self.assertIsNone(self.stage.reply(pp=(9,10,0,0)))
    def test_move_changed(self):self.stage.action();self.assertIsNone(self.stage.reply(moves=(34,34,0,0)))
    def test_cancel_on_item(self):self.stage.action();self.stage.command('CHOOSEITEM');self.assertIsNone(self.stage.reply())
    def test_cancel_on_switch(self):self.stage.action();self.stage.command('CHOOSEPOKEMON');self.assertIsNone(self.stage.reply())
    def test_cancel_on_terminal(self):self.stage.action();self.stage.command('END');self.assertIsNone(self.stage.reply())
    def test_choose_move_command_retains_stage(self):self.stage.action();self.stage.command('CHOOSEMOVE');self.assertEqual(self.stage.reply(),(0,1))
    def test_wrong_actor(self):self.stage.action();self.assertIsNone(self.stage.reply(actor=1))
    def test_outcome_changed(self):self.stage.action();self.assertIsNone(self.stage.reply(outcome=1))
    def test_out_of_battle(self):self.stage.action();self.assertIsNone(self.stage.reply(in_battle=False))
    def test_double_battle(self):self.stage.action();self.assertIsNone(self.stage.reply(wild=False))
    def test_inactive_engine(self):self.stage.action();self.assertIsNone(self.stage.reply(active=False))
    def test_wrong_opcode(self):self.stage.action();self.assertIsNone(self.stage.reply(request=False))
    def test_repeat_denied(self):self.stage.action();self.stage.reply();self.assertIsNone(self.stage.reply())
    def test_failure_consumes(self):self.stage.action();self.stage.reply(restrictions=1);self.assertIsNone(self.stage.reply())
    def test_no_usable_moves(self):self.assertFalse(self.stage.action(moves=(0,0,0,0),pp=(0,0,0,0)))
    def test_all_invalid_targets(self):self.assertFalse(self.stage.action(legal_targets=(False,False,False,False)))
    def test_other_actor_cannot_arm(self):self.assertFalse(self.stage.action(actor=1))
    def test_terminal_cannot_arm(self):self.assertFalse(self.stage.action(outcome=1))
    def test_stale_main_cannot_arm(self):self.assertFalse(self.stage.action(in_battle=False))
    def test_cancel_then_rearm(self):self.stage.action();self.stage.command('ITEM');self.assertTrue(self.stage.action());self.assertEqual(self.stage.reply(),(0,1))
    def test_wrong_status_then_fresh_action(self):self.stage.action();self.stage.reply(status1=8);self.assertTrue(self.stage.action(status1=8));self.assertEqual(self.stage.reply(status1=8),(0,1))


if __name__=='__main__':unittest.main()
