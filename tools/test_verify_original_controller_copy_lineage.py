"""Synthetic-only fail-closed original CPU copier/PP temporal marker contract."""
import copy
import json
import unittest

from verify_original_controller_copy_lineage import audit, EXACT_ROM

SAVE = '8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
RUN = 'native-' + 'a' * 32
SHA = '9' * 64


def fixture():
    def item(t, pc, **fields):return {'t':float(t),'pc':pc,'after_pc':'0x8070000',**fields}
    candidate=[
      item(10,'0x806bd80',r0='0x0',r2='0xa'),
      item(10.5,'0x806b370',r0='0x0',r1='0x1',r3='0x6',candidate_actor0_reply_copy_entry=True,source_ptr='0x201cf94',source6_sha256=SHA),
      item(11,'0x806b3a6',r1='0x6',r2='0x6',r4='0x201cf94',candidate_six_byte_copy_epilogue=True,copy_source='0x201cf94',copy_destination='0x201c794',source6_sha256=SHA,destination6_sha256=SHA,bytes_equal_at_epilogue=True,after_pc='0x806b3a8'),
      item(12,'0x8094330'),item(12.5,'0x809435c'),item(13,'0x8094374'),item(13.5,'0x8094380'),
    ]
    core=[item(17,'0x809e6ba',r0='0x0',pp_addr='0x2001ef1',before=20,after=19,after_pc='0x809e6bc'),
          item(18,'0x808e336',before=2,after=0,store_addr='0x3005a0d')]
    c={'rom_sha256':EXACT_ROM,'save_sha256':SAVE,'run_id':RUN,'candidate_cpu_events':candidate}
    p={'rom_sha256':EXACT_ROM,'save_sha256':SAVE,'original_cpu_events':core}
    return c,p


def transcript(c,p,late_key=False,spliced=False,save=SAVE):
    lines=['GDB S02',f'RUN_START {c["run_id"]} pid=300 start=1234.5', 'KEY x 0.1','KEY Left 1.2']
    if late_key:lines.append('KEY x 2.0')
    allrows=[(e['t'],'COPY_CANDIDATE_STOP '+json.dumps(e,sort_keys=True)) for e in c['candidate_cpu_events']]
    allrows += [(e['t'],'STOP '+json.dumps(e,sort_keys=True)) for e in p['original_cpu_events']]
    lines += [line for _,line in sorted(allrows)]
    if spliced:lines.append('STOP '+json.dumps({'fake':'row'}))
    lines += [f'EVENTS {len(p["original_cpu_events"])}',f'COPY_CANDIDATES {len(c["candidate_cpu_events"])}',
              "RECEIPT_NOT_VALIDATED ValueError('needs at least two complete CPU episodes in one console')",
              f'ORIGINAL_POST_HASH {EXACT_ROM} {save}']
    return '\n'.join(lines)+'\n'


class OriginalCPUCopy(unittest.TestCase):
    def setUp(self):
        self.c,self.p=fixture()

    def check_fails(self,why,*,console=None):
        with self.assertRaisesRegex(ValueError,why):audit(self.c,self.p, transcript(self.c,self.p) if console is None else console)

    def test_good_is_candidate_only_and_not_native_cert(self):
        r=audit(self.c,self.p,transcript(self.c,self.p))
        self.assertEqual(len(r['ordered_candidate_chains']),1)
        self.assertEqual(r['player0_6_byte_copies'],1)
        self.assertEqual(r['formal_native_gameplay_acceptance'],'0/20')
        self.assertEqual(r['one_use_engine_request_ownership'],'NOT_PROVEN')

    def test_wrong_rom_hash_refused(self):
        self.c['rom_sha256']='0'*64
        self.check_fails('ROM hash mismatch')

    def test_cross_session_marker_refused(self):
        self.c['run_id']='native-'+'b'*32
        console=transcript(self.c,self.p).replace('RUN_START native-'+'b'*32,'RUN_START native-'+'c'*32)
        self.check_fails('run ID disagrees',console=console)

    def test_late_host_battle_confirm_refused(self):
        self.check_fails('host battle confirm',console=transcript(self.c,self.p,late_key=True))

    def test_stitched_console_stop_rejected(self):
        self.check_fails('transcript mismatch',console=transcript(self.c,self.p,spliced=True))

    def test_post_hash_mismatch_refused(self):
        self.check_fails('post-run',console=transcript(self.c,self.p,save='0'*64))

    def test_wrong_destination_hash_refused(self):
        self.c['candidate_cpu_events'][2]['destination6_sha256']='0'*64
        self.check_fails('six-byte response copy')

    def test_mismatched_copy_source_pointer_refused(self):
        self.c['candidate_cpu_events'][2]['r4']='0x201cf90'
        self.check_fails('six-byte response copy')

    def test_wrong_copy_loop_count_refused(self):
        self.c['candidate_cpu_events'][2]['r1']='0x5'
        self.check_fails('six-byte response copy')

    def test_entry_not_player_actor_refused(self):
        self.c['candidate_cpu_events'][1]['r0']='0x1'
        self.check_fails('six-byte response copy')

    def test_no_emitter_refused(self):
        self.c['candidate_cpu_events'][0]['r2']='0x0'
        self.check_fails('ordered same-run actor0')

    def test_commit_marker_missing_refused(self):
        self.c['candidate_cpu_events'][4]['pc']='0x809435a'
        self.check_fails('ordered same-run actor0')

    def test_player_pp_actor_wrong_refused(self):
        self.p['original_cpu_events'][0]['r0']='0x1'
        self.check_fails('ordered same-run actor0')

    def test_player_pp_no_decrement_refused(self):
        self.p['original_cpu_events'][0]['after']=20
        self.check_fails('ordered same-run actor0')

    def test_clear_wrong_before_refused(self):
        self.p['original_cpu_events'][1]['before']=0
        self.check_fails('ordered same-run actor0')

    def test_invalid_clock_nan_refused(self):
        self.c['candidate_cpu_events'][0]['t']=float('nan')
        self.check_fails('non-monotonic or invalid')

    def test_boolean_timestamp_refused(self):
        self.c['candidate_cpu_events'][0]['t']=True
        self.check_fails('non-monotonic or invalid')

    def test_original_rows_out_of_time_order_refused(self):
        self.c['candidate_cpu_events'][2]['t']=9.0
        self.check_fails('non-monotonic or invalid')

    def test_missing_host_key_refused(self):
        console=transcript(self.c,self.p).replace('KEY Left 1.2\n','')
        self.check_fails('missing original menu/movement',console=console)

    def test_coherent_synthetic_is_not_proof_of_actual_cpu(self):
        report=audit(self.c,self.p,transcript(self.c,self.p))
        self.assertEqual(report['original_session_pid_proof'],'RECORDER_MARKER_ATTESTED_ONLY')
        self.assertEqual(report['source_lab_auto_execution'],'NOT_PROVEN')

if __name__=='__main__':unittest.main()
