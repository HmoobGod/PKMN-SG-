#!/usr/bin/env python3
"""Pure synthetic, deterministic GDB readiness and fail-closed regression tests."""
import importlib.util
import io
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest

SOURCE = Path(__file__).with_name("verify_mgba_gdb_readiness.py")
spec = importlib.util.spec_from_file_location("sg_rsp_readiness", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Process:
    def __init__(self, value=None): self.value=value
    def poll(self): return self.value

class FixtureTests(unittest.TestCase):
    def test_pinned_public_fixture(self):
        b=m.generated_fixture()
        self.assertEqual(len(b),32768)
        self.assertEqual(b[0xc0:0xc4],bytes.fromhex('00009fe5'))
        self.assertEqual(b[0x100:0x102],bytes.fromhex('fee7'))

    def test_preconnect_refused_then_success(self):
        seen=[];marker=object()
        def dial(*a,**kw):
            seen.append(1)
            if len(seen)<3:raise ConnectionRefusedError(111,'refused')
            return marker
        v,n=m.connect_until_listening(Process(), timeout=4, dial=dial)
        self.assertIs(v,marker);self.assertEqual(n,3)

    def test_preconnect_aborted_then_success(self):
        seen=[];marker=object()
        def dial(*a,**kw):
            seen.append(1)
            if len(seen)==1:raise ConnectionAbortedError(103,'aborted')
            return marker
        v,n=m.connect_until_listening(Process(), timeout=3, dial=dial)
        self.assertIs(v,marker);self.assertEqual(n,2)

    def test_unexpected_preconnect_error_fails(self):
        def dial(*a,**kw):raise PermissionError(13,'denied')
        with self.assertRaises(m.PreflightError):m.connect_until_listening(Process(),timeout=1,dial=dial)

    def test_process_exit_fails_before_tcp(self):
        with self.assertRaisesRegex(m.PreflightError,'emulator exited'):
            m.connect_until_listening(Process(5),timeout=1,dial=lambda *a,**kw:None)

    def test_refusal_deadline_fails(self):
        def dial(*a,**kw):raise ConnectionRefusedError(111,'refused')
        with self.assertRaisesRegex(m.PreflightError,'deadline'):
            m.connect_until_listening(Process(),timeout=.2,dial=dial)

    def test_disallowed_rsp_never_sent(self):
        class NoIO:
            def sendall(self,*a):raise AssertionError('cannot send')
        for cmd in ('c','G','M08000000,2','Z0,08000100,2','qRcmd,6162','m02000000,4'):
            with self.subTest(cmd=cmd),self.assertRaises(m.PreflightError):
                m.readonly_rsp(NoIO(),cmd)

    def test_valid_rsp_ack_packet_checksum(self):
        peer,client=socket.socketpair()
        try:
            def server():
                req=peer.recv(512)
                assert req==b'$?#3f',req
                body=b'S02'
                peer.sendall(b'+$'+body+(b'#%02x'%(sum(body)&255)))
                assert peer.recv(1)==b'+'
            t=threading.Thread(target=server);t.start()
            self.assertEqual(m.readonly_rsp(client,'?'),'S02')
            t.join(2);self.assertFalse(t.is_alive())
        finally:peer.close();client.close()

    def test_bad_ack_fails_closed(self):
        peer,client=socket.socketpair()
        try:
            peer.sendall(b'-')
            with self.assertRaisesRegex(m.PreflightError,'ACK'):m.readonly_rsp(client,'?')
        finally:peer.close();client.close()

    def test_bad_checksum_fails_closed(self):
        peer,client=socket.socketpair()
        try:
            peer.sendall(b'+$S02#00')
            with self.assertRaisesRegex(m.PreflightError,'checksum'):m.readonly_rsp(client,'?')
        finally:peer.close();client.close()

    def test_eof_after_ack_fails_closed(self):
        peer,client=socket.socketpair()
        try:
            peer.sendall(b'+')
            peer.close()
            with self.assertRaisesRegex(m.PreflightError,'RSP transport failed|socket closed'):m.readonly_rsp(client,'?')
        finally:client.close()

    def test_wrong_appimage_size_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'mGBA-0.10.5-appimage-x64.appimage'
            f.write_bytes(b'not an appimage')
            with self.assertRaisesRegex(m.PreflightError,'size mismatch'):
                m.verify_host(f,SOURCE)

    def test_rom_cli_argument_rejected(self):
        p=subprocess.run([sys.executable,str(SOURCE),'--appimage','fixture','--rom','private.gba'],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=2)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('unrecognized arguments',p.stderr)

if __name__=='__main__':unittest.main(verbosity=2)
