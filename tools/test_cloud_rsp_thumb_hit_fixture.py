#!/usr/bin/env python3
"""One-c-only synthetic breakpoint-hit tests; zero private game dependencies."""
import os
import socket
import unittest
from unittest.mock import MagicMock, patch

from cloud_mgba_rsp_fixture import encode_rsp
import cloud_rsp_thumb_hit_fixture as lab
from cloud_rsp_thumb2_fixture import THUMB_SET, THUMB_REMOVE, THUMB_READ


def regs(pc=0x08000100):
    words = [0]*15 + [pc] + [0x20]
    return b"".join(n.to_bytes(4, "little") for n in words).hex().encode("ascii")


class PublicBreakpointHitTests(unittest.TestCase):
    def pair(self):
        a,b=socket.socketpair()
        a.settimeout(.2); b.settimeout(.2)
        self.addCleanup(a.close); self.addCleanup(b.close)
        return a,b

    def test_only_one_continue_exact_packet(self):
        a,b=self.pair()
        for cmd in (b"s", b"\x03", b"c08000100", b"c;3", b"Z0,08000100,2",
                    b"M08000100,2:ffff", b"vCont;c"):
            with self.subTest(cmd=cmd):
                with self.assertRaises(ValueError):
                    lab.one_continue(a, cmd)
                with self.assertRaises(socket.timeout):
                    b.recv(1)
        b.sendall(encode_rsp(b"S05"))
        self.assertEqual(lab.one_continue(a,b"c"),b"S05")
        self.assertEqual(b.recv(100),encode_rsp(b"c")+b"+")

    def test_socket_timeout_is_not_reported_as_hit(self):
        a,b=self.pair()
        with self.assertRaises(socket.timeout):
            lab.one_continue(a,b"c")
        self.assertEqual(b.recv(100),encode_rsp(b"c"))

    def test_stop_signal_and_pc_prove_narrow_generated_hit(self):
        for stop in (b"S05", b"T05thread:01;"):
            for pc in lab.ALLOWED_STOP_PCS:
                with self.subTest(stop=stop,pc=pc):
                    self.assertEqual(lab.validate_hit(stop,regs(pc)),pc)

    def test_non_sigtrap_and_wrong_pc_fail_closed(self):
        for stop,pc in ((b"S02",0x08000100),(b"S05",0x08000200),
                        (b"S05",0x02000000),(b"OK",0x08000100)):
            with self.subTest(stop=stop,pc=pc):
                with self.assertRaises((ValueError,lab.HitError)):
                    lab.validate_hit(stop,regs(pc))

    def scripted(self, *, initial=b"S02", arm=b"00009fe5",
                 mem=b"fee7", hit=b"S05", pc=0x08000100):
        requests=[initial,regs(),arm,regs(pc)]
        events=[]
        def read(_,command):
            events.append(("read",command))
            return requests.pop(0)
        def thumb_mem(_,command):
            events.append(("mem",command))
            return mem
        def breakpoint(_,command):
            events.append(("bp",command))
            return b"OK"
        def continued(_,command):
            events.append(("c",command))
            return hit
        return events,read,thumb_mem,breakpoint,continued

    def test_ordered_hit_and_exactly_one_cleanup(self):
        events,read,mem,bp,cont=self.scripted()
        with patch.object(lab,"request",side_effect=read), \
             patch.object(lab,"thumb_memory",side_effect=mem), \
             patch.object(lab,"thumb_breakpoint",side_effect=bp), \
             patch.object(lab,"one_continue",side_effect=cont):
            pc,stop,nonstandard=lab.run_one_hit(object())
        self.assertEqual(pc,lab.TARGET_PC)
        self.assertEqual(stop,"S05")
        self.assertFalse(nonstandard)
        self.assertEqual(events,[
            ("read",b"?"),("read",b"g"),("read",b"m080000c0,4"),
            ("mem",THUMB_READ),("bp",THUMB_SET),("c",b"c"),
            ("read",b"g"),("bp",THUMB_REMOVE),
        ])

    def test_exact_public_S05k_requires_separate_diagnostic_and_matching_PC(self):
        self.assertEqual(lab.validate_hit(b"S05k", regs(0x08000100),
                                         diagnostic_nonstandard=True),0x08000100)
        with self.assertRaises(ValueError):
            lab.validate_hit(b"S05k",regs())
        with self.assertRaises(lab.HitError):
            lab.validate_hit(b"S05k",regs(0x08000900),
                             diagnostic_nonstandard=True)
        for malformed in (b"S05x", b"S05k!", b"S05K", b"S05", b"OK"):
            if malformed == b"S05":
                continue
            with self.subTest(malformed=malformed):
                with self.assertRaises((ValueError, lab.HitError)):
                    lab.validate_hit(malformed,regs(),
                                     diagnostic_nonstandard=True)

    def test_nonstandard_exact_observed_frame_requires_real_g_and_cleanup(self):
        events,read,mem,bp,cont=self.scripted(hit=b"S05k")
        with patch.object(lab,"request",side_effect=read), \
             patch.object(lab,"thumb_memory",side_effect=mem), \
             patch.object(lab,"thumb_breakpoint",side_effect=bp), \
             patch.object(lab,"one_continue",side_effect=cont):
            pc,stop,nonstandard=lab.run_one_hit(object())
        self.assertEqual((pc,stop,nonstandard),(lab.TARGET_PC,"S05k",True))
        self.assertEqual([x for x in events if x[0]=="bp"],[
            ("bp",THUMB_SET),("bp",THUMB_REMOVE),
        ])
        self.assertIn(("read",b"g"),events)

    def test_invalid_generated_mapping_never_sends_continue(self):
        events,read,mem,bp,cont=self.scripted(arm=b"ffffffff")
        with patch.object(lab,"request",side_effect=read), \
             patch.object(lab,"thumb_memory",side_effect=mem), \
             patch.object(lab,"thumb_breakpoint",side_effect=bp), \
             patch.object(lab,"one_continue",side_effect=cont):
            with self.assertRaisesRegex(lab.HitError,"ARM entry"):
                lab.run_one_hit(object())
        self.assertFalse(any(x[0] in ("bp","c") for x in events))

    def test_no_stop_reply_means_no_inband_cleanup_while_guest_running(self):
        events,read,mem,bp,cont=self.scripted()
        def hang(_,command):
            events.append(("c",command))
            raise socket.timeout("bounded c reply timeout")
        with patch.object(lab,"request",side_effect=read), \
             patch.object(lab,"thumb_memory",side_effect=mem), \
             patch.object(lab,"thumb_breakpoint",side_effect=bp), \
             patch.object(lab,"one_continue",side_effect=hang):
            with self.assertRaises(socket.timeout):
                lab.run_one_hit(object())
        self.assertEqual([x for x in events if x[0]=="bp"],[("bp",THUMB_SET)])

    def test_non_stop_continue_reply_fails_without_inband_cleanup(self):
        events, read, mem, bp, continued = self.scripted(hit=b"OK")
        with patch.object(lab,"request",side_effect=read), \
             patch.object(lab,"thumb_memory",side_effect=mem), \
             patch.object(lab,"thumb_breakpoint",side_effect=bp), \
             patch.object(lab,"one_continue",side_effect=continued):
            with self.assertRaisesRegex(lab.HitError, "NON-STOP RSP frame len=2 prefix_hex=4f4b"):
                lab.run_one_hit(object())
        self.assertEqual([x for x in events if x[0]=="bp"],[("bp",THUMB_SET)])
        self.assertFalse(("bp",THUMB_REMOVE) in events)

    def test_run_one_hit_rejects_fake_nonstandard_stops_without_cleanup(self):
        # Tests the run_one_hit boundary, not only validate_hit:
        # mutating the observed S05k branch must not accept suffix variants.
        for bad_stop in (b"S05x", b"S05kk"):
            with self.subTest(bad_stop=bad_stop):
                events, read, mem, bp, cont = self.scripted(hit=bad_stop)
                with patch.object(lab, "request", side_effect=read), \
                     patch.object(lab, "thumb_memory", side_effect=mem), \
                     patch.object(lab, "thumb_breakpoint", side_effect=bp), \
                     patch.object(lab, "one_continue", side_effect=cont):
                    with self.assertRaisesRegex(lab.HitError, "NON-STOP RSP frame"):
                        lab.run_one_hit(object())
                self.assertEqual([x for x in events if x[0] == "bp"], [
                    ("bp", THUMB_SET),
                ])
                self.assertEqual([x for x in events if x[0] == "c"], [
                    ("c", b"c"),
                ])
                # No post-resume g and no z0 when stop report is untrustworthy.
                self.assertEqual([x for x in events if x == ("read", b"g")],
                                 [("read", b"g")])

    def test_lost_install_reply_still_attempts_one_remove(self):
        events,read,mem,bp,cont=self.scripted()
        def missing(_,command):
            events.append(("bp",command))
            if command==THUMB_SET:
                raise socket.timeout("missing Z0 reply")
            return b"OK"
        with patch.object(lab,"request",side_effect=read), \
             patch.object(lab,"thumb_memory",side_effect=mem), \
             patch.object(lab,"thumb_breakpoint",side_effect=missing), \
             patch.object(lab,"one_continue",side_effect=cont):
            with self.assertRaises(socket.timeout):
                lab.run_one_hit(object())
        self.assertEqual([x for x in events if x[0]=="bp"],[("bp",THUMB_SET),("bp",THUMB_REMOVE)])
        self.assertFalse(any(x[0]=="c" for x in events))

    def test_private_arguments_and_environment_abort_before_launch(self):
        with patch.object(lab.sys,"argv",["synthetic", "/tmp/user-ROM.gba"]), \
             patch.object(lab,"inspect_network") as net, \
             patch.object(lab.subprocess,"Popen") as popen:
            with self.assertRaisesRegex(RuntimeError,"private paths"):
                lab.main()
            net.assert_not_called(); popen.assert_not_called()
        with patch.object(lab.sys,"argv",["synthetic"]), \
             patch.dict(os.environ,{"SOULGOLD_ALLOW_PRIVATE_INPUTS":""}), \
             patch.object(lab,"inspect_network") as net, \
             patch.object(lab.subprocess,"Popen") as popen:
            with self.assertRaisesRegex(RuntimeError,"private paths"):
                lab.main()
            net.assert_not_called(); popen.assert_not_called()

    def test_prelaunch_network_failure_never_starts_emulator(self):
        with patch.object(lab.sys,"argv",["synthetic"]), \
             patch.object(lab,"inspect_network",side_effect=RuntimeError("unisolated")), \
             patch.object(lab.subprocess,"Popen") as popen:
            with self.assertRaisesRegex(RuntimeError,"unisolated"):
                lab.main()
            popen.assert_not_called()

    def test_timeout_in_running_guest_terminates_disposable_emulator(self):
        proc=MagicMock()
        proc.poll.return_value=None
        proc.wait.return_value=0
        peer=MagicMock()
        peer.__enter__.return_value=peer
        with patch.object(lab.sys,"argv",["synthetic"]), \
             patch.object(lab,"inspect_network",return_value=("v4:127.0.0.1",)), \
             patch.object(lab,"check_no_egress"), \
             patch.object(lab.subprocess,"Popen",return_value=proc), \
             patch.object(lab.socket,"create_connection",return_value=peer), \
             patch.object(lab,"run_one_hit",side_effect=socket.timeout("no stop")):
            with self.assertRaises(socket.timeout):
                lab.main()
        proc.terminate.assert_called_once()
        proc.wait.assert_called_once()


    def test_literal_generated_target_pc_set_is_pinned(self):
        # Deliberately independent of lab constants: catches widened PC guards.
        self.assertEqual(lab.TARGET_PC, 0x08000100)
        self.assertEqual(
            lab.ALLOWED_STOP_PCS,
            frozenset({0x08000100, 0x08000102, 0x08000104}),
        )
        for pc in (0x080000fe, 0x08000106, 0x08000200):
            with self.subTest(pc=pc):
                with self.assertRaises(lab.HitError):
                    lab.validate_hit(b"S05", regs(pc))

    def test_main_exact_isolation_order_child_environment_and_3s_timeout(self):
        # A successful fake mGBA is only used to audit main() integration.
        # The real GDB and sandbox code paths are untouched.
        events = []
        proc = MagicMock()
        proc.poll.return_value = None
        proc.wait.return_value = 0
        sock = MagicMock()
        sock.__enter__.return_value = sock

        def network_check(*, require_listener=False):
            events.append(("network", require_listener))
            return ("v4:127.0.0.1",)

        def egress_check():
            events.append(("egress",))

        def start(argv, **kwargs):
            events.append(("launch",))
            self.assertEqual(argv[:2], ["mgba", "-g"])
            self.assertEqual(len(argv), 3)
            self.assertTrue(argv[2].endswith("original_generated_thumb_hit.gba"))
            self.assertEqual(
                set(kwargs["env"]),
                {"PATH", "DISPLAY", "XAUTHORITY", "HOME", "SDL_AUDIODRIVER"},
            )
            self.assertEqual(kwargs["env"]["SDL_AUDIODRIVER"], "dummy")
            self.assertEqual(os.path.basename(kwargs["env"]["HOME"]), "home")
            self.assertEqual(os.path.dirname(kwargs["env"]["HOME"]), str(kwargs["cwd"]))
            self.assertNotEqual(kwargs["env"]["HOME"], os.environ["HOME"])
            self.assertNotIn("SG_PRIVATE_SENTINEL", kwargs["env"])
            self.assertNotIn("SOULGOLD_ALLOW_PRIVATE_INPUTS", kwargs["env"])
            self.assertEqual(kwargs["stdin"], lab.subprocess.DEVNULL)
            self.assertEqual(kwargs["stdout"], lab.subprocess.DEVNULL)
            self.assertEqual(kwargs["stderr"], lab.subprocess.DEVNULL)
            return proc

        def connect(address, timeout):
            events.append(("connect",))
            self.assertEqual(address, (lab.HOST, lab.PORT))
            self.assertEqual(timeout, 1)
            return sock

        def hit(s):
            events.append(("run",))
            self.assertIs(s, sock)
            return (0x08000100, "S05k", True)

        private_sentinel = {
            "PATH": "/usr/bin", "DISPLAY": ":99", "XAUTHORITY": "/tmp/test-xauth",
            "SG_PRIVATE_SENTINEL": "NEVER_PASS_TO_CHILD",
            "HOME": "/private/inherited-home-must-not-escape",
        }
        with patch.object(lab.sys, "argv", ["synthetic"]), \
             patch.dict(os.environ, private_sentinel, clear=True), \
             patch.object(lab, "inspect_network", side_effect=network_check), \
             patch.object(lab, "check_no_egress", side_effect=egress_check), \
             patch.object(lab.subprocess, "Popen", side_effect=start), \
             patch.object(lab.socket, "create_connection", side_effect=connect), \
             patch.object(lab, "run_one_hit", side_effect=hit):
            lab.main()
        self.assertEqual(events, [
            ("network", False), ("egress",), ("launch",), ("connect",),
            ("network", True), ("egress",), ("run",),
        ])
        sock.settimeout.assert_called_once_with(3.0)
        proc.terminate.assert_called_once()
        proc.wait.assert_called_once_with(timeout=3)

    def test_main_prelaunch_egress_failure_prevents_emulator_launch(self):
        with patch.object(lab.sys, "argv", ["synthetic"]), \
             patch.object(lab, "inspect_network", return_value=()), \
             patch.object(lab, "check_no_egress",
                          side_effect=RuntimeError("prelaunch egress denied")) as egress, \
             patch.object(lab.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(RuntimeError, "prelaunch egress denied"):
                lab.main()
            egress.assert_called_once_with()
            popen.assert_not_called()

    def test_main_postconnect_egress_failure_terminates_without_run(self):
        proc = MagicMock()
        proc.poll.return_value = None
        proc.wait.return_value = 0
        sock = MagicMock()
        sock.__enter__.return_value = sock
        with patch.object(lab.sys, "argv", ["synthetic"]), \
             patch.object(lab, "inspect_network",
                          side_effect=[("prelaunch",), ("postconnect",)]) as network, \
             patch.object(lab, "check_no_egress",
                          side_effect=[None, RuntimeError("postconnect egress denied")]) as egress, \
             patch.object(lab.subprocess, "Popen", return_value=proc), \
             patch.object(lab.socket, "create_connection", return_value=sock), \
             patch.object(lab, "run_one_hit") as hit:
            with self.assertRaisesRegex(RuntimeError, "postconnect egress denied"):
                lab.main()
        self.assertEqual(network.call_count, 2)
        self.assertEqual(egress.call_count, 2)
        sock.settimeout.assert_called_once_with(3.0)
        hit.assert_not_called()
        proc.terminate.assert_called_once()
        proc.wait.assert_called_once_with(timeout=3)


if __name__=="__main__":
    unittest.main()
