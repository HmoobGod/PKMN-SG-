"""Synthetic/hostile input tests only; never read a ROM or save."""
import unittest
from copy import deepcopy
from patch07_move_legality import evaluate

BASE={'moves': [247, 157, 92, 269], 'pp': [10, 10, 10, 10], 'legal': [True, True, True, True], 'targets': [True, True, True, True], 'priority': [1, 2, 3, 4], 'slot': 2, 'engine_limits_checked': True, 'engine_target_checked': True, 'epoch': 4, 'legality_epoch': 4}

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

    def test_reject_no_move(self):
        row=deepcopy(BASE)
        row.update({'moves': [247, 157, 0, 269]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_zero_pp(self):
        row=deepcopy(BASE)
        row.update({'pp': [10, 10, 0, 10]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_illegal(self):
        row=deepcopy(BASE)
        row.update({'legal': [True, True, False, True]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_bad_target(self):
        row=deepcopy(BASE)
        row.update({'targets': [True, True, False, True]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_unchecked_limits(self):
        row=deepcopy(BASE)
        row.update({'engine_limits_checked': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_unchecked_target(self):
        row=deepcopy(BASE)
        row.update({'engine_target_checked': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_drift_epoch(self):
        row=deepcopy(BASE)
        row.update({'legality_epoch': 5})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_invalid_slot(self):
        row=deepcopy(BASE)
        row.update({'slot': 4})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_bool_slot(self):
        row=deepcopy(BASE)
        row.update({'slot': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_truthy_legal(self):
        row=deepcopy(BASE)
        row.update({'legal': [True, True, 'yes', True]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_oversized_pp(self):
        row=deepcopy(BASE)
        row.update({'pp': [10, 10, 100, 10]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_bad_priority(self):
        row=deepcopy(BASE)
        row.update({'priority': [1, 2, 10, 4]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

if __name__=='__main__': unittest.main()
