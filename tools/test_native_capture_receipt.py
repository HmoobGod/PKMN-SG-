"""Synthetic tests of receipt envelope only; no ROM/game/equipment executed."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_verify_native_wild_chain import synthetic
import native_capture_receipt as cap
import verify_native_wild_chain as v


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        self.rom = self.d / 'rom.gba'
        self.sram = self.d / 'original.sav'
        self.rom.write_bytes(b'synthetic ROM only')
        self.sram.write_bytes(b'synthetic SRAM only')
        exact = hashlib.sha256(self.rom.read_bytes()).hexdigest()
        for mod in (cap, v):
            p = patch.object(mod, 'EXACT_ROM_SHA256', exact)
            p.start()
            self.addCleanup(p.stop)

    def test_invalid_rom_blocked(self):
        with patch.object(cap, 'EXACT_ROM_SHA256', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'exact modified ROM'):
                cap.NativeCaptureReceipt(self.rom, self.sram)

    def test_initial_receipt_has_pid_and_start(self):
        c=cap.NativeCaptureReceipt(self.rom,self.sram)
        self.assertRegex(c.start_marker,r'RUN_START native-[0-9a-f]{32} pid=[0-9]+ start=[0-9.]+')
        self.assertEqual(c.pid, __import__('os').getpid())
        self.assertTrue(c.run_id.startswith('native-'))

    def test_debugger_and_screenshot_allowlist(self):
        c=cap.NativeCaptureReceipt(self.rom,self.sram)
        c.note_breakpoint('0x808e336')
        c.note_screenshot_label('movement_2')
        with self.assertRaisesRegex(ValueError, 'unrecognized breakpoint'):
            c.note_breakpoint('0x2000000')
        with self.assertRaisesRegex(ValueError, 'invalid screenshot'):
            c.note_screenshot_label('load_state')

    def test_guest_stop_raw_preserved(self):
        c=cap.NativeCaptureReceipt(self.rom,self.sram)
        row=synthetic()['original_cpu_events'][0]
        c.note_original_gdb_stop(row)
        self.assertEqual(c.events[0]['r0'],row['r0'])
        self.assertNotIn('run_id',row)
        self.assertIn('run_id',c.events[0])

    def test_no_guest_data_synthesis(self):
        c=cap.NativeCaptureReceipt(self.rom,self.sram)
        with self.assertRaisesRegex(ValueError, 'debugger-supplied'):
            c.note_original_gdb_stop('made-up')
        with self.assertRaisesRegex(ValueError, 'debugger-supplied'):
            c.note_original_gdb_stop({'pc':'0x808e336','run_id':'forged'})

    def test_host_input_confirm_after_walk_rejected(self):
        c=cap.NativeCaptureReceipt(self.rom,self.sram)
        c.note_key('x',1.0)
        c.note_key('Left',2.0)
        with self.assertRaisesRegex(ValueError, 'confirmation after movement'):
            c.note_key('x',3.0)

    def test_host_clock_must_increase(self):
        c=cap.NativeCaptureReceipt(self.rom,self.sram)
        c.note_key('x',1.0)
        with self.assertRaisesRegex(ValueError, 'clock regression'):
            c.note_key('x',1.0)

    def test_end_rehash_rejects_save_change(self):
        c=cap.NativeCaptureReceipt(self.rom,self.sram)
        self.sram.write_bytes(b'modified')
        with self.assertRaisesRegex(ValueError, 'save changed'):
            c.finalize()

    def test_end_rehash_rejects_rom_change(self):
        c=cap.NativeCaptureReceipt(self.rom,self.sram)
        self.rom.write_bytes(b'modified')
        with self.assertRaisesRegex(ValueError, 'ROM or save changed'):
            c.finalize()

    def test_successful_receipt_matches_strict_verifier(self):
        c=cap.NativeCaptureReceipt(self.rom,self.sram)
        c.note_breakpoint('0x808e336')
        c.note_screenshot_label('title')
        c.note_key('x',1.0)
        c.note_key('Left',2.0)
        for e in synthetic()['original_cpu_events']:
            c.note_original_gdb_stop(e)
        report=c.finalize(mode='v5-full',output_dir=self.d/'receipt')
        self.assertTrue(report['source_rom_rehashed_at_end'])
        self.assertTrue(report['source_save_rehashed_at_end'])
        self.assertEqual(report['complete_cpu_episodes'],2)
        self.assertTrue(report['post_save_unchanged'])
        self.assertEqual(report['process_identity_level'],'CAPTURE_MARKER_ATTESTED_PID_AND_START')
        self.assertTrue((self.d/'receipt'/'original_cpu_capture.json').exists())
        self.assertTrue((self.d/'receipt'/'original_console.log').exists())
        with self.assertRaisesRegex(ValueError,'already closed'):
            c.finalize()

    def test_existing_destination_refused(self):
        c=cap.NativeCaptureReceipt(self.rom,self.sram)
        c.note_key('Left',2.0)
        for e in synthetic()['original_cpu_events']:
            c.note_original_gdb_stop(e)
        with self.assertRaisesRegex(FileExistsError,'never replace'):
            c.finalize(mode='v5-full',output_dir=self.d)

    def test_no_output_without_verified_events(self):
        c=cap.NativeCaptureReceipt(self.rom,self.sram)
        c.note_key('Left',2.0)
        dest=self.d/'result'
        with self.assertRaisesRegex(ValueError, 'event'):
            c.finalize(output_dir=dest)
        self.assertFalse(dest.exists())


if __name__ == '__main__':
    unittest.main()
