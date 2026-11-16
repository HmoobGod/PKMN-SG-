"""Synthetic/hostile input tests only; never read a ROM or save."""
import unittest
from copy import deepcopy
from patch05_ticket_continuity import evaluate

BASE={'ticket': {'epoch': 4, 'turn': 7, 'party': 1, 'foe': 1, 'slot': 2, 'move_id': 269}, 'move': {'epoch': 4, 'turn': 7, 'party': 1, 'foe': 1, 'slot': 2, 'move_id': 269}, 'stage': 'CHOOSEMOVE', 'ticket_pending': True, 'lease_consumed': False}

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

    def test_reject_missing_pending(self):
        row=deepcopy(BASE)
        row.update({'ticket_pending': False})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_lease_already_used(self):
        row=deepcopy(BASE)
        row.update({'lease_consumed': True})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_wrong_stage(self):
        row=deepcopy(BASE)
        row.update({'stage': 'FIGHT'})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_ticket(self):
        row=deepcopy(BASE)
        row.update({'ticket': {}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_epoch_drift(self):
        row=deepcopy(BASE)
        row.update({'move': {'epoch': 5, 'turn': 7, 'party': 1, 'foe': 1, 'slot': 2, 'move_id': 269}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_turn_drift(self):
        row=deepcopy(BASE)
        row.update({'move': {'epoch': 4, 'turn': 8, 'party': 1, 'foe': 1, 'slot': 2, 'move_id': 269}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_party_drift(self):
        row=deepcopy(BASE)
        row.update({'move': {'epoch': 4, 'turn': 7, 'party': 2, 'foe': 1, 'slot': 2, 'move_id': 269}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_foe_drift(self):
        row=deepcopy(BASE)
        row.update({'move': {'epoch': 4, 'turn': 7, 'party': 1, 'foe': 2, 'slot': 2, 'move_id': 269}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_slot_drift(self):
        row=deepcopy(BASE)
        row.update({'move': {'epoch': 4, 'turn': 7, 'party': 1, 'foe': 1, 'slot': 1, 'move_id': 269}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_move_drift(self):
        row=deepcopy(BASE)
        row.update({'move': {'epoch': 4, 'turn': 7, 'party': 1, 'foe': 1, 'slot': 2, 'move_id': 157}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_invalid_slot(self):
        row=deepcopy(BASE)
        row.update({'ticket': {'epoch': 4, 'turn': 7, 'party': 1, 'foe': 1, 'slot': 4, 'move_id': 269}, 'move': {'epoch': 4, 'turn': 7, 'party': 1, 'foe': 1, 'slot': 4, 'move_id': 269}})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

if __name__=='__main__': unittest.main()
