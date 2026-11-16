import unittest
from patch06_manual_handoff import Handoff,State,advance
class Tests(unittest.TestCase):
 def test_full_handshake_uncertified(self):
  h=Handoff()
  for e in ('ineligible','original_manual_requested','original_menu_visible_and_controllable','physical_human_input_confirmed','original_engine_completed'):h=advance(h,e,6)
  self.assertEqual(h.state,State.CLOSED);self.assertFalse(h.native_accepted)
 def test_no_menu_no_success(self):
  h=advance(advance(Handoff(),'ineligible',6),'original_manual_requested',6)
  self.assertEqual(h.state,State.WAIT)
 def test_wrong_event(self):self.assertEqual(advance(Handoff(),'original_menu_visible_and_controllable',6).state,State.ERROR)
 def test_no_human(self):
  h=Handoff()
  for e in ('ineligible','original_manual_requested','original_menu_visible_and_controllable','original_engine_completed'):h=advance(h,e,6)
  self.assertEqual(h.state,State.ERROR)
 def test_stale_epoch(self):self.assertEqual(advance(advance(Handoff(),'ineligible',6),'original_manual_requested',7).state,State.ERROR)
 def test_wrong_owner(self):self.assertEqual(advance(Handoff(),'ineligible',6,1).state,State.ERROR)
if __name__=='__main__':unittest.main()
