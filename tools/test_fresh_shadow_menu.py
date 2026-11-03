"""Fail-closed synthetic-only tests for R12 fresh-wild host menu chronology."""
import copy
import unittest
from test_fresh_wild_request import fixture as r11_fixture
from verify_fresh_shadow_menu import verify,ROM,SAVE,HOST,MOVES,PP,KINDS,ORIGINAL_PCS

def fixture(mask=3):
 pre,r11=r11_fixture()
 slot=1 if mask==3 else 0
 emit_frame=3408 if slot==1 else 3410
 ev=[]
 for i,(pc,kind) in enumerate(zip(ORIGINAL_PCS,KINDS)):
  row={'kind':kind,'pc':hex(pc),'frame':emit_frame if i<3 else emit_frame+1,
       'pending':1 if i<2 else 0,'actor':0}
  if i==0:row.update(subcmd=10,payload=256+slot)
  if i==1:row.update(direction=1,size=6,valid=True,reply_header=0x0a20,reply_payload=256+slot)
  if i==4:row['native_result']=0
  if i==5:row['slot']=slot
  if i==6:row['move_id']=MOVES[slot]
  ev.append(row)
 d={
  'schema':'sg16266-r12-fresh-wild-host-shadow-v1',
  'scope':'one clean-save naturally triggered wild encounter; original engine installer, copy, pending and original menu with HOST button inputs; scorer runs HOST ONLY',
  'original_rom_sha256':ROM,'original_save_sha256':SAVE,'original_host_sha256':HOST,
  'preconstructor_state_sha256':pre['private_prewild_state_sha256'],
  'original_installer_player_executions':1,'original_installer_foe_executions':1,
  'original_copy_frame':3402,'original_copy_stores':44,'original_copy_source_sha256':r11['copy_source_sha256'],
  'original_pending_set_after_steps':23,'original_pending_set_frame':3402,
  'original_menu_frame':3406,'original_menu_pending_word':3,
  'original_player_move_ids':MOVES.copy(),'original_player_request_moves':MOVES.copy(),'original_player_pp':PP.copy(),
  'original_player_negative_restrictions':dict.fromkeys(['negative_mask','disabled_move','encored_move','encore_timer','repeat_blocked','last_move'],0),
  'historical_manual_test_mask':mask,
  'selected_by':'unchanged original isolated C Smart AI ranker compiled HOST only',
  'ranker_proposal':{'slot':slot,'move_id':MOVES[slot],'target':1,'candidate_count':2 if mask==3 else 1},
  'original_native_events':ev,'native_restriction_result_accepted':True,'host_scripted_original_menu_choices':1,
  'in_rom_auto_submissions':0,'in_rom_auto_acceptance':0,'complete_move_legality':False,
  'complete_target_legality':False,'general_exclusive_player_ownership_certified':False,
  'actor1_AI_modified':False,'auto_items_or_capture':False}
 return pre,r11,d

class FreshShadowSequence(unittest.TestCase):
 def reject(self,mutate):
  x=fixture();mutate(*x)
  with self.assertRaises(ValueError):verify(*x)
 def test_synthetic_accepted_slots(self):
  for mask,slot in [(3,1),(1,0)]:
   with self.subTest(mask=mask):
    x=fixture(mask);r=verify(*x)
    self.assertEqual(r['host_scorer_move_accepted'],slot)
    self.assertEqual(r['native_in_rom_auto_acceptance'],0)
 def test_inputs_unchanged(self):
  x=fixture();saved=copy.deepcopy(x);verify(*x);self.assertEqual(x,saved)
 def test_original_state_and_constructor_denials(self):
  for key,val in [('original_rom_sha256','0'*64),('original_host_sha256','0'*64),('preconstructor_state_sha256','0'*64),('original_installer_foe_executions',0),('original_installer_player_executions',2)]:
   with self.subTest(key=key):self.reject(lambda a,b,r:r.__setitem__(key,val))
  self.reject(lambda a,b,r:a['before_controller'].__setitem__('battle_flags',0x404))
 def test_copy_and_pending_denials(self):
  for key,val in [('original_copy_stores',43),('original_copy_frame',3403),('original_pending_set_after_steps',24),('original_pending_set_frame',3403),('original_copy_source_sha256','0'*64)]:
   with self.subTest(key=key):self.reject(lambda a,b,r:r.__setitem__(key,val))
 def test_move_menu_and_own_data_denials(self):
  for key,val in [('original_menu_frame',3402),('original_menu_frame',3425),('original_menu_pending_word',1),('original_player_move_ids',[325,157,92,0]),('original_player_pp',[20,0,10,20])]:
   with self.subTest(key=key):self.reject(lambda a,b,r:r.__setitem__(key,val))
 def test_historic_test_mask_and_ranker_denials(self):
  for key,val in [('historical_manual_test_mask',7),('selected_by','untrusted alternate ranker')]:
   self.reject(lambda a,b,r:r.__setitem__(key,val))
  for key,val in [('slot',0),('move_id',325),('target',0),('candidate_count',4)]:
   with self.subTest(key=key):self.reject(lambda a,b,r:r['ranker_proposal'].__setitem__(key,val))
 def test_live_negative_restrictions(self):
  for key,val in [('negative_mask',1),('disabled_move',325),('encore_timer',1),('repeat_blocked',1),('last_move',92)]:
   with self.subTest(key=key):self.reject(lambda a,b,r:r['original_player_negative_restrictions'].__setitem__(key,val))
 def test_original_native_order_and_actor_denials(self):
  self.reject(lambda a,b,r:r['original_native_events'].pop())
  self.reject(lambda a,b,r:r['original_native_events'][2].__setitem__('kind','target_commit'))
  self.reject(lambda a,b,r:r['original_native_events'][0].__setitem__('actor',1))
  self.reject(lambda a,b,r:r['original_native_events'][4].__setitem__('pc','0x1234'))
  self.reject(lambda a,b,r:r['original_native_events'][1].__setitem__('pending',0))
 def test_emission_reply_validation_and_commit_denials(self):
  for idx,key,val in [(0,'subcmd',7),(0,'payload',0),(1,'reply_payload',259),(1,'reply_header',0),(1,'valid',False),(2,'pending',1),(4,'native_result',1),(5,'slot',0),(6,'move_id',325)]:
   with self.subTest(idx=idx,key=key):self.reject(lambda a,b,r:r['original_native_events'][idx].__setitem__(key,val))
 def test_reject_action_claims_and_unrequested_hidden_foe(self):
  for key,val in [('in_rom_auto_submissions',1),('in_rom_auto_acceptance',1),('complete_move_legality',True),('complete_target_legality',True),('general_exclusive_player_ownership_certified',True),('actor1_AI_modified',True),('auto_items_or_capture',True)]:
   with self.subTest(key=key):self.reject(lambda a,b,r:r.__setitem__(key,val))
  self.reject(lambda a,b,r:r.__setitem__('opponent_hp',100))
  self.reject(lambda a,b,r:r.__setitem__('extra_authority','no'))

if __name__=='__main__':unittest.main(verbosity=2)