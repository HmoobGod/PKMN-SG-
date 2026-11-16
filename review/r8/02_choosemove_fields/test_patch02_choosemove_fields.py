"""Synthetic/hostile input tests only; never read a ROM or save."""
import unittest
from copy import deepcopy
from patch02_choosemove_fields import evaluate

BASE={'payload': [19, 0, 0, 0, 1, 1, 2, 1, 0, 0, 0, 0, 8, 5, 0, 0, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'moves': [257, 258, 0, 0], 'pp': [8, 5, 0, 0], 'max_pp': [10, 5, 0, 0]}

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

    def test_reject_short_buffer(self):
        row=deepcopy(BASE)
        row.update({'payload': [19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_move_in_payload_drift(self):
        row=deepcopy(BASE)
        row.update({'payload': [19, 0, 0, 0, 1, 2, 2, 1, 0, 0, 0, 0, 8, 5, 0, 0, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_pp_in_payload_drift(self):
        row=deepcopy(BASE)
        row.update({'payload': [19, 0, 0, 0, 1, 1, 2, 1, 0, 0, 0, 0, 9, 5, 0, 0, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_maxpp_in_payload_drift(self):
        row=deepcopy(BASE)
        row.update({'payload': [19, 0, 0, 0, 1, 1, 2, 1, 0, 0, 0, 0, 8, 5, 0, 0, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_max_below_pp(self):
        row=deepcopy(BASE)
        row.update({'max_pp': [7, 5, 0, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_populated_zero_max(self):
        row=deepcopy(BASE)
        row.update({'max_pp': [10, 0, 0, 0], 'pp': [8, 0, 0, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_empty_nonzero_pp(self):
        row=deepcopy(BASE)
        row.update({'moves': [257, 0, 0, 0], 'pp': [8, 1, 0, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_empty_nonzero_max(self):
        row=deepcopy(BASE)
        row.update({'moves': [257, 0, 0, 0], 'max_pp': [10, 5, 0, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_wrong_move_len(self):
        row=deepcopy(BASE)
        row.update({'moves': [257, 258, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_bool_move(self):
        row=deepcopy(BASE)
        row.update({'moves': [True, 258, 0, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_oversized_move(self):
        row=deepcopy(BASE)
        row.update({'moves': [65536, 258, 0, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_negative_pp(self):
        row=deepcopy(BASE)
        row.update({'pp': [-1, 5, 0, 0]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

if __name__=='__main__': unittest.main()
