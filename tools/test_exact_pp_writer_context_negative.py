#!/usr/bin/env python3
"""Synthetic PP-writer context adversarial regressions; NO original ROM execution.

Built on PR49's offline audit only. In particular, a valid writer CPU marker
must be rejected if original Main, battle flags, battler count or the inbattle
bit is invalid. Mutations prove the checks are not superficial assertions.
"""
import inspect
import unittest

import test_exact_joint_player_terminal as t
import verify_exact_joint_player_terminal as v


class OriginalWriterContextNegativeTests(unittest.TestCase):
    def invalid_writer(self, field, value):
        d = t.fixture(pp=True)
        self.assertEqual(d["events"][7]["pc"], v.WRITER)
        d["events"][7][field] = value
        return d

    def test_wrong_flags_rejected_at_real_writer_pc(self):
        d = self.invalid_writer("flags", 0)
        with self.assertRaisesRegex(ValueError, "outside active Main wild-single"):
            v.audit(d)

    def test_wrong_battler_count_rejected_at_real_writer_pc(self):
        d = self.invalid_writer("battlers", 0)
        with self.assertRaisesRegex(ValueError, "outside active Main wild-single"):
            v.audit(d)

    def test_wrong_guest_inbattle_rejected_at_real_writer_pc(self):
        d = self.invalid_writer("inbattle", 0)
        with self.assertRaisesRegex(ValueError, "outside active Main wild-single"):
            v.audit(d)

    def test_each_context_field_independently_matters(self):
        # Change just one allowed context value in an otherwise complete
        # seven-marker CPU action with real writer PC, address and PP debit.
        for field in ("flags", "battlers", "inbattle"):
            with self.subTest(field=field):
                d = self.invalid_writer(field, 0)
                with self.assertRaises(ValueError):
                    v.audit(d)
        good = v.audit(t.fixture(pp=True))
        self.assertEqual(good["original_native_pp_writer_events"], 1)
        self.assertEqual(good["attributed_original_pp_writer_candidates"], 1)
        self.assertFalse(good["unmatched_pp_cause_certified"])
        self.assertEqual(good["formal_native_gameplay_acceptance"], 0)

    def test_non_writer_drift_is_not_misclassified_as_original_writer(self):
        # Different CPU PC is not the authenticated writer: it can be
        # classified as a non-writer PP mutation, NEVER a positive debit.
        d = self.invalid_writer("flags", 0)
        d["events"][7]["pc"] = 0x081FB8DA
        x = v.audit(d)
        self.assertEqual(x["original_native_pp_writer_events"], 0)
        self.assertEqual(x["attributed_original_pp_writer_candidates"], 0)
        self.assertEqual(x["non_writer_pp_byte_mutations"], 1)
        self.assertFalse(x["unmatched_pp_cause_certified"])

    def test_original_main_clear_rejects_stale_valid_writer_context(self):
        d = t.fixture(pp=False)
        d["steps"] = 12
        d["final_pp"][0] = 19
        d["events"].append(t.event(11, 9, pc=v.WRITER, slot=0, r1=v.PP,
                                   before=20, after=19,
                                   flags=4, battlers=2, inbattle=2))
        with self.assertRaisesRegex(ValueError, "outside active Main wild-single"):
            v.audit(d)

    def test_flags_and_battlers_mutations_remove_only_targeted_gate(self):
        # Prove these negatives would fail to reject the trace if their
        # specific flags/battlers context conjunct were neutralized. Synthetic-only:
        # no file reads, opcode attestation, probe or guest execution.
        source = inspect.getsource(v.audit)
        guard = ('require(old_main==2 and (e["inbattle"]&2) and\n'
                 '                            e["flags"]==4 and e["battlers"]==2,')
        self.assertEqual(source.count(guard), 1)
        variants = {
            "flags": guard.replace('e["flags"]==4 and ', ''),
            "battlers": guard.replace('e["battlers"]==2,', 'True,'),
        }
        for field, replacement in variants.items():
            with self.subTest(mutation=field):
                d = self.invalid_writer(field, 0)
                with self.assertRaises(ValueError):
                    v.audit(d)
                scope = dict(vars(v))
                exec(compile(source.replace(guard, replacement),
                             "<synthetic-writer-gate-mutation>", "exec"), scope)
                report = scope["audit"](d)
                self.assertEqual(report["original_native_pp_writer_events"], 1)
                self.assertFalse(report["unmatched_pp_cause_certified"])
                self.assertFalse(report["production_promotion_authorized"])

    def test_reentry_pp_is_never_attached_to_closed_prior_epoch(self):
        d = t.fixture(pp=False)
        d["steps"] = 13
        d["final_main"] = 2
        d["final_pp"][0] = 19
        d["events"].append(t.event(11, 10, before=0, after=2,
                                   inbattle=2, flags=4, battlers=2))
        d["events"].append(t.event(12, 9, pc=v.WRITER, slot=0,
                                   r1=v.PP, before=20, after=19,
                                   inbattle=2, flags=4, battlers=2))
        report = v.audit(d)
        self.assertEqual(report["original_native_pp_writer_events"], 1)
        self.assertEqual(report["attributed_original_pp_writer_candidates"], 0)
        self.assertEqual(report["original_emissions_without_attributed_pp_writer"], 1)
        self.assertFalse(report["original_outcome_writer_pc_certified"])
        self.assertFalse(report["manual_fallback_certified"])


if __name__ == "__main__":
    unittest.main()
