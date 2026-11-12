"""Synthetic RSP wire tests; not an emulator run or a ROM/native approval."""
import hashlib
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import capture_original_request_rsp as m


def packet(payload):
    return b'$' + payload + b'#%02x' % (sum(payload) & 255)


def registers(pc, r0=0, r1=1, r2=m.SRC_BASE, r3=6, r4=0):
    r = [r0, r1, r2, r3, r4] + [0]*10 + [pc]
    return b''.join(x.to_bytes(4, 'little') for x in r).hex().encode()


class FakeGDB:
    def __init__(self, corrupted=False):
        self.buf = bytearray()
        self.commands = []
        self.n = 0
        self.corrupted = corrupted

    def sendall(self, data):
        if data == b'+' or data == b'-':
            return
        assert data.startswith(b'$') and len(data) > 4
        head, crc = data[1:].rsplit(b'#', 1)
        assert int(crc, 16) == sum(head) & 255
        command = head.decode()
        self.commands.append(command)
        if command == '?':
            answer = b'S02'
        elif command.startswith('Z0,') or command.startswith('z0,'):
            answer = b'OK'
        elif command == 'c':
            self.n += 1
            answer = b'S05'
        elif command == 'g':
            answer = registers(m.COPY_ENTRY if self.n == 1 else m.COPY_DONE,
                               r4=m.SRC_BASE)
        elif command.startswith('m'):
            addr, count = command[1:].split(',')
            assert int(addr, 16) in (m.SRC_BASE, m.DST_PLAYER0, m.PP_BASE)
            assert 0 < int(count, 16) <= 6
            answer = (b'010203040506' if int(count, 16) == 6 else b'14131211')
        else:
            raise AssertionError('forbidden debugger command ' + command)
        if self.corrupted and command == '?':
            reply = b'$S02#00'
        else:
            reply = packet(answer)
        self.buf.extend(b'+' + reply)

    def recv(self, n):
        assert n == 1
        if not self.buf:
            raise ConnectionError('empty fake GDB stream')
        c = bytes(self.buf[:1]); del self.buf[:1]
        return c

    def __enter__(self): return self
    def __exit__(self, *_): return None
    def settimeout(self, _): pass


class RSPTests(unittest.TestCase):
    def test_checksum_and_command_whitelist(self):
        remote = FakeGDB()
        rsp = m.RSP(remote)
        self.assertEqual(rsp.send('?'), b'S02')
        self.assertEqual(rsp.send('m0201cf94,6'), b'010203040506')
        for illegal in ('M0201cf94,6:abcdef', 'G0000', 'P0=0', 'k', 'vRun',
                        'qRcmd,7265736574', 'm03000100,20', 'Z0,08000000,4'):
            with self.assertRaises(ValueError, msg=illegal):
                rsp.send(illegal)
        self.assertEqual(remote.commands, ['?', 'm0201cf94,6'])

    def test_corrupt_packet_is_denied(self):
        with self.assertRaisesRegex(ValueError, 'checksum'):
            m.RSP(FakeGDB(corrupted=True)).send('?')

    def test_register_parser(self):
        r = m.parse_registers(registers(m.COPY_ENTRY))
        self.assertEqual(r[15], m.COPY_ENTRY)
        self.assertEqual(r[2], m.SRC_BASE)
        for x in (b'', b'00' * 10, b'z' * 128):
            with self.assertRaises(ValueError): m.parse_registers(x)

    def test_memory_pointer_denial(self):
        r = m.RSP(FakeGDB())
        for address, count in ((0, 6), (0x03000000, 6), (0x0203FFFF, 6),
                               (0x02000000, 7), (True, 6)):
            with self.assertRaises(ValueError): m.read_memory(r, address, count)

    def test_identity_and_two_breakpoint_observations(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rom, save, out = root/'private.gba', root/'private.sav', root/'private.json'
            rom.write_bytes(b'fake ROM'); save.write_bytes(b'fake SAV')
            remote = FakeGDB()
            def fake_digest(path, size, expected):
                assert Path(path) in (rom, save)
                return hashlib.sha256(Path(path).read_bytes()).hexdigest()
            with patch.object(m, 'digest', fake_digest), \
                    patch.object(m.socket, 'create_connection', return_value=remote):
                result = m.run_capture(rom, save, out, 2345, max_stops=2)
            self.assertTrue(out.is_file())
            self.assertEqual(len(result['events']), 2)
            self.assertTrue(result['events'][1]['six_byte_pair_equal'])
            self.assertFalse(result['engine_issued_one_use_request_proven'])
            self.assertFalse(result['new_auto_hook_executed_proven'])
            self.assertEqual(result['native_acceptance'], 0)
            self.assertFalse(any(x[:1] in ('M','X','P','G') for x in remote.commands))
            self.assertEqual(sum(x.startswith('Z0,') for x in remote.commands), len(m.PCS))
            self.assertEqual(sum(x.startswith('z0,') for x in remote.commands), len(m.PCS))
            with patch.object(m,'digest',fake_digest):
                with self.assertRaisesRegex(ValueError,'output exists'):
                    m.run_capture(rom,save,out,2345,2)

    def test_wrong_private_file_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            r=Path(folder)/'wrong.gba';r.write_bytes(b'wrong')
            with self.assertRaises(ValueError):m.digest(r,33554432,m.EXACT_ROM)

    def test_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            r=Path(folder)/'test';r.write_bytes(b'x')
            for port, budget, timeout in ((0, 2, 1),(2345,0,1),(2345,201,1),(2345,2,31)):
                with self.assertRaises(ValueError):
                    m.run_capture(r,r,r.parent/'out',port,budget,timeout)

if __name__=='__main__': unittest.main()