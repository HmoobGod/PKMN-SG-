"""Public synthetic-only regression tests for strict archived CPU witness verifier."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy

import verify_native_wild_chain as v

SAVE = '8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'


def synthetic(mode='v5-full', cycles=2):
    events = []
    for i in range(cycles):
        t=10.0*(i+1)
        events += [
            {'pc':v.PP,'t':t,'main':2,'r0':'0x1','after_pc':'0x809e6bc','pp_addr':'0x2001f8a','before':20,'after':19},
            {'pc':v.PP,'t':t+1,'main':2,'r0':'0x0','after_pc':'0x809e6bc','pp_addr':'0x2001ef1','before':20,'after':19},
            {'pc':v.FIRST_GATE,'t':t+2,'main':2,'Z':1,'branch_observed_taken':True,'after_pc':'0x808e364'},
        ]
        if mode=='v5-full':
            events += [{'pc':v.STATE_LOAD,'t':t+2.5,'main':2,'r5':'0x2001ab4','state_word':'0x4','after_r3':'0x4','after_pc':'0x808e372'}]
        if mode in ('v4-branch','v5-full'):
            events += [{'pc':v.TERMINAL_GATE,'t':t+3,'main':2,'Z':1,'branch_observed_taken':True,'after_pc':'0x808e324','r3':'0x4','r4':'0x2','r5':'0x2001ab4','state_word':'0x4'}]
        events += [{'pc':v.MAIN_CLEAR,'t':t+4,'main':2,'store_addr':'0x3005a0d','before':2,'after':0,'after_pc':'0x808e338','r2':'0x0'}]
    return {'rom_sha256':v.EXACT_ROM_SHA256, 'save_sha256':SAVE, 'original_cpu_events':events}


def console_for(capture):
    events = capture['original_cpu_events']
    return ('GDB S02\nBP 0x808e336 OK\nSNAP title\nKEY x 1.0\nKEY Left 2.0\n'
            + ''.join('STOP '+json.dumps(e)+'\n' for e in events)
            + f'EVENTS {len(events)}\nORIGINAL_POST_HASH {v.EXACT_ROM_SHA256} {SAVE}\n')


def verify(raw=None,mode='v5-full',console=None):
    if raw is None: raw=synthetic(mode)
    if console is None:console=console_for(raw)
    imported=v.normalize_legacy_archive(raw,console)
    return v.verify_capture(imported,console,mode)


class NativeChainStrictTests(unittest.TestCase):
    def test_v5_full_success_and_conservative_labels(self):
        r=verify()
        self.assertEqual(r['complete_cpu_episodes'],2)
        self.assertEqual(r['mode'],'v5-full')
        self.assertEqual(r['archive_single_console_consistent'],True)
        self.assertFalse(r['same_emulator_process_log'])  # no original OS PID in archive
        self.assertTrue(r['host_input_checked'])
        self.assertEqual(r['fixed_status_labels']['formal_native_acceptance'],'0/20')
        self.assertEqual(r['engine_request_ownership'],'NOT_PROVEN')

    def test_v3_relaxed_mode_explicit(self):
        r=verify(mode='v3-basic')
        self.assertEqual(r['complete_cpu_episodes'],2)
        self.assertFalse(r['episodes'][0]['terminal_gate_taken'])
        with self.assertRaisesRegex(ValueError,'missing mandatory original CPU stage'):
            verify(raw=synthetic('v3-basic'),mode='v5-full')

    def test_v4_relaxed_mode_explicit(self):
        r=verify(mode='v4-branch')
        self.assertTrue(r['episodes'][0]['terminal_gate_taken'])
        self.assertEqual(r['episodes'][0]['state_word_0x02001AB4'],'NOT_OBSERVED')
        with self.assertRaisesRegex(ValueError,'missing mandatory original CPU stage'):
            verify(raw=synthetic('v4-branch'),mode='v5-full')

    def test_state_load_after_terminal_rejected(self):
        a=synthetic(); z=a['original_cpu_events']; z[3],z[4]=z[4],z[3]
        z[3]['t'],z[4]['t']=z[4]['t'],z[3]['t']
        with self.assertRaisesRegex(ValueError,'ORDER'):verify(a)

    def test_first_gate_after_terminal_rejected(self):
        a=synthetic();z=a['original_cpu_events'];z[2],z[4]=z[4],z[2]
        z[2]['t'],z[4]['t']=z[4]['t'],z[2]['t']
        with self.assertRaisesRegex(ValueError,'ORDER'):verify(a)

    def test_pp_after_first_gate_rejected(self):
        a=synthetic();z=a['original_cpu_events'];z[1],z[2]=z[2],z[1]
        z[1]['t'],z[2]['t']=z[2]['t'],z[1]['t']
        with self.assertRaisesRegex(ValueError,'ORDER'):verify(a)

    def test_duplicate_gate_rejected(self):
        a=synthetic();z=a['original_cpu_events']; e=deepcopy(z[2]);e['t']=z[2]['t']+0.1;z.insert(3,e)
        with self.assertRaisesRegex(ValueError,'duplicated'):verify(a)

    def test_mixed_event_run_id_rejected(self):
        raw=synthetic();log=console_for(raw);a=v.normalize_legacy_archive(raw,log)
        a['original_cpu_events'][2]['run_id']='other_session'
        with self.assertRaisesRegex(ValueError,'mixed-process'):v.verify_capture(a,log)

    def test_unattested_run_id_rejected(self):
        raw=synthetic();log=console_for(raw);a=v.normalize_legacy_archive(raw,log)
        a['run']['run_id']='legacy:'+'0'*64
        with self.assertRaisesRegex(ValueError,'legacy run ID'):v.verify_capture(a,log)

    def test_instrumented_start_marker_is_required(self):
        raw=synthetic();log=console_for(raw);norm=v.normalize_legacy_archive(raw,log)
        norm['run']['provenance']='INSTRUMENTED_RUN'
        norm['run']['process_id_observed']=True
        with self.assertRaisesRegex(ValueError,'RUN_START'):
            v.verify_capture(norm,log)

    def test_native_instrumented_marker_can_be_checked(self):
        raw=synthetic();log=console_for(raw)
        run_id='native-run-unique-001'
        log=log.replace('GDB S02\n','RUN_START '+run_id+' pid=43210 start=1700000000.25\n',1)
        norm=v.normalize_legacy_archive(raw,console_for(raw))
        norm['run']={'run_id':run_id,'start_marker':'RUN_START '+run_id+' pid=43210 start=1700000000.25',
                     'console_sha256':v.hashlib.sha256(log.encode()).hexdigest(),
                     'provenance':'INSTRUMENTED_RUN','process_id_observed':True,
                     'pid':43210,'started_epoch':1700000000.25,'initial_save_sha256':SAVE}
        for e in norm['original_cpu_events']:
            e['run_id']=run_id
        result=v.verify_capture(norm,log)
        self.assertTrue(result['same_emulator_process_log'])
        self.assertEqual(result['process_identity_level'],'CAPTURE_MARKER_ATTESTED_PID_AND_START')
        self.assertTrue(result['post_save_unchanged'])
        self.assertEqual(result['complete_cpu_episodes'],2)

    def test_console_none_rejected(self):
        raw=synthetic();log=console_for(raw);a=v.normalize_legacy_archive(raw,log)
        with self.assertRaisesRegex(ValueError,'mandatory GDB console'):v.verify_capture(a,None)

    def test_unknown_command_rejected(self):
        a=synthetic();log=console_for(a).replace('KEY Left 2.0\n','KEY Left 2.0\nHOST_WRITE 0x2001ef1=0\n')
        with self.assertRaisesRegex(ValueError,'unknown host console'):verify(a,console=log)

    def test_host_action_after_movement_rejected(self):
        a=synthetic();log=console_for(a).replace('KEY Left 2.0\n','KEY Left 2.0\nKEY x 3.0\n')
        with self.assertRaisesRegex(ValueError,'host battle action'):verify(a,console=log)

    def test_stop_log_mismatch_rejected(self):
        raw=synthetic();log=console_for(raw);a=v.normalize_legacy_archive(raw,log)
        a['original_cpu_events'][1]['r0']='0x1'
        with self.assertRaisesRegex(ValueError,'CPU STOP mismatch'):v.verify_capture(a,log)

    def test_second_gdb_start_rejected(self):
        raw=synthetic();log=console_for(raw).replace('SNAP title\n','SNAP title\nGDB S02\n')
        with self.assertRaisesRegex(ValueError,'multiple run start markers|second GDB'):verify(raw,console=log)

    def test_nan_timestamp_rejected(self):
        a=synthetic();a['original_cpu_events'][2]['t']=float('nan')
        with self.assertRaisesRegex(ValueError,'non-finite JSON constant'):
            v._decode_json(json.dumps(a))
        # Direct Python objects must fail the same way, even without JSON parsing.
        with self.assertRaisesRegex(ValueError,'non-finite'):verify(a)

    def test_infinity_timestamp_rejected(self):
        a=synthetic();a['original_cpu_events'][2]['t']=float('inf')
        with self.assertRaisesRegex(ValueError,'non-finite'):verify(a)

    def test_boolean_timestamp_rejected(self):
        a=synthetic();a['original_cpu_events'][2]['t']=True
        with self.assertRaisesRegex(ValueError,'boolean'):verify(a)

    def test_decreasing_timestamp_rejected(self):
        a=synthetic();a['original_cpu_events'][3]['t']=-4
        with self.assertRaisesRegex(ValueError,'monotonic'):verify(a)

    def test_pp_actor_distinct_addresses(self):
        a=synthetic();a['original_cpu_events'][1]['pp_addr']=a['original_cpu_events'][0]['pp_addr']
        with self.assertRaisesRegex(ValueError,'addresses overlap'):verify(a)

    def test_wrong_state_word(self):
        a=synthetic();a['original_cpu_events'][3]['state_word']='0x2'
        with self.assertRaisesRegex(ValueError,'state-load'):verify(a)

    def test_wrong_terminal_r4_mask(self):
        a=synthetic();a['original_cpu_events'][4]['r4']='0x4'
        with self.assertRaisesRegex(ValueError,'state word/mask'):verify(a)

    def test_missing_foe_pp(self):
        a=synthetic();a['original_cpu_events'][0]['r0']='0x0'
        with self.assertRaisesRegex(ValueError,'missing player and foe'):verify(a)

    def test_wrong_rom_identity(self):
        a=synthetic();a['rom_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'recorded exact'):verify(a)

    def test_incomplete_trailing_events_excluded(self):
        a=synthetic();a['original_cpu_events'].append({'pc':v.PP,'t':25,'main':2,'r0':'0x0','after_pc':'0x809e6bc','pp_addr':'0x2001ef1','before':20,'after':19})
        r=verify(a);self.assertEqual(r['complete_cpu_episodes'],2);self.assertEqual(r['trailing_incomplete_events'],1)

    def test_no_single_episode_promotion(self):
        with self.assertRaisesRegex(ValueError,'at least two'):verify(synthetic(cycles=1))

    def test_non_dict_is_value_error(self):
        with self.assertRaisesRegex(ValueError,'JSON object'):v.verify_capture([], 'GDB S02')

    def test_console_required_on_cli(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'capture.json';p.write_text(json.dumps(synthetic()))
            cmd=[sys.executable,str(pathlib.Path(v.__file__)),str(p),'--normalize-legacy']
            proc=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertIn('--console',proc.stderr)

    def test_cli_explicit_relaxed_and_full_modes(self):
        for mode in ('v3-basic','v4-branch','v5-full'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
                raw=synthetic(mode);t=pathlib.Path(td)
                p=t/'capture.json';q=t/'console.txt';p.write_text(json.dumps(raw));q.write_text(console_for(raw))
                proc=subprocess.run([sys.executable,str(pathlib.Path(v.__file__)),str(p),'--console',str(q),'--mode',mode,'--normalize-legacy'],capture_output=True,text=True)
                self.assertEqual(proc.returncode,0,proc.stderr)
                r=json.loads(proc.stdout)
                self.assertEqual(r['mode'],mode)
                self.assertFalse(r['same_emulator_process_log'])



    def test_wrong_instrumented_pid_rejected(self):
        raw=synthetic();log=console_for(raw);run_id='native-run-unique-001'
        log=log.replace('GDB S02\n','RUN_START '+run_id+' pid=43210 start=1700000000.25\n',1)
        cap=v.normalize_legacy_archive(raw,console_for(raw))
        cap['run']={'run_id':run_id,'start_marker':'RUN_START '+run_id+' pid=43210 start=1700000000.25',
                    'console_sha256':v.hashlib.sha256(log.encode()).hexdigest(),
                    'provenance':'INSTRUMENTED_RUN','process_id_observed':True,
                    'pid':43211,'started_epoch':1700000000.25,'initial_save_sha256':SAVE}
        for e in cap['original_cpu_events']:e['run_id']=run_id
        with self.assertRaisesRegex(ValueError,'instrumented run needs matching'):
            v.verify_capture(cap,log)

    def test_wrong_instrumented_start_time_rejected(self):
        raw=synthetic();log=console_for(raw);run_id='native-run-unique-001'
        log=log.replace('GDB S02\n','RUN_START '+run_id+' pid=43210 start=1700000000.25\n',1)
        cap=v.normalize_legacy_archive(raw,console_for(raw))
        cap['run']={'run_id':run_id,'start_marker':'RUN_START '+run_id+' pid=43210 start=1700000000.25',
                    'console_sha256':v.hashlib.sha256(log.encode()).hexdigest(),
                    'provenance':'INSTRUMENTED_RUN','process_id_observed':True,
                    'pid':43210,'started_epoch':1700000001.25,'initial_save_sha256':SAVE}
        for e in cap['original_cpu_events']:e['run_id']=run_id
        with self.assertRaisesRegex(ValueError,'instrumented run needs matching'):
            v.verify_capture(cap,log)

    def test_post_save_modified_rejected(self):
        raw=synthetic()
        log=console_for(raw).replace(SAVE, '0'*64)
        with self.assertRaisesRegex(ValueError,'post-save hash differs'):
            verify(raw,console=log)

    def test_recorded_initial_save_mismatch_rejected(self):
        raw=synthetic();log=console_for(raw);cap=v.normalize_legacy_archive(raw,log)
        cap['save_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'capture save SHA metadata'):
            v.verify_capture(cap,log)

    def test_unknown_breakpoint_refused(self):
        raw=synthetic();log=console_for(raw).replace('BP 0x808e336 OK','BP 0x2000000 OK')
        with self.assertRaisesRegex(ValueError,'unknown debugger breakpoint'):
            verify(raw,console=log)

    def test_unknown_snap_name_refused(self):
        raw=synthetic();log=console_for(raw).replace('SNAP title','SNAP load_savestate')
        with self.assertRaisesRegex(ValueError,'unknown host console line'):
            verify(raw,console=log)

    def test_known_original_snap_labels_are_allowed(self):
        raw=synthetic();log=console_for(raw).replace('SNAP title\n',
            'SNAP title\nSNAP continue_loaded\nSNAP movement_2\nSNAP stop_25\nSNAP finished\n')
        r=verify(raw,console=log)
        self.assertTrue(r['snap_names_allowlisted'])
        self.assertTrue(r['breakpoint_addresses_allowlisted'])

    def test_consistent_mixed_v3_v5_cpu_stream_rejected_in_full_mode(self):
        # A forged single-start console and EVENTS count are NOT sufficient to
        # reclassify a v3 (no state load/terminal) episode as v5 grade.
        v3=synthetic('v3-basic',cycles=1)
        v5=synthetic('v5-full',cycles=1)
        mixed=deepcopy(v3)
        late=deepcopy(v5['original_cpu_events'])
        for e in late:e['t']+=10
        mixed['original_cpu_events']+=late
        log=console_for(mixed)
        with self.assertRaisesRegex(ValueError,'missing mandatory original CPU stage'):
            verify(mixed,mode='v5-full',console=log)

    def test_intentionally_forged_consistent_two_v5_episodes_cannot_be_detected(self):
        # Explicit documented limitation: the verifier validates consistency,
        # not hardware/OS authenticity of a coherent attacker-crafted transcript.
        fabricated=synthetic('v5-full')
        result=verify(fabricated)
        self.assertFalse(result['same_emulator_process_log'])
        self.assertEqual(result['complete_cpu_episodes'],2)
        self.assertEqual(result['original_rom_identity'].split(';')[0],
                         'RECORDED_HASH_FIELD_PLUS_GDB_POST_HASH')

    def test_direct_json_nan_isfinite_defense_in_depth(self):
        raw=synthetic();raw['original_cpu_events'][3]['t']=float('nan')
        with self.assertRaisesRegex(ValueError,'non-finite'):
            verify(raw)

if __name__=='__main__':unittest.main()
