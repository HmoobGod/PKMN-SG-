"""Synthetic/hostile input tests only; never read a ROM or save."""
import unittest
from copy import deepcopy
from patch18_npc_separation import evaluate

BASE={'player_battler': 0, 'owner_kind': 'player', 'enemy_ai_changed': False, 'npc_partner_present': False, 'npc_ai_changed': False, 'wild_single': True, 'double_battle': False, 'active_actor': 0, 'original_controller_verified': True}

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

    def test_reject_enemy_actor(self):
        row=deepcopy(BASE)
        row.update({'active_actor': 1})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_partner_actor(self):
        row=deepcopy(BASE)
        row.update({'active_actor': 2})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_not_player_kind(self):
        row=deepcopy(BASE)
        row.update({'owner_kind': 'npc'})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_enemy_ai_touched(self):
        row=deepcopy(BASE)
        row.update({'enemy_ai_changed': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_npc_present(self):
        row=deepcopy(BASE)
        row.update({'npc_partner_present': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_npc_ai_touched(self):
        row=deepcopy(BASE)
        row.update({'npc_ai_changed': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_doubles(self):
        row=deepcopy(BASE)
        row.update({'double_battle': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_trainer(self):
        row=deepcopy(BASE)
        row.update({'wild_single': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_wrong_player_battler(self):
        row=deepcopy(BASE)
        row.update({'player_battler': 1})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_controller_unverified(self):
        row=deepcopy(BASE)
        row.update({'original_controller_verified': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_bool_actor(self):
        row=deepcopy(BASE)
        row.update({'active_actor': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

if __name__=='__main__': unittest.main()
