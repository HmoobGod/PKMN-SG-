#!/usr/bin/env python3
"""Synthetic safety and failure-path tests; no live emulator or game assets."""
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('runner',here/'run_current_copy_probe_local.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CurrentProbeRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.rom=self.root/m.ROM_FILENAME
        self.save=self.root/m.SAVE_FILENAME
        self.observer=self.root/'capture_original_request_rsp.py'
        self.reportdir=self.root/'private'
        self.rom.write_bytes(b'ROM-only-fake-sample')
        self.save.write_bytes(b'fake-save-only')
        self.observer.write_bytes(b'# known synthetic observer\n')
        for name, val in [('ROM_LEN',self.rom.stat().st_size),
                          ('SAVE_LEN',self.save.stat().st_size),
                          ('ROM_SHA',hashlib.sha256(self.rom.read_bytes()).hexdigest()),
                          ('SAVE_SHA',hashlib.sha256(self.save.read_bytes()).hexdigest()),
                          ('OBSERVER_SHA',hashlib.sha256(self.observer.read_bytes()).hexdigest())]:
            p=patch.object(m,name,val)
            p.start();self.addCleanup(p.stop)

    def fake_output(self):
        return {'input_rom_identity_class':'current-duplicate-probe-only',
                'native_acceptance':0,
                'current_rom_loaded_in_emulator_proven':False,
                'events':[], 'probe_only':True,
                'tool_sent_battle_commands':0, 'tool_sent_guest_writes':0,
                'input_file_rom_sha256':m.ROM_SHA,
                'input_file_save_sha256':m.SAVE_SHA,
                'input_files_unchanged':True, 'failure':None,
                'probe_transcript':{'stop_raw_ascii':'S02'}}

    def test_default_is_offline_and_never_creates_output(self):
        with patch.object(m.subprocess,'run') as proc:
            r=m.run(self.rom,self.save,self.observer,self.reportdir)
            proc.assert_not_called()
        self.assertEqual(r['status'],'SAFE_PREFLIGHT_ONLY_NO_CONNECTION')
        self.assertFalse(self.reportdir.exists())
        self.assertFalse(r['engine_request_or_gameplay_certified'])

    def test_hash_mismatch_fails_before_subprocess(self):
        self.rom.write_bytes(b'WRONG'+self.rom.read_bytes()[5:])
        with patch.object(m.subprocess,'run') as proc:
            with self.assertRaisesRegex(m.PreflightError,'SHA256 mismatch'):
                m.run(self.rom,self.save,self.observer,self.reportdir,run_probe=True)
            proc.assert_not_called()

    def test_save_mismatch_fails_before_subprocess(self):
        self.save.write_bytes(b'Z'+self.save.read_bytes()[1:])
        with patch.object(m.subprocess,'run') as proc:
            with self.assertRaisesRegex(m.PreflightError,'SHA256 mismatch'):
                m.run(self.rom,self.save,self.observer,self.reportdir,run_probe=True)
            proc.assert_not_called()

    def test_wrong_observer_rejected_before_running(self):
        self.observer.write_bytes(b'# tampered observer\n')
        with patch.object(m.subprocess,'run') as proc:
            with self.assertRaisesRegex(m.PreflightError,'SHA256 mismatch'):
                m.run(self.rom,self.save,self.observer,self.reportdir,run_probe=True)
            proc.assert_not_called()

    def test_protected_original_basename_cannot_be_used(self):
        other=self.root/'Pokemon Soulgold.gba'
        other.write_bytes(self.rom.read_bytes())
        with self.assertRaisesRegex(m.PreflightError,'TEST_COPY'):
            m.run(other,self.save,self.observer,self.reportdir,run_probe=True)
        self.assertFalse(self.reportdir.exists())

    def test_symlink_file_and_output_dir_denied(self):
        alt=self.root/'alt'; alt.mkdir()
        alias=alt/m.ROM_FILENAME
        try: alias.symlink_to(self.rom)
        except (OSError, NotImplementedError): self.skipTest('symlinks unsupported')
        with self.assertRaisesRegex(m.PreflightError,'symlink'):
            m.run(alias,self.save,self.observer,self.reportdir)
        target=self.root/'destination';target.mkdir()
        self.reportdir.symlink_to(target,target_is_directory=True)
        with self.assertRaisesRegex(m.PreflightError,'symlink'):
            m.run(self.rom,self.save,self.observer,self.reportdir)

    def test_reject_invalid_port_timeout_and_flag(self):
        for kwargs in ({'port':0},{'port':65536},{'timeout':0.01},
                       {'timeout':31},{'run_probe':'yes'}):
            with self.subTest(kwargs=kwargs),self.assertRaises(m.PreflightError):
                m.run(self.rom,self.save,self.observer,self.reportdir,**kwargs)

    def test_optin_invokes_only_approved_flags_and_preserves_report(self):
        def fake_run(command,**options):
            self.assertEqual(options['check'],False)
            self.assertFalse(options.get('shell',False))
            self.assertIn('--probe-only',command)
            self.assertIn('--current-copy-probe-only',command)
            self.assertNotIn('c',command)
            self.assertNotIn('s',command)
            self.assertNotIn('Z0',command)
            self.assertNotIn('z0',command)
            self.assertNotIn('--deadline-seconds',command)
            self.assertEqual(command[command.index('--rom')+1],str(self.rom))
            self.assertEqual(command[command.index('--save')+1],str(self.save))
            target=Path(command[command.index('--output')+1]);self.assertFalse(target.exists())
            target.write_text(json.dumps(self.fake_output()))
            return subprocess.CompletedProcess(command,0,'','')
        with patch.object(m.subprocess,'run',side_effect=fake_run) as proc:
            r=m.run(self.rom,self.save,self.observer,self.reportdir,run_probe=True)
            proc.assert_called_once()
        self.assertEqual(r['status'],'PRIVATE_PROBE_REPORT_SAVED_NEEDS_ANALYSIS')
        self.assertTrue(Path(r['private_report_path']).is_file())
        self.assertFalse(r['emulator_loaded_rom_verified'])

    def test_failure_with_private_partial_report_is_preserved(self):
        def fake_run(cmd,**kwargs):
            target=Path(cmd[cmd.index('--output')+1]);target.write_text(json.dumps(self.fake_output()))
            return subprocess.CompletedProcess(cmd,2,'','')
        with patch.object(m.subprocess,'run',side_effect=fake_run):
            r=m.run(self.rom,self.save,self.observer,self.reportdir,run_probe=True)
        self.assertEqual(r['status'],'PRIVATE_PARTIAL_REPORT_SAVED')
        self.assertTrue(Path(r['private_report_path']).exists())

    def test_failure_without_report_not_misrepresented(self):
        with patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],2,'','')):
            r=m.run(self.rom,self.save,self.observer,self.reportdir,run_probe=True)
        self.assertEqual(r['status'],'NO_REPORT_OBSERVER_FAILED')
        self.assertIsNone(r['private_report_path'])

    def test_refuses_forged_native_acceptance_or_extra_cpu_events(self):
        for patchdata in ({'native_acceptance':1},{'events':[{'pc':'0x08000000'}]},
                          {'current_rom_loaded_in_emulator_proven':True}):
            def bad_run(cmd,**kwargs):
                target=Path(cmd[cmd.index('--output')+1])
                target.write_text(json.dumps({**self.fake_output(),**patchdata}))
                return subprocess.CompletedProcess(cmd,0,'','')
            with patch.object(m.subprocess,'run',side_effect=bad_run):
                with self.subTest(data=patchdata),self.assertRaises(m.PreflightError):
                    m.run(self.rom,self.save,self.observer,self.reportdir,run_probe=True)

    def test_subprocess_timeout_no_success_claim(self):
        with patch.object(m.subprocess,'run',side_effect=subprocess.TimeoutExpired(cmd=['x'],timeout=20)):
            r=m.run(self.rom,self.save,self.observer,self.reportdir,run_probe=True)
        self.assertEqual(r['status'],'OBSERVER_PROCESS_TIMEOUT_NO_NATIVE_EVIDENCE')
        self.assertIsNone(r['private_report_path'])

    def test_rehash_fails_closed_if_rom_changed_while_observer_running(self):
        def mutate(cmd,**kwargs):
            self.rom.write_bytes(b'A'+self.rom.read_bytes()[1:])
            return subprocess.CompletedProcess(cmd,0,'','')
        with patch.object(m.subprocess,'run',side_effect=mutate):
            with self.assertRaisesRegex(m.PreflightError,'SHA256 mismatch'):
                m.run(self.rom,self.save,self.observer,self.reportdir,run_probe=True)



# The .cmd wrapper is intentionally a plaintext local launcher, not an
# additional implementation of GDB commands. Test it without executing cmd.
class WindowsEntryTests(unittest.TestCase):
    def test_one_click_batch_is_local_probe_only(self):
        data=(here.parent/'Run_SoulGold_Current_Probe.cmd').read_text(encoding='utf-8').lower()
        self.assertIn('--run-probe',data)
        self.assertIn('run_current_copy_probe_local.py',data)
        self.assertNotIn('http://',data)
        self.assertNotIn('https://',data)
        commands='\n'.join(line.strip() for line in data.splitlines()
                            if line.strip() and not line.strip().startswith('echo '))
        for forbidden in ('--capture', ' --gdb', ' -g ', ' --patch', ' --cheat', ' --savestate',
                          'del ', 'copy /y ', 'move /y ', 'start mgba'):
            self.assertNotIn(forbidden,commands)

if __name__=='__main__':unittest.main()