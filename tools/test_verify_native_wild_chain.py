"""Public synthetic-only tests; no original game bytes or save data."""
import unittest
import verify_native_wild_chain as v


def synthetic(episodes=2):
    out = []
    for i in range(episodes):
        t = 10.0 * (i + 1)
        out.extend([
            {'t': t, 'pc': v.PP, 'main': 2, 'r0': '0x1', 'pp_addr': '0x2001f8a', 'before': 20, 'after': 19, 'after_pc': '0x809e6bc'},
            {'t': t+1, 'pc': v.PP, 'main': 2, 'r0': '0x0', 'pp_addr': '0x2001ef1', 'before': 20, 'after': 19, 'after_pc': '0x809e6bc'},
            {'t': t+2, 'pc': v.FIRST_GATE, 'main': 2, 'Z': 1, 'branch_observed_taken': True, 'after_pc': '0x808e364'},
            {'t': t+2.5, 'pc': v.STATE_LOAD, 'main': 2, 'r5': '0x2001ab4', 'state_word': '0x4', 'after_r3': '0x4', 'after_pc': '0x808e372'},
            {'t': t+3, 'pc': v.TERMINAL_GATE, 'main': 2, 'Z': 1, 'r3': '0x4', 'r5': '0x2001ab4', 'state_word': '0x4', 'branch_observed_taken': True, 'after_pc': '0x808e324'},
            {'t': t+4, 'pc': v.MAIN_CLEAR, 'main': 2, 'store_addr': '0x3005a0d', 'r2': '0x0', 'before': 2, 'after': 0, 'after_pc': '0x808e338'},
        ])
    return {'rom_sha256': v.EXACT_ROM_SHA256, 'original_cpu_events': out}


class Chain(unittest.TestCase):
    def test_success_two_episodes(self):
        r = v.verify_capture(synthetic(), 'KEY x 2\nKEY Left 3\nKEY Right 4')
        self.assertEqual(r['complete_cpu_episodes'], 2)
        self.assertEqual(r['fixed_status_labels']['formal_native_acceptance'], '0/20')
        self.assertEqual(r['original_outcome_semantics'], 'UNCLASSIFIED')

    def test_hash_refusal(self):
        f = synthetic(); f['rom_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'hash'): v.verify_capture(f)

    def test_clock_refusal(self):
        f = synthetic(); f['original_cpu_events'][2]['t'] = 9
        with self.assertRaisesRegex(ValueError, 'chronology'): v.verify_capture(f)

    def test_wrong_actor_refusal(self):
        f = synthetic(); f['original_cpu_events'][1]['r0'] = '0x2'
        with self.assertRaisesRegex(ValueError, 'ownership'): v.verify_capture(f)

    def test_pp_no_decrement_refusal(self):
        f = synthetic(); f['original_cpu_events'][1]['after'] = 20
        with self.assertRaisesRegex(ValueError, 'decrement'): v.verify_capture(f)

    def test_wrong_branch_refusal(self):
        f = synthetic(); f['original_cpu_events'][4]['after_pc'] = '0x808e376'
        with self.assertRaisesRegex(ValueError, 'branch'): v.verify_capture(f)

    def test_wrong_main_store_refusal(self):
        f = synthetic(); f['original_cpu_events'][5]['after'] = 2
        with self.assertRaisesRegex(ValueError, 'Main'): v.verify_capture(f)

    def test_missing_terminal_gate_refusal(self):
        f = synthetic()
        f['original_cpu_events'] = [e for e in f['original_cpu_events'] if e['pc'] != v.TERMINAL_GATE]
        with self.assertRaisesRegex(ValueError, 'terminal'): v.verify_capture(f)

    def test_wrong_state_load_refusal(self):
        f = synthetic(); f['original_cpu_events'][3]['state_word'] = '0x2'
        with self.assertRaisesRegex(ValueError, 'state-load'): v.verify_capture(f)

    def test_wrong_gate_state_word_refusal(self):
        f = synthetic(); f['original_cpu_events'][4]['state_word'] = '0x2'
        with self.assertRaisesRegex(ValueError, 'state-word'): v.verify_capture(f)

    def test_missing_state_load_refusal(self):
        f = synthetic()
        f['original_cpu_events'] = [e for e in f['original_cpu_events'] if e['pc'] != v.STATE_LOAD]
        with self.assertRaisesRegex(ValueError, 'state-load'): v.verify_capture(f)

    def test_one_episode_refusal(self):
        with self.assertRaisesRegex(ValueError, 'at least two'): v.verify_capture(synthetic(1))

    def test_host_action_refusal(self):
        with self.assertRaisesRegex(ValueError, 'host battle input'):
            v.verify_capture(synthetic(), 'KEY x 2\nKEY Left 3\nKEY x 10')

    def test_trailing_incomplete_does_not_count(self):
        f = synthetic()
        f['original_cpu_events'].append({'t': 25, 'pc': v.PP, 'main': 2, 'r0': '0x1', 'pp_addr': '0x2001f8a', 'before': 10, 'after': 9, 'after_pc': '0x809e6bc'})
        r = v.verify_capture(f)
        self.assertEqual(r['complete_cpu_episodes'], 2)
        self.assertEqual(r['trailing_incomplete_events'], 1)

    def test_same_process_required(self):
        f = synthetic(); f['original_cpu_events'][0]['pc'] = '0x808e322'
        with self.assertRaisesRegex(ValueError, 'unexpected'): v.verify_capture(f)


if __name__ == '__main__':
    unittest.main()
