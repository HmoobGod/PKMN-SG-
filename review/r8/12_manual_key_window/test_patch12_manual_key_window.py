"""Synthetic/hostile input tests only; never read a ROM or save."""
import unittest
from copy import deepcopy
from patch12_manual_key_window import evaluate

BASE={'times': {'defer': 10, 'menu': 11, 'human': 12, 'manual_action': 13}, 'input_source': 'physical_human', 'key': 'A', 'emulated_input_injected': False, 'automatic_action_after_defer': False, 'battler': 0}

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

    def test_reject_manual_before_human(self):
        row=deepcopy(BASE)
        row.update({'times': {'defer': 10, 'menu': 11, 'human': 13, 'manual_action': 12}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_same_frame(self):
        row=deepcopy(BASE)
        row.update({'times': {'defer': 10, 'menu': 11, 'human': 11, 'manual_action': 13}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_menu_before_defer(self):
        row=deepcopy(BASE)
        row.update({'times': {'defer': 12, 'menu': 11, 'human': 13, 'manual_action': 14}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_human(self):
        row=deepcopy(BASE)
        row.update({'times': {'defer': 10, 'menu': 11, 'human': 12}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_automatic_key(self):
        row=deepcopy(BASE)
        row.update({'input_source': 'auto'})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_injected_key(self):
        row=deepcopy(BASE)
        row.update({'emulated_input_injected': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_auto_after_defer(self):
        row=deepcopy(BASE)
        row.update({'automatic_action_after_defer': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_partner(self):
        row=deepcopy(BASE)
        row.update({'battler': 1})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_unknown_key(self):
        row=deepcopy(BASE)
        row.update({'key': 'CAPTURE'})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_negative_time(self):
        row=deepcopy(BASE)
        row.update({'times': {'defer': -1, 'menu': 11, 'human': 12, 'manual_action': 13}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_bool_time(self):
        row=deepcopy(BASE)
        row.update({'times': {'defer': True, 'menu': 11, 'human': 12, 'manual_action': 13}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

if __name__=='__main__': unittest.main()
