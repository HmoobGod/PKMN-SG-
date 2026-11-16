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

class ReviewRegressionTests(unittest.TestCase):
 def test_engine_authoritative_legality_flags(self):
  from patch04_move_legality import Move,eligible,select
  x=Move(10,20,True,True,True,True,True)
  self.assertTrue(eligible(x))
  for field in ('limitation_checked','limitation_mask_pass','target_checked','target_is_foe','current_turn_checked'):
   with self.subTest(field=field):self.assertFalse(eligible(replace(x,**{field:False})))
 def test_move_pp_bounds_and_types(self):
  from patch04_move_legality import Move,eligible,select
  x=Move(10,20,True,True,True,True,True)
  for field,value in [('move_id',0),('move_id',65535),('move_id',True),('move_id',-1),('pp',0),('pp',100),('pp',True)]:
   with self.subTest(field=field,value=value):self.assertFalse(eligible(replace(x,**{field:value})))
  for key,value in [('moves',[x]),('priorities',[1]),('priorities',[1,2,3,256]),('priorities',[1,2,3,-1]),('priorities',[1,2,3,True])]:
   kwargs=dict(moves=[x]*4,priorities=[1]*4);kwargs[key]=value
   with self.subTest(key=key,value=value):self.assertIsNone(select(**kwargs))
 def test_native_certification_false(self):
  import patch04_move_legality as p
  self.assertIs(p.NATIVE_CERTIFIED,False)

if __name__=='__main__':unittest.main()
