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

class ReviewRegressionTests(unittest.TestCase):
 def test_all_claims_remain_uncertified(self):
  from patch08_pp_epoch_attribution import candidates
  out=candidates(rows())
  self.assertEqual(out['native_accepted'],0)
  self.assertIs(out['engine_request_owned_verified'],False)
  self.assertIs(out['legality_verified'],False)
  self.assertIs(out['manual_fallback_verified'],False)
 def test_both_order_edges_and_fight_uniqueness(self):
  from patch08_pp_epoch_attribution import Event,candidates
  baseline=rows()
  self.assertEqual(len(candidates(baseline)['candidates']),1)
  mutations=[
   [Event(10,1,0,'move',3),Event(11,1,0,'fight',0),baseline[2]],
   [Event(10,1,0,'fight',0),Event(11,1,0,'pp',3,20,19,True),Event(19,1,0,'move',3)],
   [Event(10,1,0,'fight',0),Event(11,1,0,'fight',0),Event(12,1,0,'move',3),Event(19,1,0,'pp',3,20,19,True)],
   baseline[:2]+[replace(baseline[2],before=0,after=-1)],
   baseline[:2]+[replace(baseline[2],before=21,after=19)],
  ]
  for index,a in enumerate(mutations):
   with self.subTest(index=index):self.assertEqual(len(candidates(a)['candidates']),0)
 def test_manual_other_and_epoch_barriers(self):
  from patch08_pp_epoch_attribution import Event,candidates
  base=rows()
  for kind in ('manual','other','switch'):
   a=base[:2]+[Event(12,1,0,kind,0),replace(base[2],step=20)]
   with self.subTest(kind=kind):self.assertEqual(len(candidates(a)['candidates']),0)
  a=[base[0],replace(base[1],epoch=2),replace(base[2],epoch=2)]
  self.assertEqual(len(candidates(a)['candidates']),0)

if __name__=='__main__':unittest.main()
