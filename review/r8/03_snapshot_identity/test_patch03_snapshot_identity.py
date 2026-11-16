"""Synthetic/hostile input tests only; never read a ROM or save."""
import unittest
from copy import deepcopy
from patch03_snapshot_identity import evaluate

BASE={'before': {'epoch': 2, 'request': 11, 'battler': 0, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': True, 'wild': True, 'doubles': False, 'partner': False, 'resources': 1}, 'after': {'epoch': 2, 'request': 11, 'battler': 0, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': True, 'wild': True, 'doubles': False, 'partner': False, 'resources': 1}}

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

    def test_reject_epoch_drift(self):
        row=deepcopy(BASE)
        row.update({'after': {'epoch': 3, 'request': 11, 'battler': 0, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': True, 'wild': True, 'doubles': False, 'partner': False, 'resources': 1}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_id_drift(self):
        row=deepcopy(BASE)
        row.update({'after': {'epoch': 2, 'request': 12, 'battler': 0, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': True, 'wild': True, 'doubles': False, 'partner': False, 'resources': 1}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_owner_drift(self):
        row=deepcopy(BASE)
        row.update({'after': {'epoch': 2, 'request': 11, 'battler': 1, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': True, 'wild': True, 'doubles': False, 'partner': False, 'resources': 1}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_missing_after(self):
        row=deepcopy(BASE)
        row.update({'after': {}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_false_owned(self):
        row=deepcopy(BASE)
        row.update({'after': {'epoch': 2, 'request': 11, 'battler': 0, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': False, 'wild': True, 'doubles': False, 'partner': False, 'resources': 1}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_both_enemy(self):
        row=deepcopy(BASE)
        row.update({'before': {'epoch': 2, 'request': 11, 'battler': 1, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': True, 'wild': True, 'doubles': False, 'partner': False, 'resources': 1}, 'after': {'epoch': 2, 'request': 11, 'battler': 1, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': True, 'wild': True, 'doubles': False, 'partner': False, 'resources': 1}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_both_doubles(self):
        row=deepcopy(BASE)
        row.update({'before': {'epoch': 2, 'request': 11, 'battler': 0, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': True, 'wild': True, 'doubles': True, 'partner': False, 'resources': 1}, 'after': {'epoch': 2, 'request': 11, 'battler': 0, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': True, 'wild': True, 'doubles': True, 'partner': False, 'resources': 1}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_zero_epoch(self):
        row=deepcopy(BASE)
        row.update({'before': {'epoch': 0, 'request': 11, 'battler': 0, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': True, 'wild': True, 'doubles': False, 'partner': False, 'resources': 1}, 'after': {'epoch': 0, 'request': 11, 'battler': 0, 'command': 17, 'turn': 4, 'party': 2, 'foe': 1, 'owned': True, 'wild': True, 'doubles': False, 'partner': False, 'resources': 1}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

if __name__=='__main__': unittest.main()
