"""Synthetic-only RSP safety/denial tests. NO original emulator/ROM is executed."""
import hashlib
import json
import os
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import capture_original_request_rsp as m


def packet(data):
    return b'$'+data+b'#%02x' % (sum(data) & 255)


def registers(pc, r0=0, r1=1, r2=m.SRC_BASE, r3=6, r4=0, r6=0):
    values = [r0, r1, r2, r3, r4, 0, r6]+[0]*8+[pc]
    return b''.join(v.to_bytes(4, 'little') for v in values).hex().encode()


class FakeGDB:
    """Deliberately simplified fake stub. Cannot authenticate real mGBA RSP."""
    def __init__(self, stop_pcs=None, bias=0, hang=False, corrupted=None,
                 trunc=None, exit_stop=False, cleanup_fail=False, on_resume=None,
                 epilogue_dest=m.DST_PLAYER0, interrupt_responds=True,
                 stale_after_stop=False, keyboard_interrupt_once=False,
                 install_fail=False, pp_wrong_address=False, pp_r0=0,
                 step_pc_delta=2, double_interrupt_stop=False, rle_g=False,
                 entry_actors=None, disconnect_on=None, step_stop_reply=b'S05',
                 extra_g_cpsr=False, resume_stop_reply=b'S05',
                 qsupported_reply=m.PUBLIC_QSUPPORTED_REPLY):
        self.buf = bytearray()
        self.commands = []
        self.stop_pcs = list(stop_pcs or [m.COPY_ENTRY, m.COPY_POST_A, m.PP_WRITER, m.MAIN_CLEAR])
        self.bias = bias
        self.hang = hang
        self.corrupted = corrupted
        self.trunc = trunc
        self.exit_stop = exit_stop
        self.cleanup_fail = cleanup_fail
        self.on_resume = on_resume
        self.epilogue_dest = epilogue_dest
        self.interrupt_responds = interrupt_responds
        self.stale_after_stop = stale_after_stop
        self.keyboard_interrupt_once = keyboard_interrupt_once
        self.install_fail = install_fail
        self.pp_wrong_address = pp_wrong_address
        self.pp_r0 = pp_r0
        self.step_pc_delta = step_pc_delta
        self.double_interrupt_stop = double_interrupt_stop
        self.rle_g = rle_g
        self.entry_actors = dict(entry_actors or {})
        self.disconnect_on = disconnect_on
        self.step_stop_reply = step_stop_reply
        self.extra_g_cpsr = extra_g_cpsr
        self.resume_stop_reply = resume_stop_reply
        self.qsupported_reply = qsupported_reply
        self.timeouts = []
        self.n = 0
        self.stepped = False
        self.interrupts = 0
        self.nacks = 0
        self._corrupted_once = False
        self._truncated_once = False
        self.drift_bias = False

    def sendall(self, data):
        if data in (b'+', b'-'):
            if data == b'-':
                self.nacks += 1
            return
        if data == b'\x03':
            self.interrupts += 1
            if self.interrupt_responds:
                self.buf.extend(packet(b'S02'))
                if self.double_interrupt_stop:
                    self.buf.extend(packet(b'T05thread:1;'))
            return
        assert data.startswith(b'$') and b'#' in data
        request, crc = data[1:].rsplit(b'#', 1)
        assert int(crc, 16) == sum(request) & 255
        cmd = request.decode()
        self.commands.append(cmd)
        if cmd == m.PUBLIC_QSUPPORTED_COMMAND:
            response = self.qsupported_reply
        elif cmd == '?':
            response = b'S02'
        elif cmd.startswith('Z0,') or cmd.startswith('z0,'):
            response = b'ERR' if ((cmd.startswith('z0,') and self.cleanup_fail) or
                                   (cmd.startswith('Z0,') and self.install_fail)) else b'OK'
        elif cmd == 'c':
            self.n += 1
            self.stepped = False
            if self.on_resume and self.n == 1:
                self.on_resume()
            if self.hang:
                self.buf.extend(b'+')
                return
            response = b'W00' if self.exit_stop else self.resume_stop_reply
        elif cmd == 's':
            self.stepped = True
            response = self.step_stop_reply
        elif cmd == 'g':
            original_pc = self.stop_pcs[min(max(self.n-1,0), len(self.stop_pcs)-1)]
            observed_bias = 4 if self.drift_bias and self.n == 2 else self.bias
            if self.stepped:
                response = registers(original_pc+observed_bias+self.step_pc_delta, r1=m.PP_BASE, r6=19)
            elif original_pc == m.COPY_POST_A:
                response = registers(original_pc+observed_bias, r0=self.epilogue_dest,
                                     r1=6, r2=6, r4=m.SRC_BASE)
            elif original_pc == m.COPY_ENTRY:
                response = registers(original_pc+observed_bias,
                                     r0=self.entry_actors.get(self.n-1, 0))
            elif original_pc == m.PP_WRITER:
                response = registers(original_pc+observed_bias,
                                     r0=self.pp_r0,
                                     r1=0x03000100 if self.pp_wrong_address else m.PP_BASE, r6=19)
            else:
                response = registers(original_pc+observed_bias)
            if self.rle_g:
                response = b'00*xxx'
            elif self.extra_g_cpsr:
                response += (0x20).to_bytes(4,'little').hex().encode()
        elif cmd.startswith('m'):
            address, size = cmd[1:].split(',')
            address, size = int(address,16), int(size,16)
            assert m.permitted_memory(address,size)
            if address == m.PP_BASE and size == 1:
                response = b'13' if self.stepped else b'14'
            elif address == m.MAIN_BYTE:
                response = b'02'
            else:
                response = b'010203040506'[:size*2]
        else:
            raise AssertionError('unexpected debugger operation '+cmd)
        if self.disconnect_on == cmd:
            return  # Simulate a remote EOF before even sending an ACK.
        if self.corrupted == cmd and not self._corrupted_once:
            self._corrupted_once = True
            response_wire = b'$'+response+b'#00'
        elif self.trunc == cmd and not self._truncated_once:
            self._truncated_once = True
            response_wire = b'$'+response[:3]  # disconnect in middle of frame
        else:
            response_wire = packet(response)
        self.buf.extend(b'+' + response_wire)
        if cmd == 'c' and self.stale_after_stop and self.n == 1:
            self.buf.extend(packet(b'S05'))

    def recv(self, count):
        assert count == 1
        if not self.buf:
            if self.keyboard_interrupt_once:
                self.keyboard_interrupt_once = False
                raise KeyboardInterrupt('simulated operator interrupt')
            if self.hang:
                raise socket.timeout('no stop yet')
            return b''
        data = bytes(self.buf[:1])
        del self.buf[:1]
        return data

    def __enter__(self): return self
    def __exit__(self, *_): return False
    def settimeout(self, duration):
        self.timeout = duration
        self.timeouts.append(duration)


class CaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.rom, cls.save = cls.root/'original_input.gba', cls.root/'original_input.sav'
        cls.rom.write_bytes(b'A'*(32*1024*1024))
        cls.save.write_bytes(b'B'*131072)
        cls.rom_sha = hashlib.sha256(cls.rom.read_bytes()).hexdigest()
        cls.save_sha = hashlib.sha256(cls.save.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def run_fake(self, remote=None, **kwargs):
        remote = remote or FakeGDB()
        target = self.root/(self._testMethodName+'_'+str(len(list(self.root.glob(self._testMethodName+'*'))))+'.json')
        with patch.object(m,'EXACT_ROM',self.rom_sha), \
             patch.object(m,'EXACT_SAVE',self.save_sha), \
             patch.object(m.socket,'create_connection',return_value=remote):
            result = m.run_capture(self.rom,self.save,target,2345,**kwargs)
        return result, json.loads(target.read_text()), remote, target

    def test_narrow_send_whitelist(self):
        remote = FakeGDB(); rsp = m.RSP(remote)
        self.assertEqual(rsp.send('?'), b'S02')
        self.assertEqual(rsp.send(f'm{m.SRC_BASE:08x},6'), b'010203040506')
        for forbidden in ('M0201cf94,6:abcdef', 'G0000', 'P0=0','k','vRun','qRcmd,7265736574',
                          'm03000100,6','m02030000,6','m0201cf94,7','m0201cf99,2',
                          'Z0,08000000,2','z0,08000000,2','Z0,0806b370,4','c','s'):
            with self.assertRaises(ValueError, msg=forbidden): rsp.send(forbidden)
        self.assertEqual(remote.commands,['?',f'm{m.SRC_BASE:08x},6'])

    def test_public_qsupported_is_literal_fresh_optin_and_one_use(self):
        # Independently pin exact feature request/response, not a self-match.
        self.assertEqual(m.PUBLIC_QSUPPORTED_COMMAND,
                         "qSupported:swbreak+;hwbreak+")
        self.assertEqual(
            m.PUBLIC_QSUPPORTED_REPLY,
            b"swbreak+;hwbreak+;qXfer:features:read+;"
            b"qXfer:memory-map:read+;QStartNoAckMode+",
        )
        remote = FakeGDB()
        rsp = m.RSP(remote)
        with self.assertRaisesRegex(ValueError, "qSupported only allowed"):
            rsp.send(m.PUBLIC_QSUPPORTED_COMMAND)
        self.assertEqual(remote.commands, [])
        self.assertEqual(
            rsp.negotiate_public_breakpoint_capabilities(),
            m.PUBLIC_QSUPPORTED_REPLY,
        )
        self.assertEqual(remote.commands, [m.PUBLIC_QSUPPORTED_COMMAND])
        self.assertTrue(rsp._features_negotiated)
        with self.assertRaisesRegex(ValueError, "fresh stopped"):
            rsp.negotiate_public_breakpoint_capabilities()
        with self.assertRaisesRegex(ValueError, "qSupported only allowed"):
            rsp.send(m.PUBLIC_QSUPPORTED_COMMAND)
        self.assertEqual(rsp.send("?"), b"S02")
        self.assertEqual(remote.commands, [m.PUBLIC_QSUPPORTED_COMMAND, "?"])

    def test_public_qsupported_never_accepted_after_readonly_preflight(self):
        remote = FakeGDB()
        rsp = m.RSP(remote)
        self.assertEqual(rsp.send("?"), b"S02")
        with self.assertRaisesRegex(ValueError, "first on a fresh"):
            rsp.negotiate_public_breakpoint_capabilities()
        self.assertEqual(remote.commands, ["?"])

    def test_wrong_qsupported_reply_poison_session_fail_closed(self):
        for response in (b"", b"swbreak+", b"swbreak+;hwbreak-",
                         b"swbreak+;hwbreak+;unexpected", b"OK"):
            with self.subTest(response=response):
                remote = FakeGDB(qsupported_reply=response)
                rsp = m.RSP(remote)
                with self.assertRaisesRegex(ValueError, "capability response"):
                    rsp.negotiate_public_breakpoint_capabilities()
                self.assertTrue(rsp._feature_negotiation_failed)
                with self.assertRaisesRegex(ValueError, "failed feature negotiation"):
                    rsp.send("?")
                with self.assertRaisesRegex(ValueError, "fresh stopped"):
                    rsp.negotiate_public_breakpoint_capabilities()
                self.assertEqual(remote.commands, [m.PUBLIC_QSUPPORTED_COMMAND])

    def test_missing_qsupported_ack_poison_session(self):
        remote = FakeGDB(disconnect_on=m.PUBLIC_QSUPPORTED_COMMAND)
        rsp = m.RSP(remote)
        with self.assertRaises(ConnectionError):
            rsp.negotiate_public_breakpoint_capabilities()
        self.assertTrue(rsp._feature_negotiation_failed)
        with self.assertRaisesRegex(ValueError, "failed feature negotiation"):
            rsp.send("?")
        self.assertEqual(remote.commands, [m.PUBLIC_QSUPPORTED_COMMAND])

    def test_qsupported_keyboardinterrupt_after_wire_ack_poison_and_no_reuse(self):
        remote = FakeGDB()
        rsp = m.RSP(remote)
        with patch.object(rsp, "receive", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                rsp.negotiate_public_breakpoint_capabilities()
        self.assertEqual(remote.commands, [m.PUBLIC_QSUPPORTED_COMMAND])
        self.assertTrue(rsp._feature_negotiation_failed)
        self.assertFalse(rsp._features_negotiated)
        self.assertFalse(rsp._negotiating_features)
        for action in (lambda: rsp.send("?"),
                       lambda: rsp.send("g"),
                       lambda: rsp.negotiate_public_breakpoint_capabilities()):
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(remote.commands, [m.PUBLIC_QSUPPORTED_COMMAND])

    def test_qsupported_partial_transmit_baseexception_poison(self):
        for failure in (KeyboardInterrupt(), SystemExit(8)):
            with self.subTest(failure=type(failure).__name__):
                remote = FakeGDB()
                rsp = m.RSP(remote)
                # Model a guest accepting some bytes before operator interruption.
                def interrupted_transmit(command):
                    rsp._send_bytes(b"$qSupported")
                    raise failure
                with patch.object(rsp, "_transmit", side_effect=interrupted_transmit):
                    with self.assertRaises(type(failure)):
                        rsp.negotiate_public_breakpoint_capabilities()
                self.assertTrue(rsp._feature_negotiation_failed)
                self.assertFalse(rsp._features_negotiated)
                self.assertFalse(rsp._negotiating_features)
                with self.assertRaisesRegex(ValueError, "failed feature negotiation"):
                    rsp.send("?")

    def test_qsupported_fresh_rejected_before_wire_does_not_poison(self):
        remote = FakeGDB()
        rsp = m.RSP(remote)
        rsp.send("?")
        with self.assertRaisesRegex(ValueError, "first on a fresh"):
            rsp.negotiate_public_breakpoint_capabilities()
        self.assertFalse(rsp._feature_negotiation_failed)
        self.assertEqual(remote.commands, ["?"])

    def test_existing_checksum_trailer_rejects_one_digit(self):
        remote = FakeGDB()
        # One checksum nibble followed by a nonhex byte cannot be accepted.
        remote.buf.extend(b"$S02#0+")
        rsp = m.RSP(remote)
        with self.assertRaisesRegex(ValueError, "invalid GDB checksum text"):
            rsp.receive()
        self.assertEqual(remote.commands, [])

    def test_strict_generated_stop_only_t05_hardware_break(self):
        self.assertEqual(m.strict_public_negotiated_stop(b"T05hwbreak:;"),
                         "T05hwbreak:;")
        for bad in (b"S05k", b"S05", b"T05", b"T05swbreak:;",
                    b"T05hwbreak:;junk", b"T05hwbreak:;\n", b"t05hwbreak:;"):
            with self.subTest(stop=bad):
                with self.assertRaisesRegex(ValueError, "not exact negotiated"):
                    m.strict_public_negotiated_stop(bad)
        # Existing strict parser remains byte-for-byte unchanged and
        # continues to reject the nonstandard mGBA fallback.
        with self.assertRaises(ValueError):
            m.parse_stop(b"S05k")

    def test_existing_capture_never_negotiates_by_default(self):
        report, data, remote, output = self.run_fake(max_stops=1)
        self.assertNotIn(m.PUBLIC_QSUPPORTED_COMMAND, remote.commands)

    def test_corrupt_checksum_sends_nak(self):
        remote=FakeGDB(corrupted='?')
        with self.assertRaisesRegex(ValueError,'checksum'):
            m.RSP(remote).send('?')
        self.assertEqual(remote.nacks,1)

    def test_corrupt_g_response_yields_partial(self):
        report, saved, remote, file = self.run_fake(FakeGDB(corrupted='g'),max_stops=2)
        self.assertIn('checksum', report['failure'])
        self.assertFalse(report['stop_budget_reached'])
        self.assertEqual(report['leftover_breakpoints'],[])
        self.assertEqual(file.stat().st_mode & 0o777,0o600)

    def test_truncated_g_response_yields_partial(self):
        report, *_ = self.run_fake(FakeGDB(trunc='g'),max_stops=2)
        self.assertIn('GDB disconnected', report['failure'])
        self.assertFalse(report['stop_budget_reached'])

    def test_unexpected_exit_is_not_cpu_stop(self):
        report, *_ = self.run_fake(FakeGDB(exit_stop=True),max_stops=2)
        self.assertIn('not a CPU stop',report['failure'])

    def test_register_decode_and_invalid(self):
        decoded = m.parse_registers(registers(m.COPY_ENTRY, r6=19))
        self.assertEqual((decoded[15],decoded[6]),(m.COPY_ENTRY,19))
        for invalid in (b'',b'00'*10,b'z'*128,b'00'*63):
            with self.assertRaises(ValueError): m.parse_registers(invalid)
        self.assertEqual(m.parse_stop(b'T05thread:1;'), 'T05thread:1;')

    def test_reject_unsupported_escape_and_rle(self):
        for raw in (b'$abc}xx#00',b'$abc*xx#00'):
            remote=FakeGDB();remote.buf.extend(raw)
            with self.assertRaisesRegex(ValueError,'unsupported'):
                m.RSP(remote).receive()

    def test_memory_pointer_scope_enforced_twice(self):
        remote = FakeGDB();rsp=m.RSP(remote)
        for addr, count in ((0,6),(0x03000100,6),(0x02030000,6),
                            (m.SRC_BASE+5,2),(m.PP_BASE,5),(True,6)):
            with self.assertRaises(ValueError):m.read_memory(rsp,addr,count)
        self.assertEqual(remote.commands,[])

    def test_real_digest_symlink_and_wrong_sha(self):
        with patch.object(m,'EXACT_ROM',self.rom_sha):
            self.assertEqual(m.digest(self.rom,33554432,self.rom_sha),self.rom_sha)
            with self.assertRaisesRegex(ValueError,'identity'):
                m.digest(self.rom,33554432,'0'*64)
            link=self.root/'linked_rom.gba'
            if not link.exists():link.symlink_to(self.rom)
            with self.assertRaisesRegex(ValueError,'invalid private'):
                m.digest(link,33554432,self.rom_sha)

    def test_good_copy_pp_and_main_marker(self):
        report, saved, stub, file = self.run_fake(max_stops=4)
        self.assertTrue(report['stop_budget_reached'])
        self.assertNotIn('completed_capture', report)
        self.assertEqual(report['marker_stop_count'],4)
        self.assertTrue(report['stop_budget_reached'])
        self.assertIsNone(report['failure'])
        self.assertTrue(report['input_files_unchanged'])
        self.assertTrue(report['events'][1]['destination_is_player0_buffer'])
        self.assertTrue(report['events'][1]['six_byte_pair_equal'])
        self.assertTrue(report['events'][1]['post_a_loop_candidate_reached'])
        self.assertEqual(report['events'][1]['copy_index_r1'],6)
        self.assertTrue(report['events'][2]['pp_decrement_observed'])
        self.assertTrue(report['events'][2]['pp_store_value_matches_r6'])
        self.assertEqual(report['events'][3]['main_byte_before_only'],2)
        self.assertEqual(report['events'][0]['registers_r0_r15'].__len__(),16)
        self.assertIn('s',stub.commands)
        self.assertEqual(stub.interrupts,0)
        self.assertEqual(file.stat().st_mode & 0o777,0o600)
        self.assertFalse(report['emulator_loaded_rom_verified'])
        self.assertEqual(report['host_input_during_battle'],'NOT_EXCLUDED')
        self.assertEqual(report['raw_wire_trace']['format'],'ordered_raw_rsp_hex_v1')
        self.assertFalse(report['raw_wire_trace']['truncated'])
        with patch.object(m,'EXACT_ROM',self.rom_sha),patch.object(m,'EXACT_SAVE',self.save_sha):
            with self.assertRaisesRegex(ValueError,'output exists'):
                m.run_capture(self.rom,self.save,file,2345,max_stops=2)

    def test_destination_is_measured_not_constant(self):
        report,*_ = self.run_fake(FakeGDB(epilogue_dest=m.DST_OTHER),max_stops=2)
        self.assertFalse(report['events'][1]['destination_is_player0_buffer'])
        self.assertTrue(report['events'][1]['destination_is_other_buffer'])
        self.assertEqual(report['events'][1]['post_a_loop_r0_destination_candidate'],f'0x{m.DST_OTHER:08x}')
        self.assertFalse(report['events'][1]['actor0_marker_only'])

    def test_source_self_comparison_never_counts_as_equal(self):
        report,*_ = self.run_fake(FakeGDB(epilogue_dest=m.SRC_BASE),max_stops=2)
        post = report['events'][1]
        self.assertIsNone(post['six_byte_pair_equal'])
        self.assertIn('self-comparison',post['destination_unreadable'])
        self.assertFalse(post['destination_is_player0_buffer'])

    def test_unknown_destination_explicitly_unreadable(self):
        report,*_ = self.run_fake(FakeGDB(epilogue_dest=0x0203F000),max_stops=2)
        post = report['events'][1]
        self.assertIsNone(post['six_byte_pair_equal'])
        self.assertIn('independently pinned',post['destination_unreadable'])
        self.assertIsNone(report['failure'])  # Research note, not a certified copy.

    def test_shared_epilogue_is_not_a_completed_copy(self):
        stub=FakeGDB(stop_pcs=[m.COPY_ENTRY,m.COPY_SHARED_EPILOGUE])
        report,*_=self.run_fake(stub,max_stops=2)
        event=report['events'][1]
        self.assertTrue(event['shared_epilogue_reached'])
        self.assertFalse(event['copy_completion_proven_here'])
        self.assertNotIn('six_byte_pair_equal',event)

    def test_post_a_loop_without_entry_is_unusable(self):
        stub=FakeGDB(stop_pcs=[m.COPY_POST_A])
        report,*_=self.run_fake(stub,max_stops=1)
        self.assertIn('no immediately paired',report['events'][0]['copy_observation_unusable'])
        self.assertNotIn('six_byte_pair_equal',report['events'][0])

    def test_bias_consistent_plus_two(self):
        report,*_ = self.run_fake(FakeGDB(bias=2),max_stops=4)
        self.assertEqual(report['pc_bias'],2)
        self.assertTrue(report['events'][2]['pp_decrement_observed'])

    def test_bias_drift_rejected_partial(self):
        remote=FakeGDB(bias=0);remote.drift_bias=True
        report,*_ = self.run_fake(remote,max_stops=3)
        self.assertIn('PC bias changed',report['failure'])
        self.assertFalse(report['stop_budget_reached'])
        self.assertEqual(report['marker_stop_count'],1)

    def test_deadline_interrupt_and_partial_report(self):
        stub=FakeGDB(hang=True)
        report, saved, remote, file = self.run_fake(stub,max_stops=2,timeout=0.005,
                                                    deadline_seconds=0.03)
        self.assertTrue(report['deadline_reached'])
        self.assertFalse(report['stop_budget_reached'])
        self.assertGreaterEqual(stub.interrupts,1)
        self.assertEqual(report['leftover_breakpoints'],[])
        self.assertIn('deadline',report['failure'])

    def test_interrupt_failure_reports_leftover_breakpoints(self):
        stub=FakeGDB(hang=True,interrupt_responds=False)
        report, *_ = self.run_fake(stub,max_stops=2,timeout=0.001,deadline_seconds=0.004)
        self.assertTrue(report['leftover_breakpoints'])
        self.assertTrue(report['cleanup_errors'])
        self.assertFalse(report['stop_budget_reached'])
        self.assertFalse(any(cmd.startswith('z0,') for cmd in stub.commands))

    def test_stale_extra_stop_is_rejected(self):
        report, *_ = self.run_fake(FakeGDB(stale_after_stop=True),max_stops=2)
        self.assertIn('did not ACK',report['failure'])
        self.assertFalse(report['stop_budget_reached'])

    def test_keyboard_interrupt_stops_then_writes_partial(self):
        stub=FakeGDB(hang=True,keyboard_interrupt_once=True)
        report, *_ = self.run_fake(stub,max_stops=2,timeout=0.01,deadline_seconds=1)
        self.assertIn('KeyboardInterrupt', report['failure'])
        self.assertEqual(stub.interrupts,1)
        self.assertFalse(report['stop_budget_reached'])
        self.assertEqual(report['leftover_breakpoints'],[])

    def test_rejected_breakpoint_leaves_partial_file(self):
        report, saved, stub, file = self.run_fake(FakeGDB(install_fail=True),max_stops=2)
        self.assertIn('breakpoint rejected',report['failure'])
        self.assertTrue(file.is_file())
        self.assertEqual(report['marker_stop_count'],0)
        self.assertEqual(report['leftover_breakpoints'],[])

    def test_non_player_pp_address_does_not_step(self):
        stub=FakeGDB(pp_wrong_address=True)
        report, *_ = self.run_fake(stub,max_stops=3)
        self.assertNotIn('pp_before',report['events'][2])
        self.assertNotIn('s',stub.commands)
        self.assertEqual(report['events'][2]['pp_register_r1_address'],'0x03000100')

    def test_pp_r0_is_not_used_as_actor_authority(self):
        stub=FakeGDB(pp_r0=1234)
        report,*_=self.run_fake(stub,max_stops=3)
        e=report['events'][2]
        self.assertEqual(e['pp_register_r0_unverified'],1234)
        self.assertEqual(e['pp_before'],20)
        self.assertTrue(e['pp_decrement_observed'])
        self.assertIn('s',stub.commands)

    def test_failed_pp_step_keeps_before_and_failure(self):
        stub=FakeGDB(step_pc_delta=4)
        report,*_=self.run_fake(stub,max_stops=3)
        e=report['events'][2]
        self.assertEqual(report['marker_stop_count'],3)
        self.assertEqual(e['pp_before'],20)
        self.assertIn('did not advance',e['pp_step_error'])
        self.assertNotIn('pp_after',e)
        self.assertIn('did not advance',report['failure'])

    def test_probe_corrupted_g_preserves_private_wire(self):
        report,*_=self.run_fake(FakeGDB(corrupted='g'),probe_only=True)
        self.assertIn('checksum',report['failure'])
        wire=report['raw_wire_trace']
        rx=b''.join(bytes.fromhex(e['hex']) for e in wire['events'] if e['direction']=='rx')
        self.assertIn(b'$' + registers(m.COPY_ENTRY),rx)
        self.assertIn(b'#00',rx)
        self.assertTrue(report['probe_only'])
        self.assertIn('stop_raw_ascii',report['probe_transcript'])

    def test_probe_unsupported_rle_keeps_raw_response(self):
        report,*_=self.run_fake(FakeGDB(rle_g=True),probe_only=True)
        self.assertIn('unsupported',report['failure'])
        rx=b''.join(bytes.fromhex(e['hex']) for e in report['raw_wire_trace']['events'] if e['direction']=='rx')
        self.assertIn(b'00*xxx',rx)
        self.assertTrue(report['raw_wire_trace']['recorded_bytes']>0)

    def test_interrupt_double_stop_drained_before_cleanup(self):
        remote=FakeGDB(hang=True,double_interrupt_stop=True)
        report,*_=self.run_fake(remote,max_stops=2,timeout=0.003,deadline_seconds=0.015)
        self.assertTrue(report['deadline_reached'])
        self.assertEqual(report['leftover_breakpoints'],[])
        self.assertEqual(report['raw_wire_trace']['interrupt_drain_stops'],['T05thread:1;'])
        self.assertFalse(any('did not ACK' in msg for msg in report['cleanup_errors']))

    def test_breakpoint_removal_failure_is_visible(self):
        stub=FakeGDB(cleanup_fail=True)
        report, *_ = self.run_fake(stub,max_stops=1)
        self.assertTrue(report['leftover_breakpoints'])
        self.assertTrue(report['stop_budget_reached'])
        self.assertIn('cleanup',report['failure'])

    def test_probe_only_never_resumes_or_installs_breakpoints(self):
        report,saved,remote,file=self.run_fake(probe_only=True)
        self.assertTrue(report['probe_only'])
        self.assertIsNone(report['failure'])
        self.assertFalse(report['stop_budget_reached'])
        self.assertEqual(remote.commands,['?','g',f'm{m.SRC_BASE:08x},6'])
        self.assertEqual(report['probe_transcript']['register_payload_bytes'],64)

    def test_d7_non_actor_entry_invalidates_pending_actor0(self):
        # actor0 starts, then actor1 intervenes before a matching-looking
        # post-A destination. Never combine across original invocations.
        stub = FakeGDB(stop_pcs=[m.COPY_ENTRY, m.COPY_ENTRY, m.COPY_POST_A,
                                  m.COPY_POST_A], entry_actors={1: 1},
                       epilogue_dest=m.DST_OTHER)
        report, *_ = self.run_fake(stub, max_stops=4)
        self.assertIsNone(report['failure'])
        entry0, entry1, post1, post2 = report['events']
        self.assertTrue(entry0['actor0_marker_only'])
        self.assertFalse(entry1['actor0_marker_only'])
        self.assertTrue(entry1['incomplete_previous_copy_pair'])
        self.assertIn('not a validated actor0', entry1['copy_entry_rejected_reason'])
        self.assertIn('no immediately paired', post1['copy_observation_unusable'])
        self.assertIn('no immediately paired', post2['copy_observation_unusable'])
        self.assertNotIn('six_byte_pair_equal', post1)
        self.assertNotIn('six_byte_pair_equal', post2)

    def test_d7_actor0_entry_never_pairs_to_other_battler(self):
        report, *_ = self.run_fake(FakeGDB(epilogue_dest=m.DST_OTHER), max_stops=2)
        post = report['events'][1]
        self.assertIsNone(post['six_byte_pair_equal'])
        self.assertTrue(post['destination_is_other_buffer'])
        self.assertFalse(post['destination_is_player0_buffer'])
        self.assertIn('another battler', post['destination_unreadable'])
        self.assertNotIn('dest6_hex_private', post)
        self.assertFalse(post['actor0_marker_only'])

    def test_probe_truncated_g_preserves_private_wire(self):
        report, _, stub, path = self.run_fake(FakeGDB(trunc='g'), probe_only=True)
        self.assertIn('GDB disconnected', report['failure'])
        self.assertIsNotNone(report['probe_transcript'])
        rx = b''.join(bytes.fromhex(e['hex']) for e in report['raw_wire_trace']['events']
                      if e['direction'] == 'rx')
        self.assertIn(b'$'+registers(m.COPY_ENTRY)[:3], rx)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(stub.commands, ['?', 'g'])

    def test_probe_disconnect_before_ack_preserves_wire(self):
        report, _, stub, path = self.run_fake(FakeGDB(disconnect_on='g'), probe_only=True)
        self.assertIn('GDB disconnected', report['failure'])
        tx = b''.join(bytes.fromhex(e['hex']) for e in report['raw_wire_trace']['events']
                      if e['direction'] == 'tx')
        self.assertIn(packet(b'g'), tx)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(stub.commands, ['?', 'g'])

    def test_raw_wire_byte_and_event_caps(self):
        stub = FakeGDB()
        rsp = m.RSP(stub)
        with patch.object(m, 'MAX_WIRE_BYTES', 8):
            rsp._log_wire('tx', b'abcde')
            rsp._log_wire('rx', b'1234567890')
            wire = rsp.wire_trace()
            self.assertEqual(wire['recorded_bytes'], 8)
            self.assertEqual(wire['omitted_bytes'], 7)
            self.assertTrue(wire['truncated'])
            self.assertEqual(b''.join(bytes.fromhex(x['hex']) for x in wire['events']),
                             b'abcde123')
        rsp = m.RSP(stub)
        with patch.object(m, 'MAX_WIRE_EVENTS', 2):
            rsp._log_wire('tx', b'a')
            rsp._log_wire('rx', b'b')
            rsp._log_wire('tx', b'c')
            wire = rsp.wire_trace()
            self.assertEqual(len(wire['events']), 2)
            self.assertEqual(wire['recorded_bytes'], 2)
            self.assertEqual(wire['omitted_bytes'], 1)
            self.assertTrue(wire['truncated'])

    def test_resume_restores_configured_timeout(self):
        # The old 1s deadline never shortened the timeout, so this test passed
        # even when the resume() finally/restore was deliberately removed.
        stub = FakeGDB()
        rsp = m.RSP(stub)
        original_timeout = 0.15
        stop, expired = rsp.resume(__import__('time').monotonic()+0.05, original_timeout)
        self.assertFalse(expired)
        self.assertEqual(stop, 'S05')
        self.assertTrue(stub.timeouts)
        self.assertLess(min(stub.timeouts), original_timeout,
                        'test setup must exercise a shortened near-deadline read')
        self.assertEqual(stub.timeouts[-1], original_timeout,
                         'resume must restore the configured timeout after the stop')
        self.assertEqual(stub.timeout, original_timeout)

    def test_first_foreign_entry_has_no_previous_pair_to_lose(self):
        # A rejected first entry is NOT evidence that an earlier pair was lost.
        stub = FakeGDB(stop_pcs=[m.COPY_ENTRY], entry_actors={0: 1})
        report, *_ = self.run_fake(stub, max_stops=1)
        self.assertIsNone(report['failure'])
        first = report['events'][0]
        self.assertIn('not a validated actor0', first['copy_entry_rejected_reason'])
        self.assertNotIn('incomplete_previous_copy_pair', first)
        self.assertNotIn('source6_hex_private', first)

    def test_resume_t05_stop_is_recorded_without_claiming_authority(self):
        stub = FakeGDB(resume_stop_reply=b'T05thread:1;')
        report, _, remote, _ = self.run_fake(stub, max_stops=1)
        self.assertIsNone(report['failure'])
        self.assertEqual(report['events'][0]['stop'], 'T05thread:1;')
        self.assertEqual(report['marker_stop_count'], 1)
        self.assertTrue(report['events'][0]['actor0_marker_only'])
        self.assertEqual(remote.commands.count('c'), 1)

    def test_extended_g_reply_inside_capture_remains_unverified(self):
        stub = FakeGDB(extra_g_cpsr=True)
        report, _, remote, _ = self.run_fake(stub, max_stops=1)
        self.assertIsNone(report['failure'])
        self.assertEqual(report['marker_stop_count'], 1)
        self.assertEqual(report['events'][0]['candidate_original_pc'],
                         f'0x{m.COPY_ENTRY:08x}')
        self.assertFalse(report['emulator_loaded_rom_verified'])
        self.assertIn('g', remote.commands)
        # Extra register bytes are deliberately not mislabelled as verified CPSR.
        self.assertNotIn('cpsr_verified', report['events'][0])

    def test_post_a_with_plus_four_bias(self):
        report, *_ = self.run_fake(FakeGDB(bias=4), max_stops=2)
        self.assertEqual(report['pc_bias'],4)
        self.assertTrue(report['events'][1]['six_byte_pair_equal'])

    def test_pp_step_t_stop_reply(self):
        report, *_ = self.run_fake(FakeGDB(step_stop_reply=b'T05thread:1;'), max_stops=3)
        self.assertEqual(report['events'][2]['pp_single_step_stop'], 'T05thread:1;')
        self.assertTrue(report['events'][2]['pp_decrement_observed'])

    def test_extra_cpsr_length_reply_does_not_claim_decoding(self):
        report, _, stub, _ = self.run_fake(FakeGDB(extra_g_cpsr=True), probe_only=True)
        self.assertIsNone(report['failure'])
        self.assertEqual(report['probe_transcript']['register_payload_bytes'], 68)
        self.assertEqual(stub.commands,['?','g',f'm{m.SRC_BASE:08x},6'])
        self.assertFalse(report['emulator_loaded_rom_verified'])

    def test_input_mutated_during_capture_is_reported(self):
        # Use a disposable duplicate, never the user's protected save.
        temp_save=self.root/(self._testMethodName+'.sav')
        temp_save.write_bytes(b'B'*131072)
        def mutate(): temp_save.write_bytes(b'C'*131072)
        stub=FakeGDB(on_resume=mutate)
        out=self.root/(self._testMethodName+'.json')
        with patch.object(m,'EXACT_ROM',self.rom_sha),patch.object(m,'EXACT_SAVE',self.save_sha), \
             patch.object(m.socket,'create_connection',return_value=stub):
            report=m.run_capture(self.rom,temp_save,out,2345,max_stops=1)
        self.assertFalse(report['input_files_unchanged'])
        self.assertIn('rehash',report['failure'])
        self.assertTrue(report['stop_budget_reached'])

    def test_output_cannot_alias_original(self):
        with patch.object(m,'EXACT_ROM',self.rom_sha),patch.object(m,'EXACT_SAVE',self.save_sha):
            with self.assertRaisesRegex(ValueError,'output cannot replace'):
                m.run_capture(self.rom,self.save,self.rom,2345)

    def test_bounded_parameters(self):
        for port,stops,timeout,deadline in ((0,2,1,3),(2345,0,1,3),(2345,201,1,3),
                                            (2345,2,31,3),(2345,2,1,0),(2345,2,1,1801)):
            with self.assertRaises(ValueError):
                m.run_capture(self.rom,self.save,self.root/'unused.json',port,stops,timeout,deadline)

if __name__=='__main__': unittest.main()