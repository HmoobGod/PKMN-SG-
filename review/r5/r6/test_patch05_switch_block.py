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
if __name__=='__main__':unittest.main()
