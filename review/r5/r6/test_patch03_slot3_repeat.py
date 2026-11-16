import unittest
from patch03_slot3_repeat import evaluate

def row(f,slot,epoch=1):return dict(event='slot_cpu_store',frame=f,battle_epoch=epoch,slot=slot,pc='0x0801862e',owner=0)
class Tests(unittest.TestCase):
 def test_one(self):self.assertEqual(evaluate([row(10,3),row(11,3)],True)['authenticated_consecutive_slot3_candidates'],1)
 def test_cross_epoch(self):self.assertEqual(evaluate([row(10,3),row(11,3,2)],True)['authenticated_consecutive_slot3_candidates'],0)
 def test_nonadjacent(self):self.assertEqual(evaluate([row(10,3),row(11,1),row(12,3)],True)['authenticated_consecutive_slot3_candidates'],0)
 def test_no_provenance(self):
  with self.assertRaises(ValueError):evaluate([row(10,3),row(11,3)])
 def test_duplicate_frame(self):
  with self.assertRaises(ValueError):evaluate([row(10,3),row(10,3)],True)
 def test_samples_not_writes(self):
  with self.assertRaises(ValueError):evaluate([{**row(10,3),'event':'sample'}],True)
 def test_wrong_battler(self):
  with self.assertRaises(ValueError):evaluate([{**row(10,3),'owner':1}],True)
if __name__=='__main__':unittest.main()
