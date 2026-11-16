"""Synthetic/hostile input tests only; never read a ROM or save."""
import unittest
from copy import deepcopy
from patch20_acceptance_gate import evaluate

BASE={'checks': [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True], 'witnesses': ['independent-original-engine:0', 'independent-original-engine:1', 'independent-original-engine:2', 'independent-original-engine:3', 'independent-original-engine:4', 'independent-original-engine:5', 'independent-original-engine:6', 'independent-original-engine:7', 'independent-original-engine:8', 'independent-original-engine:9', 'independent-original-engine:10', 'independent-original-engine:11', 'independent-original-engine:12', 'independent-original-engine:13', 'independent-original-engine:14', 'independent-original-engine:15', 'independent-original-engine:16', 'independent-original-engine:17', 'independent-original-engine:18', 'independent-original-engine:19'], 'exact_rom_identity_verified': True, 'manual_fallback_native_verified': True, 'forced_switch_blocked_native': True, 'private_replay_complete': True}

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

    def test_reject_missing_check(self):
        row=deepcopy(BASE)
        row.update({'checks': [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_short_checks(self):
        row=deepcopy(BASE)
        row.update({'checks': [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_truthy_check(self):
        row=deepcopy(BASE)
        row.update({'checks': [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, 1]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_witness(self):
        row=deepcopy(BASE)
        row.update({'witnesses': ['independent-original-engine:0', 'independent-original-engine:1', 'independent-original-engine:2', 'independent-original-engine:3', 'independent-original-engine:4', 'independent-original-engine:5', 'independent-original-engine:6', 'independent-original-engine:7', 'independent-original-engine:8', 'independent-original-engine:9', 'independent-original-engine:10', 'independent-original-engine:11', 'independent-original-engine:12', 'independent-original-engine:13', 'independent-original-engine:14', 'independent-original-engine:15', 'independent-original-engine:16', 'independent-original-engine:17', 'independent-original-engine:18', '']})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_duplicate_witness(self):
        row=deepcopy(BASE)
        row.update({'witnesses': ['independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1', 'independent-original-engine:1']})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_bad_witness_prefix(self):
        row=deepcopy(BASE)
        row.update({'witnesses': ['independent-original-engine:0', 'independent-original-engine:1', 'independent-original-engine:2', 'independent-original-engine:3', 'independent-original-engine:4', 'independent-original-engine:5', 'independent-original-engine:6', 'independent-original-engine:7', 'independent-original-engine:8', 'independent-original-engine:9', 'independent-original-engine:10', 'independent-original-engine:11', 'independent-original-engine:12', 'independent-original-engine:13', 'independent-original-engine:14', 'independent-original-engine:15', 'independent-original-engine:16', 'independent-original-engine:17', 'independent-original-engine:18', 'synthetic:19']})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_rom(self):
        row=deepcopy(BASE)
        row.update({'exact_rom_identity_verified': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_manual(self):
        row=deepcopy(BASE)
        row.update({'manual_fallback_native_verified': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_switch_not_blocked(self):
        row=deepcopy(BASE)
        row.update({'forced_switch_blocked_native': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_private_replay(self):
        row=deepcopy(BASE)
        row.update({'private_replay_complete': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

if __name__=='__main__': unittest.main()
