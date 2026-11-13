#!/usr/bin/env python3
"""Synthetic-only safety and protocol tests; no real mGBA or private ROM required."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import probe_exact_rom_rsp_identity as mod


class FakeRSP:
    def __init__(self, image, fail=None, stop='S05', reg_bytes=68):
        self.image = image
        self.fail = fail
        self.stop = stop
        self.reg_bytes = reg_bytes
        self.response = bytearray()
        self.sent = []
        self.timeout_values = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def settimeout(self, v):
        self.timeout_values.append(v)

    def sendall(self, packet):
        self.sent.append(packet)
        if packet in (b'+', b'-'):
            return
        if not packet.startswith(b'$') or b'#' not in packet:
            raise AssertionError('unrecognized command')
        command = packet[1:packet.index(b'#')].decode()
        if command == '?':
            answer = self.stop
        elif command == 'g':
            answer = ('00' * self.reg_bytes)
        elif command.startswith('m'):
            address, size = command[1:].split(',')
            offset = int(address, 16) - mod.ROM_BASE
            answer = self.image[offset:offset + int(size, 16)].hex()
        else:
            raise AssertionError('non-read-only RSP command: ' + command)
        data = answer.encode('ascii')
        checksum = f'{sum(data) & 255:02x}'.encode()
        if self.fail == ('bad_checksum', command):
            checksum = b'00' if checksum != b'00' else b'ff'
        frame = b'+' + b'$' + data + b'#' + checksum
        if self.fail == ('truncated', command):
            frame = frame[:8]
        if self.fail == ('unsupported_rle', command):
            data = b'0*0'
            frame = b'+$' + data + b'#' + f'{sum(data) & 255:02x}'.encode()
        if self.fail == ('odd_g', command):
            data = b'0' * 137
            frame = b'+$' + data + b'#' + f'{sum(data) & 255:02x}'.encode()
        self.response.extend(frame)

    def recv(self, amount):
        if not self.response:
            return b''
        result = self.response[:amount]
        del self.response[:amount]
        return bytes(result)


class IdentityProbeTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.protected = bytearray([0x48] * 256)
        self.modified = bytearray(self.protected)
        self.modified[8:16] = b'ABCDEFGH'
        self.modified[128:136] = b'12345678'
        self.modified[240:248] = b'87654321'
        self.exact_path = self.root / 'exact.gba'
        self.protected_path = self.root / 'current.gba'
        self.exact_path.write_bytes(self.modified)
        self.protected_path.write_bytes(self.protected)
        self.hash_patch = patch.multiple(mod, ROM_LENGTH=256,
                                         EXACT_MODIFIED_SHA=hashlib.sha256(self.modified).hexdigest(),
                                         PROTECTED_CURRENT_SHA=hashlib.sha256(self.protected).hexdigest())
        self.hash_patch.start()
        self.addCleanup(self.hash_patch.stop)
        self.output = self.root / 'private.json'

    def call(self, fake):
        with patch.object(mod.socket, 'create_connection', return_value=fake) as connect:
            result = mod.run(self.exact_path, self.protected_path, self.output)
        self.assertEqual(connect.call_args.args[0], ('127.0.0.1', 2345))
        return result

    def test_window_selection_uses_distinct_discriminators_and_shared_control(self):
        windows = mod.choose_windows(self.modified, self.protected)
        self.assertEqual([w['kind'] for w in windows], ['discriminator'] * 3 + ['shared_control'])
        self.assertEqual(len(set(w['offset'] for w in windows)), 4)
        self.assertTrue(all(w['exact'] != w['protected'] for w in windows[:3]))
        self.assertEqual(windows[-1]['exact'], windows[-1]['protected'])

    def test_complete_sampled_parity_is_not_full_identity_attestation(self):
        stub = FakeRSP(self.modified, stop='T05thread:1;', reg_bytes=68)
        r = self.call(stub)
        self.assertEqual(r['outcome'], 'SAMPLED_WINDOW_PARITY_ONLY')
        self.assertIsNone(r['failure'])
        self.assertEqual(len(r['samples']), 4)
        self.assertEqual(r['g_reply_char_count'], 136)
        self.assertFalse(r['emulator_loaded_rom_verified'])
        self.assertFalse(r['host_battle_input_excluded'])
        self.assertEqual(r['native_acceptance'], 0)
        self.assertEqual(r['production_auto'], 0)
        self.assertEqual([p[1:p.index(b'#')].decode() for p in stub.sent if p.startswith(b'$')][:2], ['?', 'g'])
        self.assertTrue(all(s.startswith(('?', 'g', 'm')) for s in (p[1:p.index(b'#')].decode() for p in stub.sent if p.startswith(b'$'))))
        self.assertEqual(os.stat(self.output).st_mode & 0o777, 0o600)
        self.assertTrue(stub.closed)
        self.assertEqual(self.exact_path.read_bytes(), self.modified)
        self.assertEqual(self.protected_path.read_bytes(), self.protected)

    def test_protected_rom_running_causes_partial_failure(self):
        stub = FakeRSP(self.protected)
        result = self.call(stub)
        self.assertEqual(result['outcome'], 'FAILED_PARTIAL')
        self.assertIn('disagrees', result['failure'])
        self.assertEqual(len(result['samples']), 1)
        self.assertTrue(self.output.exists())

    def test_corrupted_g_checksum_keeps_full_raw_frame_and_nak(self):
        stub = FakeRSP(self.modified, fail=('bad_checksum', 'g'))
        r = self.call(stub)
        self.assertEqual(r['outcome'], 'FAILED_PARTIAL')
        self.assertIn('checksum', r['failure'])
        self.assertIn(b'-', stub.sent)
        self.assertTrue(any(x['direction'] == 'rx' and b'$' in bytes.fromhex(x['hex'])
                            for x in r['raw_wire_trace']))
        self.assertEqual(os.stat(self.output).st_mode & 0o777, 0o600)

    def test_truncated_g_retains_partial_frame(self):
        stub = FakeRSP(self.modified, fail=('truncated', 'g'))
        result = self.call(stub)
        self.assertIn('EOF', result['failure'])
        self.assertTrue(any(x['direction'] == 'rx' and bytes.fromhex(x['hex']).endswith(b'0000')
                            for x in result['raw_wire_trace']))
        self.assertTrue(self.output.exists())

    def test_unsupported_rle_reply_retains_complete_frame(self):
        stub = FakeRSP(self.modified, fail=('unsupported_rle', 'g'))
        result = self.call(stub)
        self.assertIn('unsupported', result['failure'])
        self.assertTrue(any(b'0*0' in bytes.fromhex(x['hex']) for x in result['raw_wire_trace']))

    def test_odd_g_reply_fails_with_unverified_layout(self):
        stub = FakeRSP(self.modified, fail=('odd_g', 'g'))
        r = self.call(stub)
        self.assertIn('unexpected g payload', r['failure'])
        self.assertFalse(r['g_register_layout_verified'])
        self.assertEqual(r['g_reply_char_count'], 137)

    def test_wrong_sha_prevents_network_connection(self):
        self.exact_path.write_bytes(b'B' * 256)
        with patch.object(mod.socket, 'create_connection') as connect:
            with self.assertRaisesRegex(mod.IdentityError, 'SHA-256'):
                mod.run(self.exact_path, self.protected_path, self.output)
            connect.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_wrong_length_prevents_network_connection(self):
        self.exact_path.write_bytes(b'B' * 255)
        with patch.object(mod.socket, 'create_connection') as connect:
            with self.assertRaisesRegex(mod.IdentityError, 'size'):
                mod.run(self.exact_path, self.protected_path, self.output)
            connect.assert_not_called()

    def test_symlinked_rom_rejected_before_network(self):
        link = self.root / 'symbolic.gba'
        link.symlink_to(self.exact_path)
        with patch.object(mod.socket, 'create_connection') as connect:
            with self.assertRaisesRegex(mod.IdentityError, 'non-symlink'):
                mod.run(link, self.protected_path, self.output)
            connect.assert_not_called()

    def test_output_file_cannot_overwrite_existing_report_or_rom(self):
        self.output.write_text('SENTINEL')
        with self.assertRaisesRegex(mod.IdentityError, 'fresh'):
            mod.run(self.exact_path, self.protected_path, self.output)
        self.assertEqual(self.output.read_text(), 'SENTINEL')
        with self.assertRaisesRegex(mod.IdentityError, 'alias'):
            mod.run(self.exact_path, self.protected_path, self.exact_path)

    def test_wire_command_whitelist_rejects_all_control_commands(self):
        fake = FakeRSP(self.modified)
        client = mod.ReadOnlyRSP(fake, mod.choose_windows(self.modified, self.protected))
        for cmd in ('c', 's', 'Z0,08000000,2', 'z0,08000000,2',
                    'M08000000,08:0000000000000000', 'm03000000,08',
                    'm08000000,20', 'k', 'R', 'vRun', 'qRcmd,abc'):
            with self.assertRaisesRegex(mod.IdentityError, 'whitelist'):
                client.exchange(cmd)
        self.assertFalse(fake.sent)

    def test_report_persists_on_connection_failure(self):
        with patch.object(mod.socket, 'create_connection', side_effect=ConnectionRefusedError('no gdb')):
            r = mod.run(self.exact_path, self.protected_path, self.output)
        self.assertEqual(r['outcome'], 'FAILED_PARTIAL')
        self.assertIn('no gdb', r['failure'])
        self.assertEqual(os.stat(self.output).st_mode & 0o777, 0o600)

    def test_wire_trace_caps_are_explicit(self):
        stub = FakeRSP(self.modified)
        client = mod.ReadOnlyRSP(stub, [])
        with patch.multiple(mod, MAX_TRACE_BYTES=5, MAX_TRACE_EVENTS=2):
            client.log('tx', b'1234567')
            client.log('rx', b'foobar')
            client.log('rx', b'discard')
        self.assertEqual(client.trace[0]['hex'], b'12345'.hex())
        self.assertEqual(client.dropped_bytes, 2 + 6 + 7)
        self.assertGreater(client.dropped_events, 0)

    def test_modified_file_change_during_remote_read_fail_closed(self):
        fake = FakeRSP(self.modified)
        orig = fake.sendall
        def tamper(packet):
            if packet.startswith(b'$m') and self.exact_path.read_bytes() == self.modified:
                self.exact_path.write_bytes(b'Z' * 256)
            orig(packet)
        fake.sendall = tamper
        r = self.call(fake)
        self.assertEqual(r['outcome'], 'FAILED_PARTIAL')
        self.assertIn('changed', r['failure'])

    def test_duplicate_image_has_no_discriminating_windows(self):
        with self.assertRaisesRegex(mod.IdentityError, 'two distinct'):
            mod.choose_windows(self.modified, self.modified)


if __name__ == '__main__':
    unittest.main()