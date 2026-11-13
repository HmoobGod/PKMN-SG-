#!/usr/bin/env python3
"""Public fixture-only unit tests; not emulator or gameplay acceptance."""
import socket
import unittest

from cloud_mgba_rsp_fixture import (
    LOOP_WORD, ROM_SIZE, check_reply, encode_rsp, make_fixture, recv_rsp, request,
)


class CloudRSPFixtureTest(unittest.TestCase):
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

    def test_no_mutating_command(self):
        a, b = socket.socketpair()
        try:
            for command in (b"c", b"s", b"Z0,080000c0,4", b"M080000c0,4:ffff"):
                with self.assertRaises(ValueError):
                    request(a, command)
        finally:
            a.close()
            b.close()

    def test_real_frame_checksums_and_ack(self):
        a, b = socket.socketpair()
        try:
            b.sendall(b"+$S05#b8")
            self.assertEqual(recv_rsp(a), b"S05")
            self.assertEqual(b.recv(1), b"+")
        finally:
            a.close()
            b.close()

    def test_frame_corruption_rejected(self):
        a, b = socket.socketpair()
        try:
            b.sendall(b"$S05#00")
            with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                recv_rsp(a)
            self.assertEqual(b.recv(1), b"-")
        finally:
            a.close()
            b.close()

    def test_grammar_rejects_forged_status_and_memory(self):
        with self.assertRaisesRegex(RuntimeError, "paused"):
            check_reply(b"OK", b"00" * 40, LOOP_WORD.hex().encode())
        with self.assertRaisesRegex(RuntimeError, "mapping mismatch"):
            check_reply(b"S05", b"00" * 40, b"00000000")
        with self.assertRaisesRegex(RuntimeError, "register"):
            check_reply(b"S05", b"zz" * 40, LOOP_WORD.hex().encode())


if __name__ == "__main__":
    unittest.main()
