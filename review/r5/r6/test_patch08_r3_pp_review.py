"""Claude R2 blocker regressions: exactly one PP store, candidate marker pinned.
Generated events only; no private ROM, save, or emulator trace.
"""
import unittest
from dataclasses import replace
from patch08_pp_epoch_attribution import Event, candidates


def valid():
    return [Event(10, 1, 0, 'fight', 0),
            Event(11, 1, 0, 'move', 3),
            Event(19, 1, 0, 'pp', 3, 20, 19, True)]


class PPReviewRegressions(unittest.TestCase):
    def test_one_proven_player_pp_witness_has_only_unverified_marker(self):
        output = candidates(valid())
        self.assertEqual(len(output['candidates']), 1)
        self.assertEqual(output['candidates'][0]['epoch'], 1)
        self.assertEqual(output['candidates'][0]['slot'], 3)
        self.assertIs(output['candidates'][0]['candidate_UNVERIFIED'], True)
        self.assertEqual(output['native_accepted'], 0)
        for field in ('legality_verified', 'engine_request_owned_verified',
                      'manual_fallback_verified'):
            self.assertIs(output[field], False)

    def test_two_player_pp_writes_same_epoch_deny_candidate(self):
        base = valid()
        second = replace(base[-1], step=20, before=19, after=18)
        output = candidates(base + [second])
        self.assertEqual(output['candidates'], [])
        self.assertEqual(output['native_accepted'], 0)

    def test_an_extra_opponent_pp_write_never_falsifies_unique_player_pp(self):
        base = valid()
        foe = replace(base[-1], step=20, owner=1, before=12, after=11)
        output = candidates(base + [foe])
        self.assertEqual(len(output['candidates']), 1)
        self.assertIs(output['candidates'][0]['candidate_UNVERIFIED'], True)

    def test_two_pp_writes_across_distinct_epochs_stay_distinct(self):
        a = valid()
        b = [replace(e, epoch=2, step=e.step+20) for e in a]
        out = candidates(a+b)
        self.assertEqual([c['epoch'] for c in out['candidates']], [1,2])
        self.assertTrue(all(c['candidate_UNVERIFIED'] is True for c in out['candidates']))


if __name__ == '__main__':
    unittest.main()
