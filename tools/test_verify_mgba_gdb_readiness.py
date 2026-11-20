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

    def test_feature_offer_is_strictly_allowlisted(self):
        self.assertEqual(m.FEATURE_QUERY, 'qSupported:swbreak+;hwbreak+')
        class NoIO:
            def sendall(self, *a): raise AssertionError('must refuse unexpected command')
        for cmd in ('qSupported', 'qSupported:hwbreak+', 'qSupported:swbreak+',
                    'qSupported:swbreak+;hwbreak+;vContSupported+',
                    'Z1,08000100,2', 's', 'c'):
            with self.subTest(cmd=cmd), self.assertRaises(m.PreflightError):
                m.readonly_rsp(NoIO(), cmd)

    def test_supported_features_exact_positive(self):
        reply='swbreak+;hwbreak+;qXfer:features:read+;qXfer:memory-map:read+;QStartNoAckMode+'
        self.assertEqual(m.validate_supported_breakpoint_features(reply)[:2],
                         ('swbreak+', 'hwbreak+'))

    def test_missing_and_contradictory_features_fail_closed(self):
        for reply in ('', 'S02', 'E07', 'hwbreak+', 'swbreak+',
                      'swbreak+;hwbreak-', 'swbreak-;hwbreak+',
                      'swbreak+;hwbreak+;hwbreak-',
                      'swbreak+;hwbreak+;swbreak+',
                      'swbreak+;hwbreak+;', 'swbreak+;;hwbreak+'):
            with self.subTest(reply=reply), self.assertRaises(m.PreflightError):
                m.validate_supported_breakpoint_features(reply)

    def test_genuine_rsp_feature_negotiation_framing(self):
        peer,client=socket.socketpair()
        try:
            client.settimeout(2)
            def server():
                req=peer.recv(512)
                payload=m.FEATURE_QUERY.encode('ascii')
                assert req==b'$'+payload+(b'#%02x'%(sum(payload)&255)), req
                body=b'swbreak+;hwbreak+;qXfer:features:read+;QStartNoAckMode+'
                peer.sendall(b'+$'+body+(b'#%02x'%(sum(body)&255)))
                assert peer.recv(1)==b'+'
            t=threading.Thread(target=server);t.start()
            response=m.negotiate_breakpoint_features(client)
            self.assertIn('swbreak+',response)
            self.assertIn('hwbreak+',response)
            t.join(2)
            self.assertFalse(t.is_alive())
        finally:peer.close();client.close()

    def test_z1_hardware_stop_and_exact_pc_only(self):
        regs=['00000000']*17
        regs[15]=(0x08000100).to_bytes(4,'little').hex()
        value=m.require_exact_z1_stop('T05hwbreak:;', ''.join(regs), 0x08000100)
        self.assertEqual(value,{'reason':'hwbreak','pc':0x08000100})

    def test_z1_s05k_is_inconclusive_even_with_matching_pc(self):
        regs=['00000000']*17
        regs[15]=(0x08000100).to_bytes(4,'little').hex()
        with self.assertRaisesRegex(m.InconclusiveStop,'S05k'):
            m.require_exact_z1_stop('S05k',''.join(regs),0x08000100)

    def test_other_stop_reasons_fail_closed(self):
        regs=['00000000']*17
        regs[15]=(0x08000100).to_bytes(4,'little').hex()
        for stop in ('S05','T05swbreak:;', 'T05watch:02000000;',
                     'T05hwbreak:;extra','T05hwbreak:', 'T05', '', 'S02', 'T05hwbreak:;\x00'):
            with self.subTest(stop=stop), self.assertRaises(m.InconclusiveStop):
                m.require_exact_z1_stop(stop, ''.join(regs), 0x08000100)

    def test_z1_wrong_pc_fails_closed(self):
        regs=['00000000']*17
        regs[15]=(0x08000102).to_bytes(4,'little').hex()
        with self.assertRaisesRegex(m.InconclusiveStop,'PC mismatch'):
            m.require_exact_z1_stop('T05hwbreak:;', ''.join(regs), 0x08000100)

    def test_z1_missing_or_malformed_registers_fails_closed(self):
        for bad in ('', '0'*128, 'Z'*136, '0'*137, None):
            with self.subTest(bad=repr(bad)), self.assertRaises(m.InconclusiveStop):
                m.require_exact_z1_stop('T05hwbreak:;',bad,0x08000100)

    def test_z1_expected_pc_cannot_be_odd_or_out_of_rom(self):
        regs='0'*136
        for bad in (True, -1, 0x08000101, 0x02000000, 0x0a000000):
            with self.subTest(bad=bad), self.assertRaises(m.PreflightError):
                m.require_exact_z1_stop('T05hwbreak:;',regs,bad)

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
