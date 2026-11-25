#!/usr/bin/env python3
"""Generated fake trace fixture tests only; never reads private ROM or logs."""
import unittest
from test_private_original_cursor_writer import fixture
from audit_private_slot3_timeline_r5 import evaluate

class Timeline(unittest.TestCase):
 def ordered_fixture(self):
  z=fixture()
  # Coherent pointer initialization, same-battle slot then target, clear.
  z[1]['target_before']=z[1]['target_after']=0
  z[3]['target_before']=1
  return z
 def set_slot3(self,z):
  w=next(r for r in z if r.get('kind')=='slot')
  w['value']=3;w['regs'][0]=3;w['slot_after']=3
  for r in z:
   if r.get('kind')=='target':r['slot_before']=r['slot_after']=3
   if r.get('pc')=='0x080f85da':r['slot_before']=3

 def test_slot3_real_writer_shape(self):
  z=self.ordered_fixture()
  self.set_slot3(z)
  out=evaluate(z)
  self.assertEqual(out['slot3_direct_cpu_writes'],1)
  self.assertEqual(out['consecutive_slot3_cpu_writes'],0)
  self.assertEqual(out['formal_native_acceptance'],0)
  self.assertFalse(out['taunt_repetition_cause_certified'])
 def test_fake_slot3_not_from_cpu_writer_denied(self):
  z=self.ordered_fixture()
  self.set_slot3(z)
  w=next(r for r in z if r.get('kind')=='slot');w['regs'][0]=0
  with self.assertRaises(ValueError):evaluate(z)
 def test_slot3_wrong_writer_pc_denied(self):
  z=self.ordered_fixture();w=next(r for r in z if r.get('kind')=='slot');w['pc']='0x08018630'
  with self.assertRaises(ValueError):evaluate(z)
 def test_missing_pointer_denied(self):
  z=self.ordered_fixture();z=[r for r in z if r.get('kind')!='pointer']
  with self.assertRaises(ValueError):evaluate(z)
 def test_intervening_unsourced_cursor_change_denied(self):
  z=self.ordered_fixture()
  z[2]['slot_before']=2;z[2]['slot_after']=2
  with self.assertRaises(ValueError):evaluate(z)
 def test_missing_summary_denied(self):
  z=self.ordered_fixture()[:-1]
  with self.assertRaises(ValueError):evaluate(z)
if __name__=='__main__':unittest.main()
