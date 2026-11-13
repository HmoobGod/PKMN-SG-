#!/usr/bin/env python3
"""Bounded negative tests; never substitute for actual hosted-mGBA run."""
import socket
import unittest
from cloud_mgba_rsp_fixture import encode_rsp
from cloud_mgba_z0_fixture import SET, REMOVE, breakpoint_request

class Z0FixtureTests(unittest.TestCase):
    def pair(self):
        a,b=socket.socketpair()
        a.settimeout(0.3)
        b.settimeout(0.3)
        self.addCleanup(a.close); self.addCleanup(b.close)
        return a,b

    def test_exact_packets(self):
        self.assertEqual(SET,b"Z0,080000c0,4")
        self.assertEqual(REMOVE,b"z0,080000c0,4")

    def test_denials_send_no_bytes(self):
        a,b=self.pair()
        for cmd in (b"c",b"s",b"\x03",b"Z0,080000c0,2",
                    b"Z0,080000c4,4",b"z0,080000c4,4",
                    b"Z2,080000c0,4",b"M080000c0,4:ffff",
                    b"P0=ffffffff",b"m080000c0,4"):
            with self.subTest(cmd=cmd):
                with self.assertRaises(ValueError):
                    breakpoint_request(a,cmd)
                with self.assertRaises(socket.timeout):
                    b.recv(1)

    def test_install_ack(self):
        a,b=self.pair()
        b.sendall(b"$OK#9a")
        self.assertEqual(breakpoint_request(a,SET),b"OK")
        self.assertEqual(b.recv(200),encode_rsp(SET)+b"+")

    def test_removal_ack(self):
        a,b=self.pair()
        b.sendall(b"$OK#9a")
        self.assertEqual(breakpoint_request(a,REMOVE),b"OK")
        self.assertEqual(b.recv(200),encode_rsp(REMOVE)+b"+")

    def test_negative_reply_rejected(self):
        for bad in (b"",b"E01",b"S05",b"T05"):
            a,b=self.pair()
            frame=b"$"+bad+b"#"+f"{sum(bad)&255:02x}".encode("ascii")
            b.sendall(frame)
            with self.assertRaisesRegex(RuntimeError,"did not acknowledge"):
                breakpoint_request(a,SET)

    def test_corrupt_checksum_rejected(self):
        a,b=self.pair()
        b.sendall(b"$OK#00")
        with self.assertRaisesRegex(RuntimeError,"checksum mismatch"):
            breakpoint_request(a,SET)
        self.assertEqual(b.recv(200),encode_rsp(SET)+b"-")

if __name__ == "__main__":
    unittest.main()
