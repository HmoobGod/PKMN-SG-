import unittest
from patch07_one_use_lease import Lease,consume

def lease():return Lease(10,21,0,19,0x02010000)
class Tests(unittest.TestCase):
 def test_once(self):
  a=lease();self.assertTrue(consume(a,10,21,0,19,0x02010000));self.assertFalse(consume(a,10,21,0,19,0x02010000))
 def test_stale_epoch(self):self.assertFalse(consume(lease(),11,21,0,19,0x02010000))
 def test_stale_turn(self):self.assertFalse(consume(lease(),10,22,0,19,0x02010000))
 def test_wrong_owner(self):self.assertFalse(consume(lease(),10,21,1,19,0x02010000))
 def test_command_drift(self):self.assertFalse(consume(lease(),10,21,0,17,0x02010000))
 def test_resource_drift(self):self.assertFalse(consume(lease(),10,21,0,19,0x02010004))
 def test_zero_epoch(self):self.assertFalse(consume(Lease(0,21,0,19,1),0,21,0,19,1))
if __name__=='__main__':unittest.main()
