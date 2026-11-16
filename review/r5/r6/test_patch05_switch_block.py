import unittest
from dataclasses import replace
from patch05_switch_block import Proposal,allow

def ok():return Proposal(0,0,17,True,True,True,True)
class Tests(unittest.TestCase):
 def test_fight(self):self.assertTrue(allow(ok()))
 def test_move(self):self.assertTrue(allow(replace(ok(),command=19,action=10)))
 def test_exhaustive_action_space(self):
  self.assertEqual([i for i in range(256) if allow(replace(ok(),action=i))],[0])
 def test_switch(self):self.assertFalse(allow(replace(ok(),action=2)))
 def test_item_capture(self):
  for i in (1,3,4,5,6,7,255):self.assertFalse(allow(replace(ok(),action=i)))
 def test_other_owner(self):self.assertFalse(allow(replace(ok(),battler=1)))
 def test_missing_lease(self):self.assertFalse(allow(replace(ok(),lease_live=False)))
 def test_stale_command(self):self.assertFalse(allow(replace(ok(),action=10)))

class ReviewRegressionTests(unittest.TestCase):
 def test_both_commands_exhaustive_action_space(self):
  from patch05_switch_block import Proposal,allow
  x=Proposal(0,0,17,True,True,True,True)
  for cmd,wanted in ((17,0),(19,10)):
   for action in range(256):
    p=replace(x,command=cmd,action=action)
    self.assertEqual(allow(p),action==wanted,(cmd,action))
 def test_ownership_and_engine_gates(self):
  from patch05_switch_block import Proposal,allow
  x=Proposal(0,10,19,True,True,True,True)
  self.assertTrue(allow(x))
  for field,value in (('engine_request_verified',False),('lease_live',False),('owner_is_player',False),('wild_single',False),('battler',1)):
   with self.subTest(field=field):self.assertFalse(allow(replace(x,**{field:value})))
  self.assertFalse(allow(replace(x,command=18)))
  self.assertFalse(allow(replace(x,engine_request_verified=1)))
 def test_no_certified_switch(self):
  import patch05_switch_block as p
  self.assertIs(p.NATIVE_SWITCH_SAFETY_CERTIFIED,False)

if __name__=='__main__':unittest.main()
