import unittest
from dataclasses import replace
from patch02_taunt_evidence import TauntEvidence,classify,Decision

def good():return TauntEvidence(True,True,1,1,269,269,True,True,2,2,True)
class Tests(unittest.TestCase):
 def test_confirmed(self):self.assertEqual(classify(good()),Decision.REDUNDANT)
 def test_not_already_taunted(self):self.assertEqual(classify(replace(good(),target_has_active_taunt=False)),Decision.BENEFICIAL)
 def test_repetition_is_insufficient(self):self.assertEqual(classify(replace(good(),engine_status_checked=False)),Decision.UNKNOWN)
 def test_other_move(self):self.assertEqual(classify(replace(good(),selected_move=100)),Decision.BENEFICIAL)
 def test_target_drift(self):self.assertEqual(classify(replace(good(),live_target=2)),Decision.UNKNOWN)
 def test_epoch_drift(self):self.assertEqual(classify(replace(good(),status_epoch_after=3)),Decision.UNKNOWN)
 def test_wrong_owner(self):self.assertEqual(classify(replace(good(),player0=False)),Decision.UNKNOWN)
 def test_dead(self):self.assertEqual(classify(replace(good(),target_alive=False)),Decision.UNKNOWN)

class ReviewRegressionTests(unittest.TestCase):
 def test_wild_single_must_be_pinned(self):
  from dataclasses import replace
  from patch02_taunt_evidence import TauntEvidence,classify,Decision
  x=TauntEvidence(True,True,1,1,269,269,True,True,10,10,True)
  self.assertEqual(classify(x),Decision.REDUNDANT)
  self.assertEqual(classify(replace(x,wild_single=False)),Decision.UNKNOWN)
  self.assertEqual(classify(replace(x,player0=False)),Decision.UNKNOWN)
  for kw in (dict(status_epoch_before=0),dict(status_epoch_after=11),
             dict(taunt_move_id=0),dict(selected_move=0),dict(engine_status_checked=False),
             dict(target_alive=False),dict(live_target=2),dict(wild_single=1)):
   with self.subTest(kw=kw):self.assertEqual(classify(replace(x,**kw)),Decision.UNKNOWN)
 def test_no_certification(self):
  import patch02_taunt_evidence as p
  self.assertIs(p.NATIVE_CERTIFIED,False)

if __name__=='__main__':unittest.main()
