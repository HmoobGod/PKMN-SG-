#!/usr/bin/env python3
"""All synthetic battle cursor snapshots; no private gameplay inputs."""
import unittest
import audit_private_original_move_cursor as a


def fake(slot=3,target=1,ptr=a.EWRAM_BASE+0x10000):
    data=bytearray(a.EWRAM_SIZE)
    offset=a.POINTER_LOCATION-a.EWRAM_BASE
    data[offset:offset+4]=ptr.to_bytes(4,'little')
    ix=ptr-a.EWRAM_BASE
    if ix>=0 and ix+a.TARGET_OFFSET<len(data):
        data[ix+a.MOVE_SLOT_OFFSET]=slot
        data[ix+a.TARGET_OFFSET]=target
    return data

class CursorSyntheticTests(unittest.TestCase):
    def test_cursor_segment_summary_without_native_claim(self):
        z=a.summarize([(100,fake(3,1)),(200,fake(3,1)),(300,fake(1,1))])
        self.assertEqual(z['accepted_snapshots'],3)
        self.assertEqual(z['cursor_segments'][0]['sample_count'],2)
        self.assertEqual(z['cursor_segments'][0]['move_slot'],3)
        self.assertEqual(z['cursor_segments'][1]['move_slot'],1)
        self.assertIs(z['cursor_is_confirmed_move_planner_output'],False)
        self.assertEqual(z['original_native_acceptance_scenarios'],0)

    def test_wrong_pointer_or_bad_snapshot_fails_closed(self):
        for mem in (b'',fake(ptr=0),fake(ptr=0x03000000),fake(ptr=0x0203FF00)):
            self.assertIsNone(a.decode_snapshot(mem))

    def test_invalid_slot_and_target_rejected(self):
        self.assertIsNone(a.decode_snapshot(fake(slot=4)))
        self.assertIsNone(a.decode_snapshot(fake(target=4)))

    def test_rejected_samples_not_promoted(self):
        z=a.summarize([(100,b''),(101,fake())])
        self.assertEqual(z['rejected_snapshots'],1)
        self.assertEqual(z['accepted_snapshots'],1)
        self.assertFalse(z['manual_fallback_certified'])

    def test_duplicate_frame_refused(self):
        with self.assertRaises(ValueError):a.summarize([(100,fake()),(100,fake())])

    def test_noninteger_frame_refused(self):
        with self.assertRaises(ValueError):a.summarize([('100',fake())])

if __name__=='__main__':unittest.main()
