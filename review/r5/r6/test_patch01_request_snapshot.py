import unittest
from dataclasses import replace
from patch01_request_snapshot import Snapshot,eligible

def good():return Snapshot(0,19,True,True,False,42,1,2,0x2010000,1,10,b'\x13\0\0\0',bytes(range(12)))
class Tests(unittest.TestCase):
 def test_valid_static(self):self.assertTrue(eligible(good(),good()))
 def test_other_owner(self):self.assertFalse(eligible(replace(good(),battler=1),replace(good(),battler=1)))
 def test_stale_epoch(self):self.assertFalse(eligible(good(),replace(good(),request_epoch=11)))
 def test_full_payload_flip(self):self.assertFalse(eligible(good(),replace(good(),move_menu_payload=bytes(range(11))+b'Z')))
 def test_missing_payload(self):self.assertFalse(eligible(good(),replace(good(),action_header=b'X')))
 def test_consumed(self):self.assertFalse(eligible(good(),replace(good(),consumed=True)))
 def test_types(self):self.assertFalse(eligible(replace(good(),request_epoch=True),replace(good(),request_epoch=True)))
 def test_doubles(self):self.assertFalse(eligible(replace(good(),is_wild_single=False),replace(good(),is_wild_single=False)))

class ReviewRegressionTests(unittest.TestCase):
 def test_all_snapshot_fields_must_match(self):
  base=good()
  changes={
   'battler':1,'command':17,'is_player_owned':False,'is_wild_single':False,
   'partner_present':True,'turn':43,'owner_party':3,'foe_party':4,
   'resources':0x2011000,'controller_flags':3,'request_epoch':11,
   'action_header':b'\x13\x01\x00\x00','move_menu_payload':bytes(range(11))+b'X','consumed':True,
  }
  for field,val in changes.items():
   with self.subTest(field=field):self.assertFalse(eligible(base,replace(base,**{field:val})))
 def test_all_owner_and_format_guards(self):
  x=good()
  changes=[dict(command=18),dict(is_player_owned=False),dict(is_wild_single=False),
   dict(partner_present=True),dict(resources=0),dict(request_epoch=0),dict(consumed=True),
   dict(action_header=b'X'),dict(move_menu_payload=b'X'),dict(action_header=b'12345'),
   dict(move_menu_payload=bytes(13)),dict(battler=1)]
  for opts in changes:
   z=replace(x,**opts)
   with self.subTest(opts=opts):self.assertFalse(eligible(z,z))
  self.assertFalse(eligible(x,replace(x,consumed=True)))
 def test_certification_is_false(self):
  import patch01_request_snapshot as p
  self.assertIs(p.NATIVE_CERTIFIED,False)
  self.assertIs(p.PRODUCTION_AUTHORIZED,False)

if __name__=='__main__':unittest.main()
