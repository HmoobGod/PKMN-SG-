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
if __name__=='__main__':unittest.main()
