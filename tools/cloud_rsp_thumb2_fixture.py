#!/usr/bin/env python3
"""Public 32-KiB synthetic GBA only: Thumb-width-2 RSP breakpoint handshake.

This generated test ROM is NOT SoulGold or a substitute for its private-ROM
identity gate. No c/s/Ctrl-C, guest writes, input injection or game data.
The only breakpoint is an installed/removed Z0 of width 2 at 0x08000100.
"""
from __future__ import annotations

import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

from cloud_mgba_rsp_fixture import (
    HOST, PORT, STOP, HEX, MAX_FRAME, encode_rsp, make_fixture, recv_rsp, request,
)
from cloud_rsp_netns_gate import inspect_network, check_no_egress
from pr26_exact_probe_parser_reference import parse_stop, parse_registers

ARM_LDR = bytes.fromhex("00009fe5")  # ARM LDR r0,[pc,#0] at 0x080000C0
ARM_BX = bytes.fromhex("10ff2fe1")  # ARM BX r0 at 0x080000C4
THUMB_DEST = 0x08000101  # bit 0 selects Thumb when BX executes
THUMB_LOOP = bytes.fromhex("fee7")  # Thumb B . at 0x08000100, not executed here
ARM_READ = b"m080000c0,4"
THUMB_READ = b"m08000100,2"
THUMB_SET = b"Z0,08000100,2"
THUMB_REMOVE = b"z0,08000100,2"


def make_thumb_fixture() -> bytes:
    data = bytearray(make_fixture())
    data[0xC0:0xC4] = ARM_LDR
    data[0xC4:0xC8] = ARM_BX
    data[0xC8:0xCC] = THUMB_DEST.to_bytes(4, "little")
    data[0x100:0x102] = THUMB_LOOP
    return bytes(data)


def thumb_memory(sock: socket.socket, command: bytes) -> bytes:
    if command != THUMB_READ:
        raise ValueError("only generated Thumb instruction read allowed")
    sock.sendall(encode_rsp(command))
    reply = recv_rsp(sock)
    if reply.lower() != THUMB_LOOP.hex().encode("ascii"):
        raise RuntimeError("generated Thumb instruction mapping mismatch")
    return reply


def thumb_breakpoint(sock: socket.socket, command: bytes) -> bytes:
    if command not in (THUMB_SET, THUMB_REMOVE):
        raise ValueError("only generated Thumb Z0/z0 width-2 fixture allowed")
    sock.sendall(encode_rsp(command))
    reply = recv_rsp(sock)
    if reply != b"OK":
        raise RuntimeError("mGBA did not acknowledge exact Thumb-size-2 packet")
    return reply


def thumb_roundtrip(sock: socket.socket) -> tuple[str, int, bytes, str]:
    """Check exact generated read/regs before Z0, always try bounded cleanup."""
    stop = request(sock, b"?")
    regs = request(sock, b"g")
    arm = request(sock, ARM_READ)
    # Combine PR30 bounded framing/grammar and PR26's exact parser functions.
    if len(stop) > 200 or not STOP.fullmatch(stop) or not stop.isascii():
        raise RuntimeError("invalid bounded stop reply")
    if len(regs) < 128 or len(regs) > MAX_FRAME or len(regs) % 2 or not HEX.fullmatch(regs):
        raise RuntimeError("invalid bounded register payload")
    parsed_stop = parse_stop(stop)
    parsed_regs = parse_registers(regs)
    if len(parsed_regs) != 16:
        raise RuntimeError("expected exactly 16 decoded PR26 ARM registers")
    if arm.lower() != ARM_LDR.hex().encode("ascii"):
        raise RuntimeError("generated ARM-to-Thumb entry mapping mismatch")
    thumb = thumb_memory(sock, THUMB_READ)

    # Real GDB response may be missing/corrupted despite a successful install.
    attempted = False
    try:
        attempted = True
        thumb_breakpoint(sock, THUMB_SET)
    finally:
        if attempted:
            try:
                thumb_breakpoint(sock, THUMB_REMOVE)
            except (OSError, ValueError, RuntimeError) as exc:
                raise RuntimeError("Thumb Z0 cleanup failed after attempted install") from exc
    # Reject stale OK used as a stop; this is only reply grammar, not a proof
    # of breakpoint removal or actual execution at the Thumb instruction.
    after = parse_stop(request(sock, b"?"))
    return parsed_stop, len(parsed_regs), thumb, after


def run() -> None:
    if len(sys.argv) != 1 or os.environ.get("SOULGOLD_ALLOW_PRIVATE_INPUTS"):
        raise RuntimeError("public Thumb fixture does not accept private input/flags")
    inspect_network()
    check_no_egress()
    print("THUMB_PRELAUNCH_ISOLATION: only lo; no successful IPv4/IPv6 egress")
    with tempfile.TemporaryDirectory(prefix="sg-generated-thumb2-") as temp:
        root = Path(temp)
        rom = root / "generated_original_thumb2_fixture.gba"
        rom.write_bytes(make_thumb_fixture())
        rom.chmod(0o600)
        home = root / "home"
        home.mkdir(mode=0o700)
        env = {key: os.environ[key] for key in ("PATH", "DISPLAY", "XAUTHORITY")
               if key in os.environ}
        env.update(HOME=str(home), SDL_AUDIODRIVER="dummy")
        process = subprocess.Popen(
            ["mgba", "-g", str(rom)], cwd=root, env=env,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            connection = None
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("mGBA stopped before generated Thumb fixture connection")
                try:
                    connection = socket.create_connection((HOST, PORT), timeout=1)
                    break
                except OSError:
                    time.sleep(0.25)
            if connection is None:
                raise RuntimeError("no generated-fixture GDB listener")
            with connection as sock:
                sock.settimeout(5)
                listeners = inspect_network(require_listener=True)
                check_no_egress()
                stop, words, mem, post = thumb_roundtrip(sock)
            print("PASS: real hosted mGBA generated Thumb width-2 Z0 and z0 handshake")
            print("PR26_PARSER_STOP: " + stop)
            print("PR26_PARSER_WORDS: " + str(words))
            print("THUMB_MEMORY_WORD: " + mem.decode("ascii"))
            print("THUMB_BREAKPOINT_PACKETS: Z0,08000100,2 / z0,08000100,2")
            print("POST_CLEANUP_STOP_GRAMMAR: " + post)
            print("ISOLATED_GDB_LISTENERS: " + repr(listeners))
            print("NO_BREAKPOINT_HIT: c/s was never sent; no private ROM/save")
            print("NATIVE_SOULGOLD_ACCEPTANCE: 0/20; production 0 percent")
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


if __name__ == "__main__":
    run()
