#!/usr/bin/env python3
"""PUBLIC synthetic regressions for R14 original second-turn auto refusal and manual
fallback after a privately verified fixture-only first ROM-resident auto action.
No private gameplay binaries/states/requests or real emulation in this CI suite.
"""
import copy
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_private_r14_second_turn import verify_r14, BadTrace, LAB_SHA, SAVE_SHA, STATES, FIRST_SHA
from test_private_r13_in_rom import sample_positive


def event(pc, frame, **other):
    v={'pc':pc,'frame':frame,'r0':0,'r1':0,'r2':0,'r3':0,'r4':0,'r6':0,
       'pending':0,'reply_valid':0,'reply_payload':0}
    v.update(other)
    return v


def fixture():
    # Public synthetic sample, NOT original user request content or original
    # game observation. The full 44-byte sha check is disabled in tests only.
    req=bytearray(44)
    req[0]=19
    for i,m in enumerate((325,157,92,269)):
        req[4+2*i:6+2*i]=m.to_bytes(2,'little')
    req[12:16]=bytes((20,9,10,20))
    hx=req.hex()
    return {'schema':'sg16266-r14-second-live-request-manual-fallback-v1',
        'candidate_rom_sha256':LAB_SHA,'save_sha256':SAVE_SHA,
        'precontroller_state_sha256':sorted(STATES)[0],
        'first_original_auto_accepted':True,'first_original_auto_move':157,
        'first_r13_witness':sample_positive(), 'first_request_sha256':FIRST_SHA,
        'second_request_sha256':hashlib.sha256(req).hexdigest(),
        'second_copy_stores':44,'second_pending_steps':23,'second_live_moves':[325,157,92,269],
        'second_live_request_moves':[325,157,92,269],'second_live_pp':[20,9,10,20],
        'second_request_frame':10,
        'second_copy_witness':{'source_before_hex':hx,'source_after_hex':hx,
            'dest_after_hex':hx,'store_values_hex':hx,
            'store_indices':list(range(44)),'actor':0,'direction':0,'length':44,
            'post_pc':'0x806b3c6'},
        'post_first_turn_windows':[
            {'kind':1,'start':6,'end':9,'pc':'0x188','pp':[20,10],'steps':10000,'pending':0},
            {'kind':2,'start':9,'end':10,'pc':'0x806b372','pp':[20,9],'steps':9000,'pending':0}],
        'second_event_trace':[
            event('0x806b370',10,r0=1),event('0x9f2d000',10),
            event('0x9f20022',10,r0=0),event('0x806bd80',11,r0=1,r2=10),
            event('0x806449c',12,r0=0),event('0x806449c',13,r0=0)],
        'second_manual_events':[
            event('0x806449c',14,r0=0),event('0x806bd80',14,r0=0,r2=10,r3=257),
            event('0x806b370',14,r0=0,r1=1,r3=6,reply_valid=1,reply_payload=257),
            event('0x806261c',14,r4=0,pending=0),event('0x80e5e5c',15,r0=0,r6=0),
            event('0x8094330',15,r0=0,r6=0),event('0x809435c',15,r0=1,r6=0),
            event('0x8094374',15,r0=157,r6=0),event('0x8094380',15,r2=1,r6=0)],
        'second_auto_emissions':0,'second_original_manual_menu':True,
        'second_manual_accept_after_fallback':True,'manual_button_inputs_before_fallback':0,
        'manual_button_confirm_after_fallback':1,'general_owner_certified':False,
        'complete_move_legality':False,'complete_target_legality':False,
        'general_playable_auto':False,'formal_auto_suite_passes':0}


class TestR14(unittest.TestCase):
    def rejects(self,mutator):
        o=fixture()
        mutator(o)
        with self.assertRaises(BadTrace):
            verify_r14(o,require_original_sha=False)

    def test_sample_is_bounded_synthetic_only(self):
        result=verify_r14(fixture(),require_original_sha=False)
        self.assertEqual(result['in_rom_auto_submissions_total'],1)
        self.assertEqual(result['second_turn_auto_submissions'],0)
        self.assertEqual(result['formal_general_auto_acceptance'],0)
        self.rejects(lambda o:o.__setitem__('second_request_sha256',FIRST_SHA))
        with self.assertRaises(BadTrace):verify_r14(fixture()) # require original SHA by default

    def test_public_c11_observer_syntax(self):
        cc=shutil.which('cc')
        if not cc:self.skipTest('host C compiler unavailable')
        subprocess.run([cc,'-std=c11','-Wall','-Wextra','-Werror','-pedantic','-fsyntax-only',
            str(Path(__file__).with_name('trace_second_request.c'))],check=True,capture_output=True,text=True)

    def test_wrong_inputs_and_source_hashes(self):
        for field,value in [('candidate_rom_sha256','0'*64),('save_sha256','1'*64),
                            ('precontroller_state_sha256','2'*64),('schema','bogus')]:
            self.rejects(lambda o,f=field,v=value:o.__setitem__(f,v))

    def test_no_claims_of_general_authority(self):
        for field,value in [('general_owner_certified',True),('complete_move_legality',True),
            ('complete_target_legality',True),('general_playable_auto',True),
            ('formal_auto_suite_passes',1)]:
            self.rejects(lambda o,f=field,v=value:o.__setitem__(f,v))

    def test_first_live_auto_must_be_exactly_once(self):
        self.rejects(lambda o:o['first_r13_witness']['events'].pop(5))
        self.rejects(lambda o:o['first_r13_witness']['events'].append(copy.deepcopy(o['first_r13_witness']['events'][5])))
        self.rejects(lambda o:o['first_r13_witness'].__setitem__('lab_native_in_rom_auto_acceptance',0))
        self.rejects(lambda o:o.__setitem__('first_original_auto_accepted',False))

    def test_second_original_copy_is_byte_perfect(self):
        self.rejects(lambda o:o['second_copy_witness'].__setitem__('dest_after_hex','00'*44))
        self.rejects(lambda o:o['second_copy_witness'].__setitem__('store_indices',list(reversed(range(44)))))
        self.rejects(lambda o:o['second_copy_witness'].__setitem__('length',43))
        self.rejects(lambda o:o['second_copy_witness'].__setitem__('actor',1))
        self.rejects(lambda o:o['second_copy_witness'].__setitem__('direction',1))

    def test_second_request_and_pp_drift(self):
        self.rejects(lambda o:o.__setitem__('second_live_pp',[20,10,10,20]))
        self.rejects(lambda o:o.__setitem__('second_pending_steps',22))
        self.rejects(lambda o:o.__setitem__('second_live_request_moves',[325,157,92,0]))
        self.rejects(lambda o:o.__setitem__('second_copy_stores',43))
        self.rejects(lambda o:o['post_first_turn_windows'][-1].__setitem__('pp',[20,10]))
        self.rejects(lambda o:o['post_first_turn_windows'][-1].__setitem__('pending',1))

    def test_stale_or_missing_second_original_guard_denied(self):
        self.rejects(lambda o:o['second_event_trace'].pop(1))
        self.rejects(lambda o:o['second_event_trace'][2].__setitem__('r0',1))
        self.rejects(lambda o:o['second_event_trace'].reverse())
        self.rejects(lambda o:o['second_event_trace'].insert(3,event('0x8065eb4',11,r0=0)))

    def test_no_duplicate_or_premature_second_autocommand(self):
        self.rejects(lambda o:o['second_event_trace'].insert(3,event('0x806bd80',11,r0=0,r2=10,r3=257)))
        self.rejects(lambda o:o['second_event_trace'].insert(3,event('0x9f20022',11,r0=1)))
        self.rejects(lambda o:o.__setitem__('second_auto_emissions',1))
        self.rejects(lambda o:o['second_event_trace'].__setitem__(5,event('0x8094330',13,r0=0)))

    def test_manual_fallback_and_second_human_input(self):
        self.rejects(lambda o:o.__setitem__('second_original_manual_menu',False))
        self.rejects(lambda o:o.__setitem__('manual_button_inputs_before_fallback',1))
        self.rejects(lambda o:o.__setitem__('manual_button_confirm_after_fallback',0))
        self.rejects(lambda o:o.__setitem__('second_event_trace',[e for e in o['second_event_trace'] if e['pc']!='0x806449c']))
        self.rejects(lambda o:o['second_manual_events'].pop(1))

    def test_manual_reply_completion_commit(self):
        self.rejects(lambda o:o['second_manual_events'][2].__setitem__('reply_payload',256))
        self.rejects(lambda o:o['second_manual_events'][3].__setitem__('pending',1))
        self.rejects(lambda o:o['second_manual_events'][5].__setitem__('r0',2))
        self.rejects(lambda o:o['second_manual_events'][7].__setitem__('r0',325))
        self.rejects(lambda o:o['second_manual_events'][8].__setitem__('r2',0))

    def test_manual_must_not_be_mislabeled_new_auto(self):
        self.rejects(lambda o:o['second_manual_events'].insert(1,event('0x8065eb4',14,r0=0)))
        self.rejects(lambda o:o['second_manual_events'].insert(1,event('0x9f20022',14,r0=1)))
        self.rejects(lambda o:o['second_manual_events'].insert(1,event('0x806bd80',14,r0=0,r2=10,r3=257)))


if __name__ == '__main__':unittest.main(verbosity=2)