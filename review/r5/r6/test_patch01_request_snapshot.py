import unittest
from dataclasses import replace
from patch01_request_snapshot import Snapshot,eligible

def good():return Snapshot(0,19,True,True,False,42,1,2,0x2010000,1,10,b'\x13\0\0\0',bytes(range(12)))
class Tests(unittest.TestCase):
 def test_valid_static(self):self.assertTrue(eligible(good(),good()))
 def test_other_owner(self):self.assertFalse(eligible(replace(good(),battler=1),replace(good(),battler=1)))
 def test_stale_epoch(self):self.assertFalse(eligible(good(),replace(good(),request_epoch=11)))
 def test_full_payload_flip(self):self.assertFalse(eligible(good(),replace(good(),move_menu_payload=bytes(range(11))+b'Z')))
 def test_missing_payload(self):self.assertFalse(eligible(good(),replace(good(),action_header=b'X')))
 def test_consumed(self):self.assertFalse(eligible(good(),replace(good(),consumed=True)))
 def test_types(self):self.assertFalse(eligible(replace(good(),request_epoch=True),replace(good(),request_epoch=True)))
 def test_doubles(self):self.assertFalse(eligible(replace(good(),is_wild_single=False),replace(good(),is_wild_single=False)))
if __name__=='__main__':unittest.main()
