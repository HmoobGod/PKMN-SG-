#!/usr/bin/env python3
"""Hosted-runner compatibility probe. GENERATED NON-GAME fixture ONLY.

No user ROM, battery save, savestate, private GDB transcript, or remote URL
is read. Do not repurpose this script to accept arbitrary ROM paths.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time


PORT = 2345
HOST = "127.0.0.1"
ROM_SIZE = 32768
LOOP_WORD = bytes.fromhex("feffffea")  # ARM b . at 0x080000C0
HEX = re.compile(rb"[0-9a-fA-F]*\Z")


def make_fixture() -> bytes:
    """Construct an original minimal, noncommercial GBA cartridge test image.

    We intentionally do not embed Nintendo's licensed 156-byte header logo.
    We only check GDB ROM-mapped reads, not emulated commercial game boot.
    """
    data = bytearray(ROM_SIZE)
    # ARM branch from 0x08000000 to entry point 0x080000C0.
    data[:4] = (0xEA00002E).to_bytes(4, "little")
    data[0xA0:0xAC] = b"RSPFIXTURE01"
    data[0xAC:0xB0] = b"RSP1"
    data[0xB0:0xB2] = b"HB"
    data[0xB2] = 0x96
    data[0xBC] = 0x00
    data[0xBD] = (-(0x19 + sum(data[0xA0:0xBD]))) & 0xFF
    data[0xC0:0xC4] = LOOP_WORD
    return bytes(data)


def encode_rsp(payload: bytes) -> bytes:
    if not payload or len(payload) > 80 or b"$" in payload or b"#" in payload:
        raise ValueError("invalid outbound RSP command")
    return b"$" + payload + b"#" + f"{sum(payload) & 255:02x}".encode("ascii")


def recv_rsp(sock: socket.socket) -> bytes:
    """Read one checksum-verified frame, ACK it; never log raw registers."""
    # The stub may ACK our request before sending its response.
    while True:
        ch = sock.recv(1)
        if ch == b"$":
            break
        if ch in (b"+",):
            continue
        if ch == b"-":
            raise RuntimeError("GDB stub NAK")
        if not ch:
            raise RuntimeError("GDB stub disconnected before response")
        raise RuntimeError("unexpected GDB framing byte")
    buf = bytearray()
    while True:
        ch = sock.recv(1)
        if not ch:
            raise RuntimeError("GDB stub disconnected mid-frame")
        if ch == b"#":
            break
        if len(buf) >= 16384:
            raise RuntimeError("GDB reply exceeds bounded limit")
        buf.extend(ch)
    checksum = b""
    while len(checksum) < 2:
        part = sock.recv(2 - len(checksum))
        if not part:
            raise RuntimeError("missing RSP checksum")
        checksum += part
    try:
        claimed = int(checksum.decode("ascii"), 16)
    except (ValueError, UnicodeDecodeError):
        sock.sendall(b"-")
        raise RuntimeError("invalid RSP checksum encoding")
    if (sum(buf) & 255) != claimed:
        sock.sendall(b"-")
        raise RuntimeError("RSP checksum mismatch")
    sock.sendall(b"+")
    return bytes(buf)


def request(sock: socket.socket, command: bytes) -> bytes:
    # Explicit allowlist, no continue/step/watchpoints/guest writes.
    if command not in (b"?", b"g", b"m080000c0,4"):
        raise ValueError("non-read-only or non-fixture RSP request forbidden")
    sock.sendall(encode_rsp(command))
    return recv_rsp(sock)


def check_reply(stop: bytes, regs: bytes, rom: bytes) -> None:
    if not (stop.startswith(b"S") or stop.startswith(b"T")):
        raise RuntimeError("not a paused-stop reply")
    if len(regs) < 64 or len(regs) % 2 or not HEX.fullmatch(regs):
        raise RuntimeError("unexpected register reply grammar")
    if rom.lower() != LOOP_WORD.hex().encode("ascii"):
        raise RuntimeError("generated fixture ROM mapping mismatch")


def run() -> None:
    if os.environ.get("SOULGOLD_ALLOW_PRIVATE_INPUTS"):
        raise RuntimeError("private-input flag forbidden in public fixture workflow")
    with tempfile.TemporaryDirectory(prefix="sg-public-rsp-fixture-") as directory:
        root = Path(directory)
        rom_file = root / "generated_public_fixture.gba"
        rom_file.write_bytes(make_fixture())
        os.chmod(rom_file, 0o600)
        # A clean HOME prevents mGBA from loading unrelated user data.
        home = root / "home"
        home.mkdir(mode=0o700)
        env = dict(os.environ, HOME=str(home), SDL_AUDIODRIVER="dummy")
        process = subprocess.Popen(
            ["mgba", "-g", str(rom_file)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=root,
            env=env,
        )
        try:
            deadline = time.monotonic() + 25
            connection = None
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("mGBA exited before debugger connection")
                try:
                    connection = socket.create_connection((HOST, PORT), timeout=1)
                    break
                except OSError:
                    time.sleep(0.25)
            if connection is None:
                raise RuntimeError("real mGBA GDB listener unavailable on loopback")
            with connection as sock:
                sock.settimeout(5)
                stop = request(sock, b"?")
                regs = request(sock, b"g")
                rom = request(sock, b"m080000c0,4")
                check_reply(stop, regs, rom)
            print("PASS: real hosted-runner mGBA GDB RSP ?/g/m fixture-only")
            print("EVIDENCE: paused status, bounded register payload, exact generated ROM mapping")
            print("SCOPE: NO private ROM/save; NO native SoulGold gameplay acceptance")
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


if __name__ == "__main__":
    run()
