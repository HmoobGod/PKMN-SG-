#!/usr/bin/env python3
"""Fail-closed synthetic mutation tests. No real modified ROM in CI."""
import copy
import unittest
import verify_exact_main_battle_edge as v


def row(step=5, frame=100, before=2, after=0):
    return dict(frame=frame, step_index=step, pc=0x0808E33C,
                opcode_halfword=0x7001, before_byte=before, after_byte=after,
                before_callback1=0x0808CBDD, after_callback1=0x081C7589,
                before_callback2=0x0808F225, after_callback2=0x081C9FC5,
                before_flags=4, after_flags=4, before_pending=0, after_pending=0,
                before_battlers=2, after_battlers=2, registers=[0]*8)


def fixture():
    return dict(schema=v.SCHEMA, current_sha256=v.CURRENT, modified_sha256=v.MODIFIED,
                save_sha256=v.SAVE, guest_writes=0, host_move_menu_inputs=0,
                new_hook_installed=False, status=1, start_frame=99, end_frame=120,
                window_frames=20, guest_steps=30, start_byte=2, end_byte=0,
                start_callback1=0x0808CBDD, end_callback1=0x081C7589,
                start_callback2=0x0808F225, end_callback2=0x081C9FC5,
                start_flags=4, end_flags=4, events=[row()])

class OriginalMainEdgeTests(unittest.TestCase):
    def denied(self, fn):
        x=fixture();fn(x)
        with self.assertRaises((ValueError, KeyError, TypeError)):v.audit(x)

    def test_cpu_bit_clear_is_not_battle_result(self):
        x=v.audit(fixture())
        self.assertEqual(x["observed_clear_edges"],1)
        self.assertTrue(x["callbacks_changed_by_window"])
        self.assertFalse(x["original_native_result_or_victory_certified"])
        self.assertFalse(x["original_battle_outcome_decision_pc_certified"])
        self.assertFalse(x["production_promotion_authorized"])
    def test_empty_completed_window(self):
        x=fixture();x["events"]=[];x["end_byte"]=2
        self.assertEqual(v.audit(x)["observed_clear_edges"],0)
    def test_low_bit_variation_does_not_miscount(self):
        x=fixture();x["events"][0]["before_byte"]=3;x["end_byte"]=1
        self.assertEqual(v.audit(x)["observed_clear_edges"],1)
    def test_multiple_original_bit_edges(self):
        x=fixture()
        x["events"].extend([row(8,104,0,2),row(11,108,2,0)])
        self.assertEqual(v.audit(x)["inbattle_bit_transitions"],3)
    def test_unknown_pc_is_unresolved(self):
        x=fixture();x["events"][0].update(pc=0,opcode_halfword=0)
        self.assertEqual(v.audit(x)["cpu_pc_candidates"],["UNRESOLVED"])
    def test_terminal_unproven_even_flags_clear(self):
        x=fixture();x["events"][0].update(before_flags=0,after_flags=0)
        x["start_flags"]=x["end_flags"]=0
        self.assertFalse(v.audit(x)["full_unattended_terminal_certified"])
    def test_wrong_rom(self):self.denied(lambda x:x.update(modified_sha256='x'))
    def test_wrong_current(self):self.denied(lambda x:x.update(current_sha256='x'))
    def test_wrong_save(self):self.denied(lambda x:x.update(save_sha256='x'))
    def test_hook_installed(self):self.denied(lambda x:x.update(new_hook_installed=True))
    def test_guest_modified(self):self.denied(lambda x:x.update(guest_writes=1))
    def test_host_menu_input(self):self.denied(lambda x:x.update(host_move_menu_inputs=1))
    def test_bad_boolean_guest(self):self.denied(lambda x:x.update(guest_writes=False))
    def test_incomplete(self):self.denied(lambda x:x.update(status=2))
    def test_overflow(self):self.denied(lambda x:x.update(status=3))
    def test_invalid_core(self):self.denied(lambda x:x.update(status=4))
    def test_clock_backwards(self):self.denied(lambda x:x.update(status=5))
    def test_fake_bool_status(self):self.denied(lambda x:x.update(status=True))
    def test_frame_incomplete(self):self.denied(lambda x:x.update(end_frame=118))
    def test_frame_negative(self):self.denied(lambda x:x.update(start_frame=-1))
    def test_frame_beyond_limit(self):self.denied(lambda x:x.update(window_frames=10001))
    def test_steps_missing(self):self.denied(lambda x:x.update(guest_steps=0))
    def test_steps_over_u32(self):self.denied(lambda x:x.update(guest_steps=0x100000000))
    def test_wrong_context(self):self.denied(lambda x:x.update(end_flags=8))
    def test_main_word_not_byte(self):self.denied(lambda x:x.update(start_byte=256))
    def test_bad_start_bit(self):self.denied(lambda x:x.update(start_byte=0))
    def test_missing_transition(self):self.denied(lambda x:x.update(events=[]))
    def test_bad_event_shape(self):self.denied(lambda x:x['events'][0].update(raw_bytes='bad'))
    def test_bad_top_shape(self):self.denied(lambda x:x.update(untrusted='bad'))
    def test_bad_pc(self):self.denied(lambda x:x['events'][0].update(pc=0x02001000))
    def test_bad_pc_alignment(self):self.denied(lambda x:x['events'][0].update(pc=0x0808E33D))
    def test_bad_opcode(self):self.denied(lambda x:x['events'][0].update(opcode_halfword=0x10000))
    def test_unknown_pc_with_spoofed_opcode(self):self.denied(lambda x:x['events'][0].update(pc=0))
    def test_bad_registers(self):self.denied(lambda x:x['events'][0].update(registers=[0]*7))
    def test_boolean_registers(self):self.denied(lambda x:x['events'][0].update(registers=[True]+[0]*7))
    def test_unchanged_bit(self):self.denied(lambda x:x['events'][0].update(after_byte=3))
    def test_wrong_final_bit(self):self.denied(lambda x:x.update(end_byte=2))
    def test_wrong_battlers(self):self.denied(lambda x:x['events'][0].update(after_battlers=4))
    def test_wrong_flags(self):self.denied(lambda x:x['events'][0].update(after_flags=8))
    def test_event_beyond_frame(self):self.denied(lambda x:x['events'][0].update(frame=121))
    def test_event_before_frame(self):self.denied(lambda x:x['events'][0].update(frame=98))
    def test_event_beyond_steps(self):self.denied(lambda x:x['events'][0].update(step_index=31))
    def test_duplicate_event(self):self.denied(lambda x:x['events'].append(copy.deepcopy(x['events'][0])))
    def test_oversized_events(self):self.denied(lambda x:x.update(events=[row() for _ in range(257)]))
    def test_second_clear_without_set(self):
        self.denied(lambda x:x['events'].append(row(9,105,2,0)))

if __name__=='__main__':unittest.main()
