"""Synthetic fail-closed tests. They do NOT replay a ROM or certify auto moves."""
import copy
import unittest
from verify_fresh_wild_request import verify,ROM_SHA,SAVE_SHA,HOST_SHA,PRESTATE_SHA

def fixture():
 pre={
  'schema':'sg16266-cold-save-precontroller-v1',
  'original_rom_sha256':ROM_SHA,'original_save_sha256':SAVE_SHA,
  'loadable_host_sha256':HOST_SHA,'private_prewild_state_sha256':PRESTATE_SHA,
  'private_prewild_state_bytes':397312,
  'before_controller':{'frame':3023,'original_guest_pc':'0x806ad46','battle_flags':4,'battlers':2,'kinds':[0,0],
    'player_runner':'0x806a34d','opponent_runner':'0x806a34d'},
  'route':[{'direction':'right','button':16,'end_frame':3023,'reason':2,'pc':'0x806ad46','flags':'0x4','count':2,'kinds':[0,0]}],
  'installed_player_certified_general':False,'native_auto_acceptance':0,'opponent_ai_modified':False}
 run={
  'schema':'sg16266-r11-fresh-wild-installer-copy-v1','original_rom_sha256':ROM_SHA,
  'original_save_sha256':SAVE_SHA,'preconstructor_state_sha256':PRESTATE_SHA,
  'preconstructor_frame':3023,'installer_player_executions':1,'installer_foe_executions':1,
  'trace_windows':[[0,0,1,3023,3113,1,1],[1,0,1,3113,3203,0,0],[2,1,1,3203,3205,0,0],
    [3,0,1,3205,3295,0,0],[4,1,1,3295,3297,0,0],[5,0,1,3297,3387,0,0],
    [6,1,1,3387,3389,0,0],[7,0,2,3389,3402,0,0]],
  'copy_frame':3402,'copy_stores':44,'copy_source_sha256':'1'*64,
  'pending_set_steps':23,'pending_set_frame':3402,
  'player_own_move_ids':[325,157,92,269],'player_request_move_ids':[325,157,92,269],
  'player_own_pp':[20,10,10,20],
  'auto_submissions':0,'automatic_battle_acceptance':0,
  'native_hook_modified':False,'general_owner_authority':False,'complete_legality_certified':False}
 return pre,run

class NativeWildBoundary(unittest.TestCase):
 def test_valid_synthetic(self):
  self.assertEqual(verify(*fixture())['in_rom_auto_acceptance'],0)
 def test_nonmutation(self):
  a,b=fixture();old=copy.deepcopy((a,b));verify(a,b);self.assertEqual((a,b),old)
 def test_reject_other_battle_modes_and_contexts(self):
  mutants=[('battle_flags',0x404),('battle_flags',13),('battle_flags',0x400005),('battlers',4),
    ('kinds',[1,3]),('player_runner','0x80619d5'),('original_guest_pc','0x806b370')]
  for key,value in mutants:
   a,b=fixture();a['before_controller'][key]=value
   with self.subTest(field=key,value=value),self.assertRaises(ValueError):verify(a,b)
 def test_reject_unproven_input_and_event_sources(self):
  for key,value in [('original_rom_sha256','0'*64),('original_save_sha256','0'*64),
    ('private_prewild_state_sha256','0'*64),('loadable_host_sha256','0'*64),('private_prewild_state_bytes',0),
    ('installed_player_certified_general',True),('native_auto_acceptance',1),('opponent_ai_modified',True)]:
   a,b=fixture();a[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):verify(a,b)
 def test_reject_wrong_lifetime_and_copy(self):
  for key,value in [('preconstructor_frame',1),('preconstructor_state_sha256','0'*64),
    ('installer_player_executions',0),('installer_foe_executions',2),('copy_stores',43),
    ('pending_set_steps',0),('pending_set_steps',24),('pending_set_frame',3403),('copy_frame',3401),
    ('copy_source_sha256','bad'),('player_request_move_ids',[325,157,92,0]),('player_own_pp',[-1,10,10,20]),
    ('native_hook_modified',True),('general_owner_authority',True),('complete_legality_certified',True),
    ('auto_submissions',1),('automatic_battle_acceptance',1),('opponent_item',600)]:
   a,b=fixture();b[key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):verify(a,b)
 def test_reject_missing_or_forged_native_order(self):
  for i,idx,value in [(0,5,0),(0,6,0),(0,2,2),(1,3,3024),(4,1,32),(7,2,1),(7,4,3403)]:
   a,b=fixture();b['trace_windows'][i][idx]=value
   with self.subTest(i=i,idx=idx,value=value),self.assertRaises(ValueError):verify(a,b)
 def test_reject_forged_route_and_hidden_foe(self):
  for key,value in [('button',1),('reason',3),('pc','0x806b370'),('flags','0x404'),('count',4),('kinds',[2,3])]:
   a,b=fixture();a['route'][-1][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):verify(a,b)
  a,b=fixture();a['foe_moves']=[1,2,3,4]
  with self.assertRaises(ValueError):verify(a,b)

if __name__=='__main__':unittest.main(verbosity=2)