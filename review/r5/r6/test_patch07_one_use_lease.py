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

class ReviewRegressionTests(unittest.TestCase):
 def test_all_lease_identity_preconditions(self):
  from patch07_one_use_lease import Lease,consume
  for name,overrides in (('owner',dict(owner=1)),('command',dict(command=18)),('resources',dict(resource_identity=0)),
   ('epoch',dict(epoch=0)),('wrong_epoch',dict(epoch=2)),('wrong_turn',dict(turn=6)),
   ('wrong_resources',dict(resource_identity=6))):
   l=Lease(1,5,0,19,7)
   args=dict(epoch=1,turn=5,owner=0,command=19,resource_identity=7)
   args.update(overrides)
   with self.subTest(name=name):self.assertFalse(consume(l,**args));self.assertFalse(l.consumed)
  # Independently pin constraints when the lease itself agrees with the
  # invalid request. A mismatched lease would mask a deleted owner guard.
  for lease,request in ((Lease(1,5,1,19,7),(1,5,1,19,7)),
                        (Lease(1,5,0,18,7),(1,5,0,18,7)),
                        (Lease(1,5,0,19,0),(1,5,0,19,0)),
                        (Lease(0,5,0,19,7),(0,5,0,19,7))):
   self.assertFalse(consume(lease,*request))
   self.assertFalse(lease.consumed)
  for fields in (dict(owner=1),dict(requested_command=18),dict(resource_identity=0)):
   l=Lease(1,5,0,19,7)
   for k,v in fields.items():setattr(l,k,v)
   self.assertFalse(consume(l,1,5,0,19,7))
 def test_replay_consumes_once_and_no_production(self):
  from patch07_one_use_lease import Lease,consume,PRODUCTION_AUTHORIZED
  l=Lease(1,5,0,19,7)
  self.assertTrue(consume(l,1,5,0,19,7))
  self.assertFalse(consume(l,1,5,0,19,7))
  self.assertIs(PRODUCTION_AUTHORIZED,False)

if __name__=='__main__':unittest.main()
