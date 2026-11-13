#!/usr/bin/env python3
"""Public generated-ROM GDB breakpoint installation/removal. NEVER run game ROM."""
from __future__ import annotations
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from cloud_mgba_rsp_fixture import (
    HOST, PORT, check_reply, encode_rsp, make_fixture, recv_rsp, request,
)

SET = b"Z0,080000c0,4"
REMOVE = b"z0,080000c0,4"

def breakpoint_request(sock: socket.socket, command: bytes) -> bytes:
    if command not in (SET, REMOVE):
        raise ValueError("forbidden command or non-fixture breakpoint")
    sock.sendall(encode_rsp(command))
    reply = recv_rsp(sock)
    if reply != b"OK":
        raise RuntimeError("stub did not acknowledge fixture breakpoint command")
    return reply

def roundtrip(sock: socket.socket) -> tuple[bytes, bytes, bytes]:
    stop = request(sock, b"?")
    regs = request(sock, b"g")
    rom = request(sock, b"m080000c0,4")
    check_reply(stop, regs, rom)
    installed = False
    try:
        breakpoint_request(sock, SET)
        installed = True
    finally:
        if installed:
            breakpoint_request(sock, REMOVE)
    return stop, regs, rom

def run() -> None:
    if os.environ.get("SOULGOLD_ALLOW_PRIVATE_INPUTS"):
        raise RuntimeError("private mode forbidden")
    with tempfile.TemporaryDirectory(prefix="sg-public-z0-only-") as directory:
        root = Path(directory)
        rom = root / "generated_original_fixture.gba"
        rom.write_bytes(make_fixture())
        rom.chmod(0o600)
        home = root / "home"
        home.mkdir(mode=0o700)
        env = {k: os.environ[k] for k in ("PATH", "DISPLAY", "XAUTHORITY") if k in os.environ}
        env.update(HOME=str(home), SDL_AUDIODRIVER="dummy")
        p = subprocess.Popen(
            ["mgba", "-g", str(rom)], cwd=root, env=env,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 25
            sock = None
            while time.monotonic() < deadline:
                if p.poll() is not None:
                    raise RuntimeError("emulator exited before connection")
                try:
                    sock = socket.create_connection((HOST, PORT), timeout=1)
                    break
                except OSError:
                    time.sleep(0.25)
            if sock is None:
                raise RuntimeError("no real mGBA GDB listener")
            with sock:
                sock.settimeout(5)
                stop, regs, mem = roundtrip(sock)
            print("PASS: real hosted mGBA public fixture Z0 install and z0 removal")
            print("STOP_BEFORE_INSTALL: " + stop.decode("ascii"))
            print("REGISTER_BYTES: " + str(len(regs)//2))
            print("ROM_WORD: " + mem.decode("ascii"))
            print("PACKETS: Z0,080000c0,4 / z0,080000c0,4")
            print("NO_BREAKPOINT_HIT: no continue or step was issued")
            print("NATIVE_SOULGOLD_ACCEPTANCE: 0/20; no private game data")
        finally:
            if p.poll() is None:
                p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=3)

if __name__ == "__main__":
    run()
