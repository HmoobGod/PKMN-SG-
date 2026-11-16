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

class ReviewRegressionTests(unittest.TestCase):
 def test_exact_slot3_repeat_not_general_repeat(self):
  from patch03_slot3_repeat import evaluate
  def row(f,slot,epoch=1,pc='0x0801862e',owner=0):return dict(event='slot_cpu_store',frame=f,battle_epoch=epoch,slot=slot,pc=pc,owner=owner)
  r=evaluate([row(4,3),row(5,3)],True)
  self.assertEqual(r['authenticated_consecutive_slot3_candidates'],1)
  self.assertIs(r['taunt_ineffectiveness_verified'],False)
  self.assertEqual(r['native_accepted'],0)
  self.assertIs(r['production_authorized'],False)
  self.assertEqual(evaluate([row(4,2),row(5,2)],True)['authenticated_consecutive_slot3_candidates'],0)
  self.assertEqual(evaluate([row(4,3),row(5,3,epoch=2)],True)['authenticated_consecutive_slot3_candidates'],0)
 def test_every_trace_identity_guard(self):
  from patch03_slot3_repeat import evaluate
  base=dict(event='slot_cpu_store',frame=5,battle_epoch=1,slot=3,pc='0x0801862e',owner=0)
  for changes in (dict(pc='0x08018630'),dict(battle_epoch=0),dict(slot=4),dict(slot=-1),
      dict(owner=1),dict(frame=-1),dict(frame=True),dict(event='cursor_sample_change')):
   with self.subTest(changes=changes):
    with self.assertRaises(ValueError):evaluate([dict(base,**changes)],True)
  for rows in ([dict(base),dict(base,frame=5)],['bad'],[dict(base,frame=1),dict(base,frame=0)]):
   with self.assertRaises(ValueError):evaluate(rows,True)
  with self.assertRaises(ValueError):evaluate([base],False)


class ReviewSchemaBridgeTests(unittest.TestCase):
 def test_r5_cursor_schema_bridge_counts_only_stores(self):
  from patch03_slot3_repeat import from_r5_authenticated_cursor_trace,evaluate
  rows=[{'event':'cursor_store','kind':'slot','pc':'0x0801862e','f':12,'slot_after':3},
        {'event':'cursor_sample_change','f':13,'slot':3},
        {'event':'cursor_store','kind':'slot','pc':'0x0801862e','f':14,'slot_after':3}]
  report={'full_underlying_pointer_and_opcode_audit_passed':True,
          'original_player0_slot_writes':2,'observed_written_slots':[3,3],
          'formal_native_acceptance':0}
  out=from_r5_authenticated_cursor_trace(rows,report,7)
  self.assertEqual(evaluate(out,True)['authenticated_consecutive_slot3_candidates'],1)
  for key,value in [('full_underlying_pointer_and_opcode_audit_passed',False),
                    ('original_player0_slot_writes',3),
                    ('observed_written_slots',[3,1]),('formal_native_acceptance',1)]:
   with self.subTest(key=key):
    with self.assertRaises(ValueError):from_r5_authenticated_cursor_trace(rows,dict(report,**{key:value}),7)
  broken=[dict(rows[0],pc='0x08018630'),rows[1],rows[2]]
  with self.assertRaises(ValueError):from_r5_authenticated_cursor_trace(broken,report,7)

if __name__=='__main__':unittest.main()
