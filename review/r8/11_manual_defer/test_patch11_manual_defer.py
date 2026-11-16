"""Synthetic/hostile input tests only; never read a ROM or save."""
import unittest
from copy import deepcopy
from patch11_manual_defer import evaluate

BASE={'auto_response_count': 0, 'defer_requested': True, 'original_controller_retained': True, 'manual_menu_visible': True, 'human_input_after_menu': True, 'original_manual_action_seen': True, 'auto_switch_seen': False, 'events': ['defer', 'menu', 'human_input', 'original_manual_action'], 'original_request_epoch': 1, 'menu_epoch': 1}

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

    def test_reject_response_sent(self):
        row=deepcopy(BASE)
        row.update({'auto_response_count': 1})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_defer_false(self):
        row=deepcopy(BASE)
        row.update({'defer_requested': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_controller_lost(self):
        row=deepcopy(BASE)
        row.update({'original_controller_retained': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_menu(self):
        row=deepcopy(BASE)
        row.update({'manual_menu_visible': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_human(self):
        row=deepcopy(BASE)
        row.update({'human_input_after_menu': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_manual_action(self):
        row=deepcopy(BASE)
        row.update({'original_manual_action_seen': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_auto_switch(self):
        row=deepcopy(BASE)
        row.update({'auto_switch_seen': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_out_of_order(self):
        row=deepcopy(BASE)
        row.update({'events': ['defer', 'human_input', 'menu', 'original_manual_action']})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_prefix_only(self):
        row=deepcopy(BASE)
        row.update({'events': ['defer', 'menu', 'human_input']})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_extra_auto(self):
        row=deepcopy(BASE)
        row.update({'events': ['defer', 'menu', 'human_input', 'original_manual_action', 'auto_response']})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_epoch_drift(self):
        row=deepcopy(BASE)
        row.update({'menu_epoch': 2})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_zero_epoch(self):
        row=deepcopy(BASE)
        row.update({'menu_epoch': 0, 'original_request_epoch': 0})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

if __name__=='__main__': unittest.main()
