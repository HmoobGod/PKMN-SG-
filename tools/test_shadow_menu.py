"""Public ROM-free adverse test of R10 shadow scorer + host menu trace schema."""
import copy
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from test_native_manual_legality import example as manual_example
from test_live_context import example_bytes_hex
from verify_shadow_menu import verify, SCOPE

ROOT=Path(__file__).resolve().parents[1]
SYNTHETIC_REQUEST_HASH=hashlib.sha256(bytes.fromhex(example_bytes_hex())).hexdigest()


def sample(slot=1):
    r=manual_example(slot)
    r['schema']='sg16266-host-shadow-menu-v1'
    r['scope']=SCOPE
    r.pop('original_user_input')
    r.pop('manual_native_validation_accepted')
    r.pop('automatic_moves')
    r['original_native_validation_accepted']=True
    r['host_scripted_menu_move_choices']=1
    r['in_rom_auto_moves']=0
    r['host_menu_buttons']='LEFT then A' if slot==0 else 'A'
    r['shadow_proposal']={
        'slot':slot,'target':1,'move_id':(1,2)[slot],
        'candidate_count':1 if slot==0 else 2,
        'tested_manual_fixture_mask':1 if slot==0 else 3,
        'selected_by':'original isolated SG public ranker, HOST-ONLY',
        'engine_action_authority':False,'original_game_ai_enabled':False}
    return r


def check(r):
    return verify(r,expected_moves=(1,2,3,4),expected_pp=(5,6,7,8),
                  expected_request_sha256=SYNTHETIC_REQUEST_HASH)

class ShadowMenuVerifier(unittest.TestCase):
    def test_two_valid_synthetic_host_paths(self):
        for slot in (0,1):
            with self.subTest(slot=slot):
                result=check(sample(slot))
                self.assertEqual(result['host_selected_accepted_actions'],1)
                self.assertEqual(result['native_in_rom_auto_actions'],0)
                self.assertEqual(result['native_auto_acceptance'],0)
    def test_fails_claims_of_native_auto_or_full_authority(self):
        for key,bad in [('in_rom_auto_moves',1),('automatic_battle_acceptance',1),
                        ('exclusive_player_ownership_certified',True),
                        ('general_move_legality_certified',True),
                        ('other_encounters_certified',True),
                        ('original_native_emitter_untouched',False),
                        ('original_native_validation_accepted',False),
                        ('host_scripted_menu_move_choices',2)]:
            r=sample();r[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):check(r)
    def test_reject_unsupported_fixture_mask_or_score(self):
        for key,bad in [('tested_manual_fixture_mask',0),('tested_manual_fixture_mask',4),
                        ('tested_manual_fixture_mask',1),('move_id',3),
                        ('candidate_count',1),('slot',0),('target',0),
                        ('selected_by','fake'),('engine_action_authority',True),
                        ('original_game_ai_enabled',True)]:
            r=sample();r['shadow_proposal'][key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):check(r)
    def test_reject_command_reply_consumer_mutations(self):
        for i in range(8):
            for field,bad in [('original_pc','0x1234'),('frame',14500),
                              ('pending_word',1 if i>=2 else 0)]:
                r=sample();r['native_player_events'][i][field]=bad
                with self.subTest(i=i,field=field),self.assertRaises(ValueError):check(r)
            r=sample();r['native_player_events'].pop(i)
            with self.subTest(i=i,kind='missing'),self.assertRaises(ValueError):check(r)
    def test_reject_wrong_native_acceptance_actor_move(self):
        for i,field,bad in [(0,'emit_actor',1),(0,'encoded_choice',256),
            (0,'subcmd',0),(1,'reply_payload',256),(1,'reply_header',0),
            (1,'reply_ewram_valid',False),(2,'completion_actor',1),
            (4,'original_native_result',1),(5,'committed_move_slot',0),
            (6,'committed_move_id',5),(7,'consumer_actor',1)]:
            r=sample();r['native_player_events'][i][field]=bad
            with self.subTest(i=i,field=field),self.assertRaises(ValueError):check(r)
    def test_reject_changed_own_context_and_opponent_secret_fields(self):
        for key,bad in [('player_own_moves',[1,8,3,4]),('player_own_pp',[5,0,7,8]),
                        ('controller_kinds',[3,1]),('flags',13),('player_disabled_move',2),
                        ('player_native_restricted_mask_negative_only',2),
                        ('player_encore_timer',1),('player_repeat_blocked',1),
                        ('foe_hidden_hp',150)]:
            r=sample()
            for stage in ('postcopy_context','pending_context'):
                r['underlying_live_request'][stage][key]=copy.deepcopy(bad)
            with self.subTest(key=key),self.assertRaises(ValueError):check(r)
    def test_report_not_mutated(self):
        r=sample();old=copy.deepcopy(r)
        check(r);self.assertEqual(r,old)

class SourceScorer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.exe=Path(cls.temp.name)/'shadow_ranker'
        cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-pedantic',
             '-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),
             str(ROOT/'tools'/'shadow_ranker.c'),
             *(str(ROOT/'src'/n) for n in ('ranker_workspace.c','sg_action_gate.c',
               'sg_baseline_mode_guard.c','sg_public_types.c')),'-o',str(cls.exe)]
        subprocess.run(cmd,check=True,capture_output=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_scorer(self,mask,slots=None):
        slots=slots or [325,20,60,0,1,157,9,75,100,6,92,10,0,90,1,269,20,0,100,1]
        return subprocess.run([str(self.exe),str(mask),*map(str,slots)],capture_output=True,text=True)
    def test_original_public_ranker_picks_one_of_two(self):
        p=self.run_scorer(3)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(p.stdout.strip(),'SHADOW_ONLY slot=1 target=1 candidates=2; NO ENGINE PERMISSION')
    def test_mask_fallback_stays_within_original_manually_verified_slots(self):
        p=self.run_scorer(1)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(p.stdout.strip(),'SHADOW_ONLY slot=0 target=1 candidates=1; NO ENGINE PERMISSION')
    def test_ranker_denies_empty_bad_masks_or_invalid_metadata(self):
        for mask in ('0','4','-1','3x'):
            p=self.run_scorer(mask)
            with self.subTest(mask=mask):self.assertNotEqual(p.returncode,0)
        for index,bad in [(0,0),(1,0),(2,0),(4,0),(5,0),(6,0),(7,0),(9,0)]:
            slots=[325,20,60,0,1,157,9,75,100,6,92,10,0,90,1,269,20,0,100,1]
            slots[index]=bad
            p=self.run_scorer(3,slots)
            with self.subTest(index=index):self.assertNotEqual(p.returncode,0)

if __name__=='__main__':unittest.main(verbosity=2)