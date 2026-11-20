#!/usr/bin/env python3
"""No-game, deterministic tests for isolated PR #152 Xlib hardening."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

SRC=Path(__file__).with_name('verify_mgba_qt_focus.py')
spec=importlib.util.spec_from_file_location('hardened_qt_focus',SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class HardenedObserverTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='sg_xlib_unit_')
        self.addCleanup(self.temp.cleanup)
        self.auth=str(Path(self.temp.name)/'Xauthority')
        Path(self.auth).touch(mode=0o600)
        self.display=':199'
        self.env=mock.patch.dict(os.environ,{'DISPLAY':self.display,'XAUTHORITY':self.auth})
        self.env.start();self.addCleanup(self.env.stop)
        self.good={'status':'PASS','window_id':9876,'title':'mGBA - 0.10.5',
                   'class':['mgba-qt','mGBA'],'map_state':2,'dimensions':[480,343],
                   'title_changed':False,'focus_verified':True,'dialog_verified':False}

    def test_credentials_private_exact(self):
        self.assertEqual(m.require_parent_x11(self.display,self.auth),(self.display,self.auth))

    def test_parent_display_mismatch_refused(self):
        with self.assertRaisesRegex(m.ObserverError,'disagree'):
            m.require_parent_x11(':200',self.auth)

    def test_parent_auth_mismatch_refused(self):
        with self.assertRaisesRegex(m.ObserverError,'disagree'):
            m.require_parent_x11(self.display,'/tmp/other')

    def test_untrusted_display_refused(self):
        for value in ('localhost:5','ssh:10',':1;rm -rf /','',None):
            with self.subTest(value=value),self.assertRaises(m.ObserverError):
                m.require_parent_x11(value,self.auth)

    def test_non_private_xauthority_refused(self):
        os.chmod(self.auth,0o644)
        with self.assertRaisesRegex(m.ObserverError,'private regular file'):
            m.require_parent_x11(self.display,self.auth)

    def test_symlink_xauthority_refused(self):
        link=str(Path(self.temp.name)/'linked')
        os.symlink(self.auth,link)
        os.environ['XAUTHORITY']=link
        with self.assertRaisesRegex(m.ObserverError,'private regular file'):
            m.require_parent_x11(self.display,link)

    def call(self,result=None,returncode=0):
        if result is None:result=self.good
        proc=subprocess.CompletedProcess(['test'],returncode,stdout=json.dumps(result),stderr='')
        with mock.patch.object(m.subprocess,'run',return_value=proc) as patched:
            out=m.call_isolated_xlib(self.display,self.auth)
            args,kwargs=patched.call_args
            self.assertEqual(kwargs['env']['DISPLAY'],self.display)
            self.assertEqual(kwargs['env']['XAUTHORITY'],self.auth)
            self.assertTrue(kwargs['start_new_session'])
            self.assertNotIn('shell',kwargs)
            self.assertLessEqual(kwargs['timeout'],15)
            return out

    def test_parent_accepts_strict_helper_result(self):
        self.assertEqual(self.call(),self.good)

    def test_simulated_helper_sigsegv_is_inconclusive(self):
        p=subprocess.CompletedProcess([], -11, '', '')
        with mock.patch.object(m.subprocess,'run',return_value=p):
            with self.assertRaisesRegex(m.ObserverError,'exit=-11'):
                m.call_isolated_xlib(self.display,self.auth)

    def test_helper_timeout_is_inconclusive(self):
        with mock.patch.object(m.subprocess,'run',side_effect=subprocess.TimeoutExpired('child',8)):
            with self.assertRaisesRegex(m.ObserverError,'timeout'):
                m.call_isolated_xlib(self.display,self.auth)

    def test_malformed_json_is_inconclusive(self):
        p=subprocess.CompletedProcess([],0,'broken-json','')
        with mock.patch.object(m.subprocess,'run',return_value=p):
            with self.assertRaisesRegex(m.ObserverError,'invalid isolated helper output'):
                m.call_isolated_xlib(self.display,self.auth)

    def test_not_ready_only_pre_window_is_inconclusive(self):
        p=subprocess.CompletedProcess([],0,json.dumps({'status':'NOT_READY'}),'')
        with mock.patch.object(m.subprocess,'run',return_value=p):
            with self.assertRaisesRegex(m.ObserverError,'not yet available'):
                m.call_isolated_xlib(self.display,self.auth)

    def test_invalid_identity_refused(self):
        for changes in ({'title':'mGBA'}, {'title':'mGBA - 0.10.4'}, {'class':['unknown','mGBA']},
                        {'map_state':0},{'dimensions':[1,1]}, {'focus_verified':False},
                        {'window_id':0},{'window_id':'fake'},{'status':'NOT_READY'},
                        {'title_changed':True}):
            val={**self.good,**changes}
            p=subprocess.CompletedProcess([],0,json.dumps(val),'')
            with mock.patch.object(m.subprocess,'run',return_value=p):
                with self.subTest(changes=changes),self.assertRaises(m.ObserverError):
                    m.call_isolated_xlib(self.display,self.auth)

    def test_bounded_arguments(self):
        with self.assertRaisesRegex(m.ObserverError,'invalid bounded helper'):
            m.call_isolated_xlib(self.display,self.auth,timeout=20)

    def test_close_idempotently_restores_prior_handler(self):
        class FakeX:
            def __init__(self):self.calls=[]
            def XSync(self,*args):self.calls.append('sync')
            def XCloseDisplay(self,*args):self.calls.append('close')
            def XSetErrorHandler(self,*args):self.calls.append('restore')
        x=FakeX()
        client=object.__new__(m.XClient)
        client.x=x;client.dpy=234;client._handler=object();client._old_handler=567
        client._closed=False
        client.close();client.close()
        self.assertEqual(x.calls,['sync','close','restore'])
        self.assertIsNone(client._handler)

    def test_ctrl_o_dialog_preserves_original_key_sequence(self):
        calls=[]
        class FakeClient:
            def key(self,name,down): calls.append((name,down))
            def windows(self):
                return [{'name':'Select ROM','map_state':2,'width':480,'height':320}]
        self.assertTrue(m.XClient.open_dialog(FakeClient()))
        self.assertEqual(calls,[('Control_L',True),('o',True),('o',False),('Control_L',False)])

    def test_ctrl_o_always_releases_control_on_key_failure(self):
        calls=[]
        class FakeClient:
            def key(self,name,down):
                calls.append((name,down))
                if name=='o' and down: raise m.ObserverError('failed o key')
        with self.assertRaisesRegex(m.ObserverError,'failed o key'):
            m.XClient.open_dialog(FakeClient())
        self.assertEqual(calls[-1],('Control_L',False))

    def test_ctrl_o_does_not_accept_multiple_or_hidden_dialogs(self):
        class FakeClient:
            def key(self,name,down): pass
            def windows(self):
                return [{'name':'Select ROM','map_state':0,'width':480,'height':320},
                        {'name':'Select ROM','map_state':2,'width':1,'height':1}]
        with mock.patch.object(m.time,'sleep',return_value=None):
            with self.assertRaisesRegex(m.ObserverError,'Ctrl\\+O'):
                m.XClient.open_dialog(FakeClient())
        class Multiple(FakeClient):
            def windows(self):
                return [{'name':'Select ROM','map_state':2,'width':400,'height':300}]*2
        with mock.patch.object(m.time,'sleep',return_value=None):
            with self.assertRaisesRegex(m.ObserverError,'exactly one'):
                m.XClient.open_dialog(Multiple())

    def test_dialog_request_sent_only_when_requested(self):
        p=subprocess.CompletedProcess([],0,json.dumps({**self.good,'dialog_verified':True,
                                                       'title_changed':True,
                                                       'title':'mGBA - TEST (45.3 fps) - 0.10.5'}),'')
        with mock.patch.object(m.subprocess,'run',return_value=p) as run:
            out=m.call_isolated_xlib(self.display,self.auth,simulate_title=True,verify_dialog=True)
        self.assertTrue(out['dialog_verified'])
        args,kwargs=run.call_args
        self.assertIn('--verify-dialog',args[0])
        self.assertIn('--simulate-title',args[0])
        self.assertEqual(kwargs['env']['XAUTHORITY'],self.auth)

    def test_dialog_positive_cannot_be_forged_in_non_dialog_run(self):
        p=subprocess.CompletedProcess([],0,json.dumps({**self.good,'dialog_verified':True}),'')
        with mock.patch.object(m.subprocess,'run',return_value=p):
            with self.assertRaisesRegex(m.ObserverError,'identity checks'):
                m.call_isolated_xlib(self.display,self.auth)

    def test_dialog_missing_result_rejected(self):
        p=subprocess.CompletedProcess([],0,json.dumps({k:v for k,v in self.good.items()
                                                        if k!='dialog_verified'}),'')
        with mock.patch.object(m.subprocess,'run',return_value=p):
            with self.assertRaisesRegex(m.ObserverError,'schema'):
                m.call_isolated_xlib(self.display,self.auth)

    def test_dialog_validation_keeps_original_title_rules(self):
        for title in ('mGBA','Qt Selection Owner for mGBA',
                      'mGBA - POKEMON EMER - 0.10.4','mGBA - (45.3 fps) - 0.10.5'):
            self.assertIsNone(m.MAIN_TITLE.fullmatch(title))
        self.assertIsNotNone(m.MAIN_TITLE.fullmatch('mGBA - TEST (45.3 fps) - 0.10.5'))

    def test_forbidden_source_patterns_absent(self):
        src=SRC.read_text()
        self.assertIn('def open_dialog(self):',src)
        self.assertIn('verify_dialog=True',src)
        self.assertIn("'XAUTHORITY':authority",src)
        self.assertIn('start_new_session=True',src)
        self.assertNotIn('import mgba',src)
        self.assertNotIn('mDebuggerRunFrame',src)

    def test_no_rom_or_debugger_cli(self):
        result=subprocess.run([os.sys.executable,str(SRC),'--rom','private.gba'],
                              capture_output=True,text=True,timeout=3)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('unrecognized arguments',result.stderr)

if __name__=='__main__':unittest.main(verbosity=2)
