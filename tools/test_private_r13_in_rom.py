#!/usr/bin/env python3
"""Public synthetic regression gates for a ROM-resident, fixture-only R13 lab.
These do NOT execute a ROM or certify a real player action; live private replay
receipt hashes and original ROM checks must be verified separately.
"""
import copy
import sys
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_private_r13_in_rom import (verify_positive,verify_negative,BadTrace,LAB_SHA,DENY_SHA,SAVE_SHA,STATES)
from build_private_r13_lab import (emit_private_header,generate,REQUEST_SHA,ROM_SIZE)

STATE_A='4157e7c910d9a55a1f19484c4a2daf6eae9707d52ecff3083b9adff3d08d9085'

def e(pc,frame,**kw):
 r={'pc':pc,'frame':frame,'r0':0,'r1':0,'r2':0,'r3':0,'r4':0,'r5':0,'r6':0,
    'pending':0,'cursor':1,'auto_slot':1,'reply_header':0,'reply_payload':0,'reply_valid':0}
 r.update(kw);return r

def sample_positive():
 # Fake values, never private guest pointers/bytes. The verifier checks
 # structure only and cannot authenticate a fabricated transcript.
 return {'rom_sha256':LAB_SHA,'save_sha256':SAVE_SHA,'state_sha256':STATE_A,
   'copy_complete_44':True,'pending_set_after_steps':23,'status':1,'steps':20000,
   'original_player_installer_count':1,'original_foe_installer_count':1,
   'host_move_menu_buttons_sent':0,'lab_native_in_rom_auto_submission':1,
   'lab_native_in_rom_auto_acceptance':1,'general_owner_certified':False,
   'complete_move_legality':False,'complete_target_legality':False,
   'normal_playable_auto_enabled':False,'automatic_items_or_capture':False,
   'events':[
      e('0x9f20012',4,r0=4),
      e('0x9f2d000',4),
      e('0x9f20022',4,r0=1),
      e('0x9f20032',4),
      e('0x8065eb4',4,r0=0),
      e('0x806bd80',4,r0=0,r2=10,r3=257),
      e('0x806b370',4,r0=0,r1=1,r3=6,reply_header=0x0a20,reply_payload=257,reply_valid=1),
      e('0x806261c',4,r4=0,pending=2),
      e('0x806bd80',4,r0=1,r2=10,r3=3),
      e('0x80e5e5c',5,r0=0,r6=0),
      e('0x8094330',5,r0=0,r6=0),
      e('0x809435c',5,r0=1,r6=0),
      e('0x8094374',5,r0=157,r6=0),
      e('0x8094380',5,r2=1,r6=0),
   ]}

def sample_negative():
 return {'rom_sha256':DENY_SHA,'save_sha256':SAVE_SHA,'state_sha256':STATE_A,
    'copy_complete_44':True,'pending_set_after_steps':23,'status':1,'steps':20000,
    'events':[e('0x9f2d000',4),e('0x9f20022',4,r0=0),
      e('0x806bd80',5,r0=1,r2=10,r3=3),e('0x806449c',6),e('0x806449c',7)]}

class TestPrivateR13(unittest.TestCase):
 def assert_denied_positive(self,mutator):
  j=sample_positive();mutator(j)
  with self.assertRaises(BadTrace):verify_positive(j)
 def test_public_guard_c_syntax_with_mock_private_header(self):
  compiler=shutil.which('cc')
  if not compiler:self.skipTest('C compiler missing')
  root=Path(__file__).resolve().parent.parent
  with tempfile.TemporaryDirectory() as folder:
   h=Path(folder)/'private_r13_request.h'
   h.write_text('static const uint8_t k_request[44]={0};\n')
   subprocess.run([compiler,'-std=c11','-Wall','-Wextra','-Werror',
     '-pedantic','-fsyntax-only','-I',folder,str(root/'research/r13_fixture_gate.c')],
     check=True,capture_output=True,text=True)
 def test_positive_fixture_schema(self):
  self.assertTrue(verify_positive(sample_positive())['accepted'])
 def test_negative_fixture_schema(self):
  self.assertTrue(verify_negative(sample_negative())['manual_fallback'])
 def test_original_base_and_request_pin(self):
  with self.assertRaises(ValueError):emit_private_header(bytes([0])*44)
  with self.assertRaises(ValueError):emit_private_header(bytes([0])*43)
  with self.assertRaises(ValueError):generate(bytes(ROM_SIZE),bytes([1])*80,bytes([2])*400)
 def test_changed_rom_or_save_rejected(self):
  self.assert_denied_positive(lambda j:j.update(rom_sha256='0'*64))
  self.assert_denied_positive(lambda j:j.update(save_sha256='0'*64))
  self.assert_denied_positive(lambda j:j.update(state_sha256='0'*64))
 def test_copy_pending_and_installers(self):
  for k,v in [('copy_complete_44',False),('pending_set_after_steps',22),
      ('original_player_installer_count',0),('original_foe_installer_count',2),
      ('steps',30000000),('status',2)]:
   self.assert_denied_positive(lambda j,k=k,v=v:j.__setitem__(k,v))
 def test_host_buttons_or_exaggerated_claims(self):
  for k,v in [('host_move_menu_buttons_sent',1),('general_owner_certified',True),
      ('complete_move_legality',True),('complete_target_legality',True),
      ('normal_playable_auto_enabled',True),('automatic_items_or_capture',True)]:
   self.assert_denied_positive(lambda j,k=k,v=v:j.__setitem__(k,v))
 def test_player_emission_order_and_exactly_once(self):
  self.assert_denied_positive(lambda j:j['events'].pop(5))
  self.assert_denied_positive(lambda j:j['events'].insert(6,copy.deepcopy(j['events'][5])))
  self.assert_denied_positive(lambda j:j['events'].reverse())
  self.assert_denied_positive(lambda j:j['events'][5].__setitem__('r0',1))
 def test_native_reply_and_completion(self):
  for k,v in [('reply_header',0),('reply_payload',256),('reply_valid',0)]:
   self.assert_denied_positive(lambda j,k=k,v=v:j['events'][6].__setitem__(k,v))
  self.assert_denied_positive(lambda j:j['events'][7].__setitem__('pending',3))
  self.assert_denied_positive(lambda j:j['events'].pop(7))
 def test_native_restriction_and_commit(self):
  self.assert_denied_positive(lambda j:j['events'][10].__setitem__('r0',1))
  self.assert_denied_positive(lambda j:j['events'][11].__setitem__('r0',0))
  self.assert_denied_positive(lambda j:j['events'][12].__setitem__('r0',325))
  self.assert_denied_positive(lambda j:j['events'][13].__setitem__('r2',0))
 def test_manual_contamination(self):
  self.assert_denied_positive(lambda j:j['events'].insert(5,e('0x806449c',4)))
 def test_negative_auto_cannot_be_claimed(self):
  j=sample_negative();j['events'].append(e('0x8065eb4',8,r0=0))
  with self.assertRaises(BadTrace):verify_negative(j)
  j=sample_negative();j['events'].insert(2,e('0x806bd80',5,r0=0,r2=10,r3=257))
  with self.assertRaises(BadTrace):verify_negative(j)
  j=sample_negative();j['events']=[x for x in j['events'] if x['pc']!='0x806449c']
  with self.assertRaises(BadTrace):verify_negative(j)
 def test_gate_condition_denial(self):
  self.assert_denied_positive(lambda j:j['events'][2].__setitem__('r0',0))
  self.assert_denied_positive(lambda j:j['events'][4].__setitem__('r0',2))
  self.assert_denied_positive(lambda j:j['events'][6].__setitem__('auto_slot',0))

if __name__=='__main__':unittest.main(verbosity=2)