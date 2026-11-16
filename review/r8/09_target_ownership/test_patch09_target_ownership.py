"""Synthetic/hostile input tests only; never read a ROM or save."""
import unittest
from copy import deepcopy
from patch09_target_ownership import evaluate

BASE={'battler': 0, 'owned': True, 'wild_single': True, 'doubles': False, 'target': 1, 'active_foe': 1, 'foe_alive': True, 'native_target_proven': True, 'partner': False, 'target_epoch': 3, 'request_epoch': 3}

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

    def test_reject_self_target(self):
        row=deepcopy(BASE)
        row.update({'target': 0})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_wrong_foe(self):
        row=deepcopy(BASE)
        row.update({'target': 2})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_dead_foe(self):
        row=deepcopy(BASE)
        row.update({'foe_alive': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_not_proven(self):
        row=deepcopy(BASE)
        row.update({'native_target_proven': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_partner(self):
        row=deepcopy(BASE)
        row.update({'partner': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_double(self):
        row=deepcopy(BASE)
        row.update({'doubles': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_not_owned(self):
        row=deepcopy(BASE)
        row.update({'owned': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_enemy_owner(self):
        row=deepcopy(BASE)
        row.update({'battler': 1})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_non_wild(self):
        row=deepcopy(BASE)
        row.update({'wild_single': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_epoch_drift(self):
        row=deepcopy(BASE)
        row.update({'target_epoch': 4})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_bool_target(self):
        row=deepcopy(BASE)
        row.update({'target': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

if __name__=='__main__': unittest.main()
