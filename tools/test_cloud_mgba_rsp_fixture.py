#!/usr/bin/env python3
"""Public fixture-only unit tests; not emulator or gameplay acceptance."""
import socket
import unittest

from cloud_mgba_rsp_fixture import (
    LOOP_WORD, MAX_FRAME, MAX_PREFIX_BYTES, ROM_SIZE, check_reply,
    encode_rsp, make_fixture, recv_rsp, request,
)


class CloudRSPFixtureTest(unittest.TestCase):
    def sockets(self):
        a, b = socket.socketpair()
        a.settimeout(0.4)
        b.settimeout(0.4)
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        return a, b

    def test_generated_rom_is_original_bounded_image(self):
        rom = make_fixture()
        self.assertEqual(len(rom), ROM_SIZE)
        self.assertEqual(rom[:4], bytes.fromhex("2e0000ea"))
        self.assertEqual(rom[0xC0:0xC4], LOOP_WORD)
        self.assertEqual(rom[4:0xA0], bytes(156))
        self.assertEqual((0x19 + sum(rom[0xA0:0xBE])) & 255, 0)

    def test_rsp_encoding_checksum(self):
        self.assertEqual(encode_rsp(b"?"), b"$?#3f")
        self.assertEqual(encode_rsp(b"g"), b"$g#67")

    def test_no_mutating_command_and_no_wire_bytes(self):
        a, b = self.sockets()
        for command in (b"c", b"s", b"Z0,080000c0,4", b"z0,080000c0,4",
                        b"M080000c0,4:ffff", b"m080000c0,8"):
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    request(a, command)
                with self.assertRaises(socket.timeout):
                    b.recv(1)  # negative wire assertion; cannot silently send

    def test_real_frame_checksums_and_ack(self):
        a, b = self.sockets()
        b.sendall(b"+$S05#b8")
        self.assertEqual(recv_rsp(a), b"S05")
        self.assertEqual(b.recv(1), b"+")

    def test_frame_corruption_rejected_with_nak(self):
        a, b = self.sockets()
        b.sendall(b"$S05#00")
        with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
            recv_rsp(a)
        self.assertEqual(b.recv(1), b"-")

    def test_invalid_checksum_encoding_rejected_with_nak(self):
        a, b = self.sockets()
        b.sendall(b"$S05#zz")
        with self.assertRaisesRegex(RuntimeError, "checksum encoding"):
            recv_rsp(a)
        self.assertEqual(b.recv(1), b"-")

    def test_unexpected_framing_byte(self):
        a, b = self.sockets()
        b.sendall(b"!")
        with self.assertRaisesRegex(RuntimeError, "framing byte"):
            recv_rsp(a)

    def test_stub_nak(self):
        a, b = self.sockets()
        b.sendall(b"-")
        with self.assertRaisesRegex(RuntimeError, "stub NAK"):
            recv_rsp(a)

    def test_eof_mid_frame(self):
        a, b = self.sockets()
        b.sendall(b"$S05")
        b.shutdown(socket.SHUT_WR)
        with self.assertRaisesRegex(RuntimeError, "mid-frame"):
            recv_rsp(a)

    def test_eof_in_checksum(self):
        a, b = self.sockets()
        b.sendall(b"$S05#a")
        b.shutdown(socket.SHUT_WR)
        with self.assertRaisesRegex(RuntimeError, "missing RSP checksum"):
            recv_rsp(a)

    def test_frame_size_bound(self):
        a, b = self.sockets()
        b.sendall(b"$" + b"A" * (MAX_FRAME + 1))
        with self.assertRaisesRegex(RuntimeError, "bounded limit"):
            recv_rsp(a)

    def test_ack_prefix_flood_bounded(self):
        a, b = self.sockets()
        b.sendall(b"+" * (MAX_PREFIX_BYTES + 1))
        with self.assertRaisesRegex(RuntimeError, "prefix exceeds bounded limit"):
            recv_rsp(a)

    def test_grammar_rejects_forged_status_and_memory(self):
        with self.assertRaisesRegex(RuntimeError, "stop reply"):
            check_reply(b"OK", b"00" * 64, LOOP_WORD.hex().encode())
        with self.assertRaisesRegex(RuntimeError, "mapping mismatch"):
            check_reply(b"S05", b"00" * 64, b"00000000")
        with self.assertRaisesRegex(RuntimeError, "register"):
            check_reply(b"S05", b"zz" * 64, LOOP_WORD.hex().encode())

    def test_stop_requires_full_pr26_grammar(self):
        for invalid in (b"S", b"S05extra", b"T05\nbad", b"T0X", b"T", b"SZZ"):
            with self.subTest(stop=invalid):
                with self.assertRaisesRegex(RuntimeError, "stop reply"):
                    check_reply(invalid, b"00" * 64, LOOP_WORD.hex().encode())

    def test_register_floor_matches_pr26_128_hex(self):
        with self.assertRaisesRegex(RuntimeError, "register"):
            check_reply(b"S05", b"00" * 63, LOOP_WORD.hex().encode())
        check_reply(b"S05", b"00" * 64, LOOP_WORD.hex().encode())

    def test_register_upper_bound(self):
        with self.assertRaisesRegex(RuntimeError, "register"):
            check_reply(b"S05", b"0" * (MAX_FRAME + 2), LOOP_WORD.hex().encode())

    def test_extended_registers_and_t_stop_are_accepted(self):
        check_reply(b"T05watch:080000c0;", b"00" * 68, LOOP_WORD.hex().encode())


if __name__ == "__main__":
    unittest.main()
