#!/usr/bin/env python3
"""REAL mGBA RSP over loopback; generated 32KiB noncommercial ROM ONLY.

Explicitly exercises PR26 RSP._transmit(), RSP.receive() and PR44 strict
post-resume adapter. NO owner ROM/save, no private transcript, no host input,
no changes to run_capture(), and no arbitrary command-line paths. Running
this module outside --network none is prohibited by network preflights.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

from capture_original_request_rsp import RSP, parse_stop, parse_registers
from pr26_public_strict_resume_adapter import (
    PublicStrictStopAdapter, GENERATED_THUMB_PC,
)
from cloud_rsp_netns_gate import check_no_egress, inspect_network

HOST, PORT = "127.0.0.1", 2345
EXPECTED_GENERATED_SHA256 = (
    "cfa20bc9ccad2131abeedaed0d1d5aa49425f8bce5616370d0b6659c7cd4804b"
)
ALLOWED_PUBLIC_RAW = frozenset((
    b"m080000c0,4",
    b"m08000100,2",
    b"Z0,08000100,2",
    b"z0,08000100,2",
))


def generated_thumb_rom() -> bytes:
    """Original synthetic header and Thumb loop, never based on game data."""
    data = bytearray(32768)
    data[:4] = (0xEA00002E).to_bytes(4, "little")
    data[0xA0:0xAC] = b"RSPFIXTURE01"
    data[0xAC:0xB0] = b"RSP1"
    data[0xB0:0xB2] = b"HB"
    data[0xB2] = 0x96
    data[0xBC] = 0
    data[0xBD] = (-(0x19 + sum(data[0xA0:0xBD]))) & 255
    data[0xC0:0xC4] = bytes.fromhex("00009fe5")  # ARM LDR
    data[0xC4:0xC8] = bytes.fromhex("10ff2fe1")  # ARM BX r0
    data[0xC8:0xCC] = (GENERATED_THUMB_PC | 1).to_bytes(4, "little")
    data[0x100:0x102] = bytes.fromhex("fee7")  # Thumb b .
    result = bytes(data)
    if hashlib.sha256(result).hexdigest() != EXPECTED_GENERATED_SHA256:
        raise RuntimeError("generated public ROM differs from literal expected identity")
    return result


def fixed_public_request(sock: socket.socket, rsp: RSP, payload: bytes) -> bytes:
    """A fixed synthetic-ONLY Z0/z0/read packet, outside private RSP whitelist.

    Intentionally not a generic PR26 RSP.send extension. The prevalidated
    disposable ROM and this source's fixed literals are the only authority.
    Never transplant this helper into run_capture or a private game tool.
    """
    if type(payload) is not bytes or payload not in ALLOWED_PUBLIC_RAW:
        raise ValueError("only exact generated-ROM breakpoint/read packets allowed")
    if not rsp._features_negotiated or rsp._feature_negotiation_failed or rsp.running:
        raise ValueError("public raw request requires stopped negotiated generated session")
    sock.sendall(b"$" + payload + b"#%02x" % (sum(payload) & 255))
    return rsp.receive()  # Actual PR26 ACK/framing, checksum, RLE safeguards


def validate_generated_preflight(stop: str, initial_pc: int,
                                 arm: bytes, thumb: bytes) -> None:
    """Narrow observed Ubuntu 0.10.5 generated startup contract ONLY.

    At first debugger attachment this public fixture's paused startup r15
    was 0x00000000. That is *not* proof of original-game code execution:
    it is solely a reproducible disposable-fixture consistency sentinel.
    """
    if type(stop) is not str or stop != "S02":
        raise RuntimeError("generated public pre-c stop differs from observed S02")
    if type(initial_pc) is not int or initial_pc != 0:
        raise RuntimeError("generated public pre-c startup PC differs from 0")
    if type(arm) is not bytes or arm.lower() != b"00009fe5":
        raise RuntimeError("generated public pre-c ARM entry bytes differ")
    if type(thumb) is not bytes or thumb.lower() != b"fee7":
        raise RuntimeError("generated public pre-c Thumb instruction bytes differ")


def validate_generated_post_cleanup(stop: str) -> None:
    if type(stop) is not str or stop != "S02":
        raise RuntimeError("generated post-z0 stop differs from observed S02")


def run() -> None:
    if len(sys.argv) != 1 or "SOULGOLD_ALLOW_PRIVATE_INPUTS" in os.environ:
        raise RuntimeError("generated-only mGBA test forbids private file arguments")
    inspect_network()
    check_no_egress()
    with tempfile.TemporaryDirectory(prefix="sg-pr26-public-real-socket-") as tmp:
        root = Path(tmp)
        rom = root / "GENERATED_THUMB_ONLY.gba"
        rom.write_bytes(generated_thumb_rom())
        rom.chmod(0o400)
        home = root / "home"
        home.mkdir(mode=0o700)
        child_env = {k: os.environ[k] for k in ("PATH", "DISPLAY", "XAUTHORITY")
                     if k in os.environ}
        child_env.update(HOME=str(home), SDL_AUDIODRIVER="dummy")
        process = subprocess.Popen(
            ["mgba", "-g", str(rom)], cwd=root, env=child_env,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            conn = None
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("disposable mGBA exited before generated GDB listener")
                try:
                    conn = socket.create_connection((HOST, PORT), timeout=1)
                    break
                except OSError:
                    time.sleep(.2)
            if conn is None:
                raise RuntimeError("no generated-ROM loopback GDB listener")
            with conn as sock:
                sock.settimeout(3.0)
                listeners = inspect_network(require_listener=True)
                check_no_egress()
                rsp = RSP(sock)
                strict = PublicStrictStopAdapter(rsp)
                strict.negotiate()
                before = parse_stop(rsp.send("?"))
                initial = parse_registers(rsp.send("g"))[15]
                arm = fixed_public_request(sock, rsp, b"m080000c0,4")
                thumb = fixed_public_request(sock, rsp, b"m08000100,2")
                # All exact pre-c reads/status/PC are validated BEFORE Z0.
                validate_generated_preflight(before, initial, arm, thumb)
                if fixed_public_request(sock, rsp, b"Z0,08000100,2") != b"OK":
                    raise RuntimeError("generated width-2 Z0 not acknowledged")
                # PR44 exactly one c, PR26 real ACK receiver, literal T05 and
                # generated-only PC. Any error poisons adapter; terminate mGBA.
                pc = strict.one_generated_stop(timeout=3.0)
                if pc != GENERATED_THUMB_PC:
                    raise RuntimeError("generated Thumb PC is not exact target")
                if fixed_public_request(sock, rsp, b"z0,08000100,2") != b"OK":
                    raise RuntimeError("generated width-2 z0 cleanup rejected")
                post = parse_stop(rsp.send("?"))
                validate_generated_post_cleanup(post)
                if rsp.running or rsp._feature_negotiation_failed:
                    raise RuntimeError("verified generated stop left unsafe RSP session")
            print("PR26_REAL_MGBA_SOCKET: PASS authentic Ubuntu 0.10.5 loopback GDB RSP")
            print("PR26_REAL_RSP_RECEIVER: PASS exact original ACK/frame/checksum parser")
            print("PUBLIC_QSUPPORTED_LITERAL: swbreak+ and hwbreak+ explicit opt-in")
            print("PUBLIC_GENERATED_STOP: T05hwbreak:;")
            print("PUBLIC_GENERATED_PC: " + hex(pc))
            print("PUBLIC_INITIAL_PC: " + hex(initial))
            print("PUBLIC_BEFORE_AFTER_STOP: " + before + " / " + post)
            print("PUBLIC_GENERATED_SHA256: " + EXPECTED_GENERATED_SHA256)
            print("PUBLIC_LOOPBACK_LISTENERS: " + repr(listeners))
            print("PUBLIC_ONLY_ONE_C: exactly one; no private input, capture, or file")
            print("SOULGOLD_GAME_NATIVE_ACCEPTANCE: 0/20; production 0 percent")
        finally:
            # If a stop, PC, ACK, network check or cleanup is uncertain,
            # kill the disposable emulator, never issue a second c or z0.
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


if __name__ == "__main__":
    run()
