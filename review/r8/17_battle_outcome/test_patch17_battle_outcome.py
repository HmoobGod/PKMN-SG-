"""Synthetic/hostile input tests only; never read a ROM or save."""
import unittest
from copy import deepcopy
from patch17_battle_outcome import evaluate

BASE={'steps': {'battle_start': 100, 'last_auto': 120, 'outcome': 130, 'overworld': 150}, 'original_battle_outcome_verified': True, 'original_overworld_return_verified': True, 'auto_after_outcome': 0, 'forced_switch_count': 0, 'owner': 0}

class ContractTests(unittest.TestCase):
    def test_valid_unverified_candidate(self):
        got=evaluate(deepcopy(BASE))
        self.assertIs(got['candidate_UNVERIFIED'],True)
        self.assertEqual(got['native_accepted'],0)
        for flag in ('manual_fallback_certified','no_forced_switch_certified','production_authorized'):
            self.assertIs(got[flag],False)

    def test_non_mapping_fails_closed(self):
        for x in (None, [], 'yes', True, 1):
            self.assertIs(evaluate(x)['candidate_UNVERIFIED'],False)

    def test_reject_outcome_early(self):
        row=deepcopy(BASE)
        row.update({'steps': {'battle_start': 100, 'last_auto': 135, 'outcome': 130, 'overworld': 150}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_overworld_early(self):
        row=deepcopy(BASE)
        row.update({'steps': {'battle_start': 100, 'last_auto': 120, 'outcome': 150, 'overworld': 140}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_outcome(self):
        row=deepcopy(BASE)
        row.update({'original_battle_outcome_verified': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_overworld(self):
        row=deepcopy(BASE)
        row.update({'original_overworld_return_verified': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_auto_after(self):
        row=deepcopy(BASE)
        row.update({'auto_after_outcome': 1})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_forced_switch(self):
        row=deepcopy(BASE)
        row.update({'forced_switch_count': 1})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_foe_owner(self):
        row=deepcopy(BASE)
        row.update({'owner': 1})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_negative_frame(self):
        row=deepcopy(BASE)
        row.update({'steps': {'battle_start': -1, 'last_auto': 120, 'outcome': 130, 'overworld': 150}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_same_outcome_frame(self):
        row=deepcopy(BASE)
        row.update({'steps': {'battle_start': 100, 'last_auto': 130, 'outcome': 130, 'overworld': 150}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

if __name__=='__main__': unittest.main()
