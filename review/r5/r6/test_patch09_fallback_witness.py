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

class ReviewRegressionTests(unittest.TestCase):
 def test_exact_sequence_only_and_no_certification(self):
  from patch09_fallback_witness import inspect
  base=rows();z=inspect(base)
  self.assertTrue(z['manual_fallback_candidate_UNVERIFIED'])
  self.assertIs(z['manual_fallback_certified'],False)
  self.assertEqual(z['native_accepted'],0)
  for event_order in (
   ('ineligible','defer','original_menu_visible','human_input'),
   ('ineligible','defer','original_menu_visible','human_input','manual_response','human_input'),
   ('defer','ineligible','original_menu_visible','human_input','manual_response'),
   ('ineligible','original_menu_visible','defer','human_input','manual_response'),
  ):
   test=[dict(step=i,epoch=1,owner=0,event=e) for i,e in enumerate(event_order,1)]
   self.assertFalse(inspect(test)['manual_fallback_candidate_UNVERIFIED'])
 def test_auto_switch_enemy_and_owner_policy(self):
  from patch09_fallback_witness import inspect
  for kind in ('auto_response','switch_response'):
   a=rows();a.insert(2,dict(step=3,epoch=1,owner=0,event=kind))
   for j,r in enumerate(a):r['step']=j+1
   self.assertFalse(inspect(a)['manual_fallback_candidate_UNVERIFIED'])
  bad=rows();bad[2]['owner']=1
  with self.assertRaises(ValueError):inspect(bad)
  bad=rows();bad.insert(2,dict(step=3,epoch=1,owner=0,event='enemy_event'))
  for j,r in enumerate(bad):r['step']=j+1
  self.assertTrue(inspect(bad)['manual_fallback_candidate_UNVERIFIED'])

if __name__=='__main__':unittest.main()
