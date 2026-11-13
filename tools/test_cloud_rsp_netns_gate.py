#!/usr/bin/env python3
"""No private data. In-memory procfs negatives, plus real container runtime gate."""
import tempfile
import unittest
from pathlib import Path
from cloud_rsp_netns_gate import (
    IsolationError, check_no_external_interfaces, inspect_network, parse_tcp_listeners
)

HEADER = "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode\n"
V4 = "   0: 00000000:0929 00000000:0000 0A 0:0 00:0 0 0 0 0\n"
V4LO = "   0: 0100007F:0929 00000000:0000 0A 0:0 00:0 0 0 0 0\n"
V6 = "   0: 00000000000000000000000000000000:0929 00000000000000000000000000000000:0000 0A 0:0 00:0 0 0 0 0\n"
V6LO = "   0: 00000000000000000000000001000000:0929 00000000000000000000000000000000:0000 0A 0:0 00:0 0 0 0 0\n"

class GateTests(unittest.TestCase):
    def test_ipv4_wildcard_and_loopback(self):
        self.assertEqual(parse_tcp_listeners(HEADER+V4+V4LO, ipv6=False), ("0.0.0.0","127.0.0.1"))

    def test_ipv6_wildcard_and_loopback(self):
        self.assertEqual(parse_tcp_listeners(HEADER+V6+V6LO, ipv6=True), ("::","::1"))

    def test_non_listener_states_are_ignored(self):
        self.assertEqual(parse_tcp_listeners(HEADER+V4.replace(" 0A ", " 01 "), ipv6=False), ())

    def test_wrong_port_ignored(self):
        self.assertEqual(parse_tcp_listeners(HEADER+V4.replace(":0929",":1234"), ipv6=False), ())

    def test_bad_tcp_header_fails(self):
        with self.assertRaises(IsolationError):
            parse_tcp_listeners("broken", ipv6=False)

    def test_bad_ipv4_length_fails(self):
        with self.assertRaises(IsolationError):
            parse_tcp_listeners(HEADER+V4.replace("00000000:","0000:"), ipv6=False)

    def test_bad_ipv6_length_fails(self):
        with self.assertRaises(IsolationError):
            parse_tcp_listeners(HEADER+V6.replace("00000000000000000000000000000000:0929","ffff:0929"), ipv6=True)

    def stage(self):
        root=Path(tempfile.mkdtemp(prefix="sg-netns-neg-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        links=root/"net"; links.mkdir(); (links/"lo").mkdir()
        (root/"tcp").write_text(HEADER+V4)
        (root/"tcp6").write_text(HEADER)
        return root,links

    def test_external_interface_fails(self):
        root, links=self.stage(); (links/"eth0").mkdir()
        with self.assertRaisesRegex(IsolationError,"unsafe network"):
            check_no_external_interfaces(links)

    def test_missing_ipv6_table_fails(self):
        root, links=self.stage(); (root/"tcp6").unlink()
        with self.assertRaisesRegex(IsolationError,"both IPv4 and IPv6"):
            inspect_network(interfaces=links,tcp4=root/"tcp",tcp6=root/"tcp6")

    def test_missing_listener_fails_closed(self):
        root,links=self.stage(); (root/"tcp").write_text(HEADER)
        with self.assertRaisesRegex(IsolationError,"missing"):
            inspect_network(interfaces=links,tcp4=root/"tcp",tcp6=root/"tcp6",require_listener=True)

    def test_expected_listener_inside_only_lo_allowed(self):
        root,links=self.stage()
        self.assertEqual(inspect_network(interfaces=links,tcp4=root/"tcp",
                                        tcp6=root/"tcp6",require_listener=True),("v4:0.0.0.0",))

    def test_ipv6_listener_is_not_ignored(self):
        root,links=self.stage(); (root/"tcp").write_text(HEADER)
        (root/"tcp6").write_text(HEADER+V6LO)
        self.assertEqual(inspect_network(interfaces=links,tcp4=root/"tcp",
                                        tcp6=root/"tcp6",require_listener=True),("v6:::1",))


    def test_malformed_listener_row_must_reject(self):
        for malformed in ("   0: 00000000:0929\n",
                          "   0: 00000000 00000000:0000 0A\n",
                          "   0: BAD\n"):
            with self.subTest(row=malformed):
                with self.assertRaisesRegex(IsolationError,"malformed"):
                    parse_tcp_listeners(HEADER + malformed, ipv6=False)

    def test_inspect_network_itself_rejects_extra_interface(self):
        root, links = self.stage()
        (links/"eth0").mkdir()
        with self.assertRaisesRegex(IsolationError, "unsafe network"):
            inspect_network(interfaces=links,tcp4=root/"tcp",tcp6=root/"tcp6",
                            require_listener=True)

    def test_successful_local_connection_must_raise(self):
        import socket
        from cloud_rsp_netns_gate import check_no_egress
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as listening:
            listening.bind(("127.0.0.1",0))
            listening.listen(1)
            reachable = listening.getsockname()
            with self.assertRaisesRegex(IsolationError,"unexpectedly available"):
                check_no_egress(((socket.AF_INET,reachable),
                                 (socket.AF_INET6,("::1",1))))

    def test_closed_ports_are_negative_evidence_not_proof_of_isolation(self):
        import socket
        from cloud_rsp_netns_gate import check_no_egress
        # Pick a real local closed IPv4 port, paired with IPv6 loopback port 1.
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as tmp:
            tmp.bind(("127.0.0.1",0))
            closed_port=tmp.getsockname()[1]
        self.assertIsNone(check_no_egress(
            ((socket.AF_INET,("127.0.0.1",closed_port)),
             (socket.AF_INET6,("::1",1)))))
        # Caller must ALSO verify no-network host mode and only-lo interfaces.

    def test_skipping_ipv6_or_allowing_connected_ipv6_is_caught(self):
        import socket
        from unittest.mock import patch
        import cloud_rsp_netns_gate as g
        families=[]
        class FakeSocket:
            def __init__(self,family): self.family=family
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def settimeout(self,value): pass
            def connect(self,address):
                families.append(self.family)
                if self.family==socket.AF_INET:
                    raise ConnectionRefusedError("mock IPv4 denied")
                # Mock IPv6 endpoint is REACHABLE.
        with patch.object(g.socket,"socket",side_effect=lambda family,kind:FakeSocket(family)):
            with self.assertRaisesRegex(IsolationError,"unexpectedly available"):
                g.check_no_egress()
        self.assertEqual(families,[socket.AF_INET,socket.AF_INET6])

    def test_timeout_is_inconclusive_not_a_successful_denial(self):
        import socket
        from unittest.mock import patch
        import cloud_rsp_netns_gate as g
        class TimeoutSocket:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def settimeout(self,value): pass
            def connect(self,address):
                raise socket.timeout("mock timeout")
        with patch.object(g.socket,"socket",return_value=TimeoutSocket()):
            with self.assertRaisesRegex(IsolationError,"inconclusive"):
                g.check_no_egress()

    def test_single_family_probe_must_fail(self):
        import socket
        from cloud_rsp_netns_gate import check_no_egress
        with self.assertRaisesRegex(IsolationError,"both IPv4 and IPv6"):
            check_no_egress(((socket.AF_INET,("127.0.0.1",1)),))


if __name__ == "__main__":
    unittest.main()
