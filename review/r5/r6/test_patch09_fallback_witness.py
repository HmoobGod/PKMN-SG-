import unittest
from patch09_fallback_witness import inspect

def rows():return [dict(step=i,epoch=1,owner=0,event=e) for i,e in enumerate(('ineligible','defer','original_menu_visible','human_input','manual_response'),1)]
class Tests(unittest.TestCase):
 def test_candidate_not_cert(self):
  x=inspect(rows());self.assertTrue(x['manual_fallback_candidate_UNVERIFIED']);self.assertEqual(x['native_accepted'],0)
 def test_no_menu(self):self.assertFalse(inspect([r for r in rows() if r['event']!='original_menu_visible'])['manual_fallback_candidate_UNVERIFIED'])
 def test_no_human(self):self.assertFalse(inspect([r for r in rows() if r['event']!='human_input'])['manual_fallback_candidate_UNVERIFIED'])
 def test_switch(self):self.assertFalse(inspect(rows()[:2]+[dict(step=3,epoch=1,owner=0,event='switch_response')])['manual_fallback_candidate_UNVERIFIED'])
 def test_auto(self):self.assertFalse(inspect(rows()[:2]+[dict(step=3,epoch=1,owner=0,event='auto_response')])['manual_fallback_candidate_UNVERIFIED'])
 def test_no_epoch_drift(self):
  a=rows();a[-1]['epoch']=2
  with self.assertRaises(ValueError):inspect(a)
 def test_order(self):
  a=rows();a[-1]['step']=1
  with self.assertRaises(ValueError):inspect(a)
if __name__=='__main__':unittest.main()
