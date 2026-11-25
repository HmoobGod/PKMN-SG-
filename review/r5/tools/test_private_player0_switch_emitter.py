#!/usr/bin/env python3
"""Generated-only safety counters, no private game required."""
import unittest
from audit_private_player0_switch_emitter import evaluate,EMITTER_STORE,ACTION_CALLER,SWITCH_CALLER

def row(battler=0,value=0,lr=ACTION_CALLER):
    return {'pc':EMITTER_STORE,'r':[battler,1,value,0,0,0,0,0],
            'lr':lr,'width':1,'value':value,'f':4000}

class Tests(unittest.TestCase):
    def test_no_switch_does_not_certify_safety(self):
        z=evaluate([row()])
        self.assertTrue(z['no_player0_action2_observed_in_this_bounded_trace'])
        self.assertFalse(z['no_forced_switch_execution_or_reachability_certified'])
        self.assertEqual(z['native_acceptance_scenarios'],0)
    def test_switch_path_detected(self):
        z=evaluate([row(),row(value=2,lr=SWITCH_CALLER)])
        self.assertFalse(z['no_player0_action2_observed_in_this_bounded_trace'])
        self.assertEqual(z['player0_switch_action2_emitter_rows'],1)
    def test_enemy_not_misattributed(self):
        z=evaluate([row(),row(battler=1,value=2,lr=SWITCH_CALLER)])
        self.assertEqual(z['player0_switch_action2_emitter_rows'],0)
    def test_unknown_source_denied(self):
        z=evaluate([row(),row(value=2,lr=ACTION_CALLER)])
        self.assertFalse(z['no_player0_action2_observed_in_this_bounded_trace'])
    def test_no_evidence_is_not_safe(self):
        self.assertFalse(evaluate([])['no_player0_action2_observed_in_this_bounded_trace'])
    def test_bool_and_bad_regs_fail_closed(self):
        for change in [lambda x:x.update(width=True),lambda x:x['r'].__setitem__(0,True),lambda x:x.update(value=None)]:
            x=row();change(x)
            with self.assertRaises(ValueError):evaluate([x])

if __name__=='__main__':unittest.main()
