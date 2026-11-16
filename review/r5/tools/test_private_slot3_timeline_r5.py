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


class ReviewRegressionTests(Timeline):
 def test_local_guard_mutations_independently(self):
  import copy
  from unittest.mock import patch
  z=self.ordered_fixture();self.set_slot3(z)
  base={'private_cpu_store_rows_schema_and_source_valid':True}
  cases={}
  d=copy.deepcopy(z);d[2]['f']=d[1]['f']-1;cases['nonmonotonic']=d
  d=copy.deepcopy(z);d.insert(1,dict(event='cursor_sample_change',f=3900,ptr='0x00000000',slot=0,target=0));cases['sample_drift']=d
  d=copy.deepcopy(z);d[0]['slot_before']=0;cases['bad_pointer_init']=d
  d=copy.deepcopy(z);d[3]['slot_after']=0;cases['bad_pointer_clear']=d
  d=copy.deepcopy(z);d[0]['ptr_after']='0x00000000';cases['unexpected_pointer_transition']=d
  d=copy.deepcopy(z);d[1]['slot_before']=2;cases['unattributed_slot_drift']=d
  d=copy.deepcopy(z);d.pop(3);cases['unfinished_pointer_lifecycle']=d
  with patch('audit_private_slot3_timeline_r5.audit',return_value=base):
   self.assertEqual(evaluate(z)['slot3_direct_cpu_writes'],1)
   for label,rows in cases.items():
    with self.subTest(label=label):
     with self.assertRaises((ValueError,KeyError,TypeError)):evaluate(rows)
 def test_two_authentic_slot3_writes_counted_and_a_different_choice(self):
  import copy
  from unittest.mock import patch
  z=self.ordered_fixture();self.set_slot3(z)
  second=copy.deepcopy(z[1]);second.update(f=4100,slot_before=3,slot_after=3)
  z.insert(2,second)
  z[-1]['stores']+=1;z[-1]['slot_writes']+=1
  with patch('audit_private_slot3_timeline_r5.audit',return_value={'private_cpu_store_rows_schema_and_source_valid':True}):
   r=evaluate(z)
   self.assertEqual(r['observed_written_slots'],[3,3])
   self.assertEqual(r['consecutive_slot3_cpu_writes'],1)
   self.assertEqual(r['slot3_then_different_slot'],0)
   self.assertFalse(r['taunt_repetition_cause_certified'])
   self.assertEqual(r['formal_native_acceptance'],0)
   # A third distinct selection changes the slot; count remains one.
   third=copy.deepcopy(second);third.update(f=4150,slot_before=3,slot_after=1,value=1)
   third['regs'][0]=1
   z.insert(3,third);z[4]['slot_before']=z[4]['slot_after']=1;z[5]['slot_before']=1
   z[-1]['stores']+=1;z[-1]['slot_writes']+=1
   r=evaluate(z)
   self.assertEqual(r['observed_written_slots'],[3,3,1])
   self.assertEqual(r['consecutive_slot3_cpu_writes'],1)
   self.assertEqual(r['slot3_then_different_slot'],1)
   self.assertFalse(r['taunt_repetition_cause_certified'])

if __name__=='__main__':unittest.main()
