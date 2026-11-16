#!/usr/bin/env python3
"""Generated-only negative tests. NEVER loads a private ROM or trace."""
import copy
import unittest
from audit_private_original_cursor_writer import audit, SELECTOR_PC

P=0x0201b76c

def x(n):return '0x%08x'%n

def fixture():
    return [
      dict(event='cursor_store',f=3645,kind='pointer',pc=x(0x080f8438),thumb=1,
           lr=x(0x081b2117),address=x(0x02001e90),width=4,value=P,ptr_before=x(0),
           ptr_after=x(P),slot_before=-1,slot_after=0,target_before=-1,target_after=0,
           regs=[P,0,0,0,0,0,0,0]),
      dict(event='cursor_store',f=4075,kind='slot',pc=x(0x0801862e),thumb=1,
           lr=x(0x08018497),address=x(P+0x106),width=1,value=0,ptr_before=x(P),
           ptr_after=x(P),slot_before=0,slot_after=0,target_before=1,target_after=1,
           regs=[0,0,0,P+0x106,0,0,0,0]),
      dict(event='cursor_store',f=4198,kind='target',pc=x(0x08016fb6),thumb=1,
           lr=x(0x08016fa5),address=x(P+0x10a),width=1,value=1,ptr_before=x(P),
           ptr_after=x(P),slot_before=0,slot_after=0,target_before=0,target_after=1,
           regs=[1,0,0,P+0x10a,0,0,0,0]),
      dict(event='cursor_store',f=4419,kind='pointer',pc=x(0x080f85da),thumb=1,
           lr=x(0x080f85db),address=x(0x02001e90),width=4,value=0,ptr_before=x(P),
           ptr_after=x(0),slot_before=0,slot_after=-1,target_before=1,target_after=-1,
           regs=[0,0,0,0,0,0,0,0]),
      dict(event='cursor_trace_summary',stores=4,pointer_writes=2,slot_writes=1,valid_samples=77),
    ]

class Tests(unittest.TestCase):
    def test_positive_candidate_not_certification(self):
        z=audit(fixture())
        self.assertTrue(z['selector_returns_value_to_slot_writer_candidate'])
        self.assertEqual(z['original_player0_slot_store_candidates'],1)
        self.assertEqual(z['original_native_acceptance_scenarios'],0)
        self.assertFalse(z['manual_fallback_certified'])
        self.assertFalse(z['no_forced_switch_certified'])
        self.assertFalse(z['actual_taunt_failure_root_cause_certified'])
    def test_wrong_writer_pc(self):
        d=fixture();d[1]['pc']=x(0x08018630)
        with self.assertRaises(ValueError):audit(d)
    def test_wrong_source_register(self):
        d=fixture();d[1]['regs'][0]=1
        with self.assertRaises(ValueError):audit(d)
    def test_wrong_target_pointer(self):
        d=fixture();d[2]['address']=x(P+0x10b)
        with self.assertRaises(ValueError):audit(d)
    def test_wrong_slot_or_no_pointer_owner(self):
        for change in [lambda d:d[1].update(ptr_before=x(P+4)),
                       lambda d:d[1]['regs'].__setitem__(4,1),
                       lambda d:d[1].update(slot_after=5)]:
            d=fixture();change(d)
            with self.assertRaises(ValueError):audit(d)
    def test_missing_row_summary_denied(self):
        d=fixture();d.pop(1)
        with self.assertRaises(ValueError):audit(d)
    def test_no_native_claim_without_slot_writer(self):
        d=fixture();d.pop(1);d[-1]['stores']=3;d[-1]['slot_writes']=0
        z=audit(d)
        self.assertFalse(z['selector_returns_value_to_slot_writer_candidate'])
        self.assertEqual(z['original_native_acceptance_scenarios'],0)
    def test_ambiguous_extra_writer_denied(self):
        d=fixture();d.insert(2,copy.deepcopy(d[1]))
        with self.assertRaises(ValueError):audit(d)
    def test_bad_opcode_provenance_never_certified(self):
        z=audit(fixture(),False)
        self.assertFalse(z['exact_rom_static_writer_path_verified'])
        self.assertFalse(z['selector_returns_value_to_slot_writer_candidate'])
    def test_bad_schema_or_stale_step(self):
        for mutate in [lambda d:d[2].update(f=100),
                       lambda d:d[1].update(thumb=True),
                       lambda d:d[1]['regs'].__setitem__(2,True),
                       lambda d:d[1].update(width=4)]:
            d=fixture();mutate(d)
            with self.assertRaises(ValueError):audit(d)
    def test_move_cursor_not_proof_of_dynamic_legality(self):
        z=audit(fixture());self.assertFalse(z['dynamic_move_and_target_legality_certified']);self.assertFalse(z['original_engine_one_use_request_certified'])

if __name__=='__main__':unittest.main()
