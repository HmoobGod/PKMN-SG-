"""Synthetic-only mutation regressions against Claude R5 R2 remaining blockers.

No private ROM, saves, traces, or CPU events are loaded.
"""
import copy
import unittest
from unittest.mock import patch

from test_private_original_cursor_writer import fixture, P, x
from audit_private_slot3_timeline_r5 import evaluate

BASE_REPORT = {'private_cpu_store_rows_schema_and_source_valid': True}


def coherent(first=3, second=None):
    z = fixture()
    z[1]['target_before'] = z[1]['target_after'] = 0
    z[3]['target_before'] = 1
    slot = z[1]
    slot.update(value=first, slot_after=first)
    slot['regs'][0] = first
    z[2]['slot_before'] = z[2]['slot_after'] = first
    z[3]['slot_before'] = first
    if second is not None:
        follow = copy.deepcopy(slot)
        follow.update(f=4100, slot_before=first, slot_after=second, value=second)
        follow['regs'][0] = second
        z.insert(2, follow)
        z[3]['slot_before'] = z[3]['slot_after'] = second
        z[4]['slot_before'] = second
        z[-1]['stores'] += 1
        z[-1]['slot_writes'] += 1
    return z


class CursorR7MutantRegressions(unittest.TestCase):
    def evaluate_with_independent_cpu_check(self, rows):
        with patch('audit_private_slot3_timeline_r5.audit', return_value=BASE_REPORT):
            return evaluate(rows)

    def test_nonzero_pointer_repoint_is_independently_denied(self):
        z = coherent(3)
        repoint = copy.deepcopy(z[0])
        repoint.update(f=4300, ptr_before=x(P), ptr_after=x(P + 4),
                       value=P + 4, slot_before=3, target_before=1,
                       slot_after=3, target_after=1)
        repoint['regs'][0] = P + 4
        z.insert(-2, repoint)
        with patch('audit_private_slot3_timeline_r5.audit', return_value=BASE_REPORT):
            with self.assertRaisesRegex(ValueError, 'unexpected pointer ownership transition'):
                evaluate(z)

    def test_clear_requires_matching_before_state_separately(self):
        z = coherent(3)
        z[-2]['slot_before'] = 2
        with patch('audit_private_slot3_timeline_r5.audit', return_value=BASE_REPORT):
            with self.assertRaisesRegex(ValueError, 'bad clear cursor state'):
                evaluate(z)

    def test_slot3_counter_is_exact_two_sided_rule(self):
        for slots, expected_count, expected_transition in [
            ((3, 3), 1, 0), ((1, 1), 0, 0), ((1, 3), 0, 0),
            ((3, 1), 0, 1), ((3, 0), 0, 1), ((2, 3), 0, 0)
        ]:
            with self.subTest(slots=slots):
                out = self.evaluate_with_independent_cpu_check(coherent(*slots))
                self.assertEqual(out['observed_written_slots'], list(slots))
                self.assertEqual(out['original_player0_slot_writes'], 2)
                self.assertEqual(out['slot3_direct_cpu_writes'], list(slots).count(3))
                self.assertEqual(out['consecutive_slot3_cpu_writes'], expected_count)
                self.assertEqual(out['slot3_then_different_slot'], expected_transition)

    def test_legacy_certification_flags_never_promoted(self):
        out = self.evaluate_with_independent_cpu_check(coherent(3, 3))
        for flag in ('taunt_repetition_cause_certified',
                     'dynamic_move_target_legality_certified',
                     'original_manual_fallback_certified',
                     'no_forced_switch_certified',
                     'production_authorized'):
            with self.subTest(flag=flag):
                self.assertIs(out[flag], False)
        self.assertEqual(out['formal_native_acceptance'], 0)
        self.assertIs(out['full_underlying_pointer_and_opcode_audit_passed'], True)

    def test_underlying_verification_false_not_promoted(self):
        with patch('audit_private_slot3_timeline_r5.audit',
                   return_value={'private_cpu_store_rows_schema_and_source_valid': False}):
            out = evaluate(coherent(3))
        self.assertIs(out['full_underlying_pointer_and_opcode_audit_passed'], False)


if __name__ == '__main__':
    unittest.main()
