"""Synthetic/hostile input tests only; never read a ROM or save."""
import unittest
from copy import deepcopy
from patch13_pp_opcode_join import evaluate

BASE={'events': [{'kind': 'fight', 'f': 10, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'move', 'f': 11, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'pp', 'f': 20, 'epoch': 1, 'owner': 0, 'slot': 2, 'pc': '0x0809e6ba', 'opcode_verified': True, 'before': 10, 'after': 9}]}

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

    def test_reject_two_pp(self):
        row=deepcopy(BASE)
        row.update({'events': [{'kind': 'fight', 'f': 10, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'move', 'f': 11, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'pp', 'f': 20, 'epoch': 1, 'owner': 0, 'slot': 2, 'pc': '0x0809e6ba', 'opcode_verified': True, 'before': 10, 'after': 9}, {'kind': 'pp', 'f': 21, 'epoch': 1, 'owner': 0, 'slot': 2, 'pc': '0x0809e6ba', 'opcode_verified': True, 'before': 9, 'after': 8}]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_wrong_pp_pc(self):
        row=deepcopy(BASE)
        row.update({'events': [{'kind': 'fight', 'f': 10, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'move', 'f': 11, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'pp', 'f': 20, 'epoch': 1, 'owner': 0, 'slot': 2, 'pc': '0x0809e6bc', 'opcode_verified': True, 'before': 10, 'after': 9}]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_no_opcode(self):
        row=deepcopy(BASE)
        row.update({'events': [{'kind': 'fight', 'f': 10, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'move', 'f': 11, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'pp', 'f': 20, 'epoch': 1, 'owner': 0, 'slot': 2, 'pc': '0x0809e6ba', 'opcode_verified': False, 'before': 10, 'after': 9}]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_enemy_pp(self):
        row=deepcopy(BASE)
        row.update({'events': [{'kind': 'fight', 'f': 10, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'move', 'f': 11, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'pp', 'f': 20, 'epoch': 1, 'owner': 1, 'slot': 2, 'pc': '0x0809e6ba', 'opcode_verified': True, 'before': 10, 'after': 9}]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_same_frame(self):
        row=deepcopy(BASE)
        row.update({'events': [{'kind': 'fight', 'f': 10, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'move', 'f': 11, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'pp', 'f': 11, 'epoch': 1, 'owner': 0, 'slot': 2, 'pc': '0x0809e6ba', 'opcode_verified': True, 'before': 10, 'after': 9}]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_wrong_slot(self):
        row=deepcopy(BASE)
        row.update({'events': [{'kind': 'fight', 'f': 10, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'move', 'f': 11, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'pp', 'f': 20, 'epoch': 1, 'owner': 0, 'slot': 3, 'pc': '0x0809e6ba', 'opcode_verified': True, 'before': 10, 'after': 9}]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_double_debit(self):
        row=deepcopy(BASE)
        row.update({'events': [{'kind': 'fight', 'f': 10, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'move', 'f': 11, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'pp', 'f': 20, 'epoch': 1, 'owner': 0, 'slot': 2, 'pc': '0x0809e6ba', 'opcode_verified': True, 'before': 10, 'after': 8}]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_zero_before(self):
        row=deepcopy(BASE)
        row.update({'events': [{'kind': 'fight', 'f': 10, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'move', 'f': 11, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'pp', 'f': 20, 'epoch': 1, 'owner': 0, 'slot': 2, 'pc': '0x0809e6ba', 'opcode_verified': True, 'before': 0, 'after': -1}]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

    def test_reject_epoch_drift(self):
        row=deepcopy(BASE)
        row.update({'events': [{'kind': 'fight', 'f': 10, 'epoch': 1, 'owner': 0, 'slot': 2}, {'kind': 'move', 'f': 11, 'epoch': 2, 'owner': 0, 'slot': 2}, {'kind': 'pp', 'f': 20, 'epoch': 1, 'owner': 0, 'slot': 2, 'pc': '0x0809e6ba', 'opcode_verified': True, 'before': 10, 'after': 9}]})
        got=evaluate(row)
        self.assertIs(got['candidate_UNVERIFIED'],False)
        self.assertEqual(got['native_accepted'],0)
        self.assertIs(got['production_authorized'],False)

if __name__=='__main__': unittest.main()
