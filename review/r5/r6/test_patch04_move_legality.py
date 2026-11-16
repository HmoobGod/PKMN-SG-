import unittest
from dataclasses import replace
from patch04_move_legality import Move,eligible,select

def ok():return Move(10,20,True,True,True,True,True)
class Tests(unittest.TestCase):
 def test_eligible(self):self.assertTrue(eligible(ok()))
 def test_no_pp(self):self.assertFalse(eligible(replace(ok(),pp=0)))
 def test_illegal_move(self):self.assertFalse(eligible(replace(ok(),limitation_mask_pass=False)))
 def test_unknown_target(self):self.assertFalse(eligible(replace(ok(),target_checked=False)))
 def test_wrong_target(self):self.assertFalse(eligible(replace(ok(),target_is_foe=False)))
 def test_unknown_turn(self):self.assertFalse(eligible(replace(ok(),current_turn_checked=False)))
 def test_select_best(self):self.assertEqual(select([ok()]*4,[1,2,3,4]),3)
 def test_no_eligible(self):self.assertIsNone(select([replace(ok(),pp=0)]*4,[1,2,3,4]))
 def test_tie_break(self):self.assertEqual(select([ok()]*4,[4,4,4,4]),0)
if __name__=='__main__':unittest.main()
