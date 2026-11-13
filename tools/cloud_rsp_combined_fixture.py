#!/usr/bin/env python3
"""PUBLIC synthesized ROM ONLY: approved parser and Z0 combined inside no-network container.

PR26's original capture runner requires exact modified commercial ROM/save hashes;
this harness ONLY imports its original parse_stop/parse_registers functions.
No private file interface or c/s/control, never a native SoulGold test.
"""
from __future__ import annotations

import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

from cloud_mgba_rsp_fixture import HOST, PORT, make_fixture, request
from cloud_mgba_z0_fixture import roundtrip
from cloud_rsp_netns_gate import IsolationError, inspect_network, check_no_egress
from pr26_exact_probe_parser_reference import parse_registers, parse_stop


def verified_post_cleanup_stop(sock: socket.socket) -> str:
    """An unexpected/stale OK must NOT be mistaken for a stop reply."""
    return parse_stop(request(sock, b"?"))


def run() -> None:
    if len(sys.argv) != 1 or os.environ.get("SOULGOLD_ALLOW_PRIVATE_INPUTS"):
        raise RuntimeError("combined PUBLIC fixture accepts no private ROM/save paths or flags")

    # BOTH guards run before any emulator process or fixture IO.
    inspect_network()
    check_no_egress()
    print("PRELAUNCH_NETWORK_GUARD: only lo, both IP families checked, no successful egress")
    with tempfile.TemporaryDirectory(prefix="sg-public-combined-") as folder:
        root=Path(folder)
        image=root/"generated_original_public_32k_fixture.gba"
        image.write_bytes(make_fixture())
        image.chmod(0o600)
        home=root/"home"
        home.mkdir(mode=0o700)
        env={k:os.environ[k] for k in ("PATH","DISPLAY","XAUTHORITY") if k in os.environ}
        env.update(HOME=str(home), SDL_AUDIODRIVER="dummy")
        process=subprocess.Popen(["mgba","-g",str(image)], cwd=root, env=env,
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        try:
            deadline=time.monotonic()+25
            connection=None
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("mGBA unexpectedly exited")
                try:
                    connection=socket.create_connection((HOST,PORT),timeout=1)
                    break
                except OSError:
                    time.sleep(.25)
            if connection is None:
                raise RuntimeError("no real fixture GDB listener in isolated namespace")
            with connection as sock:
                sock.settimeout(5)
                listeners=inspect_network(require_listener=True)
                check_no_egress()
                stop, regs, mem=roundtrip(sock)
                # Execute unchanged parser functions copied from PR26 exact head.
                decoded_stop=parse_stop(stop)
                decoded_regs=parse_registers(regs)
                if len(decoded_regs)!=16:
                    raise RuntimeError("PR26 register parser did not yield 16 ARM registers")
                # Additional bounded post-cleanup read detects a queued stale OK.
                after=verified_post_cleanup_stop(sock)
            print("PASS: real hosted no-network generated-fixture mGBA ?/g/m + Z0/z0")
            print("PR26_EXACT_PARSER_STOP: "+decoded_stop)
            print("PR26_EXACT_PARSER_REG_WORDS: "+str(len(decoded_regs)))
            print("REGISTER_BYTES: "+str(len(regs)//2))
            print("PUBLIC_FIXTURE_ROM_WORD: "+mem.decode("ascii"))
            print("POST_Z0_REMOVAL_STOP_GRAMMAR: "+after)
            print("LISTENERS_INSIDE_NETWORK_NONE: "+repr(listeners))
            print("SCOPE: no private ROM/save; no c/s, no breakpoint hit; PR26 FULL probe not run")
            print("NATIVE_SOULGOLD_ACCEPTANCE: 0/20, production 0 percent")
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)

if __name__=="__main__":
    run()
