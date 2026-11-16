import unittest
from dataclasses import replace
from patch08_pp_epoch_attribution import Event,candidates

def rows():return [Event(10,1,0,'fight',0),Event(11,1,0,'move',3),Event(19,1,0,'pp',3,20,19,True)]
class Tests(unittest.TestCase):
 def test_one(self):self.assertEqual(len(candidates(rows())['candidates']),1)
 def test_wrong_slot(self):self.assertEqual(len(candidates(rows()[:2]+[replace(rows()[2],slot=1)])['candidates']),0)
 def test_no_opcode(self):self.assertEqual(len(candidates(rows()[:2]+[replace(rows()[2],proven_opcode=False)])['candidates']),0)
 def test_enemy_pp_not_promoted(self):self.assertEqual(len(candidates(rows()[:2]+[replace(rows()[2],owner=1)])['candidates']),0)
 def test_double_debit(self):self.assertEqual(len(candidates(rows()[:2]+[replace(rows()[2],after=18)])['candidates']),0)
 def test_switch_barrier(self):self.assertEqual(len(candidates(rows()+[Event(20,1,0,'switch',0)])['candidates']),0)
 def test_overlapping_move(self):self.assertEqual(len(candidates(rows()[:2]+[Event(12,1,0,'move',3),rows()[2]])['candidates']),0)
 def test_duplicate_frame(self):
  with self.assertRaises(ValueError):candidates(rows()[:2]+[replace(rows()[2],step=11)])
if __name__=='__main__':unittest.main()
