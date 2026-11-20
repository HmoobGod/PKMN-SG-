#!/usr/bin/env python3
"""ROM-free mGBA 0.10.5 GDB readiness witness over isolated loopback.

Only a hardcoded, original 32KiB PR45 public-generated inert Thumb fixture
is run in an isolated network namespace. Never reads private games/saves.
Only source-allowlisted qSupported, read-only ?/g/m are sent. No breakpoints.
Pure Z1 stop classification cannot install a breakpoint or mutate a guest.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time

APPIMAGE_SHA256 = "fdf0a5c1588e1606c38315735cf48a9f9dca3573f32a3947ebc956f8297e85cd"
APPIMAGE_SIZE = 25208000
MGBA_VERSION_COMMIT = "26b7884bc25a5933960f3cdcd98bac1ae14d42e2"
FIXTURE_SHA256 = "cfa20bc9ccad2131abeedaed0d1d5aa49425f8bce5616370d0b6659c7cd4804b"
HOST, PORT = "127.0.0.1", 2345
FEATURE_QUERY = "qSupported:swbreak+;hwbreak+"


class PreflightError(RuntimeError):
    pass


class InconclusiveStop(PreflightError):
    """An ambiguous debugger stop is NOT evidence of a reached instruction."""
    pass


def generated_fixture() -> bytes:
    """PR45-authenticated synthetic loop, generated in temporary private host area."""
    data = bytearray(32768)
    data[:4] = (0xEA00002E).to_bytes(4, "little")
    data[0xA0:0xAC] = b"RSPFIXTURE01"
    data[0xAC:0xB0] = b"RSP1"
    data[0xB0:0xB2] = b"HB"
    data[0xB2] = 0x96
    data[0xBC] = 0
    data[0xBD] = (-(0x19 + sum(data[0xA0:0xBD]))) & 255
    data[0xC0:0xC4] = bytes.fromhex("00009fe5")
    data[0xC4:0xC8] = bytes.fromhex("10ff2fe1")
    data[0xC8:0xCC] = (0x08000101).to_bytes(4, "little")
    data[0x100:0x102] = bytes.fromhex("fee7")
    result = bytes(data)
    if hashlib.sha256(result).hexdigest() != FIXTURE_SHA256:
        raise PreflightError("generated-only fixture identity mismatch")
    return result


def read_byte(sock: socket.socket) -> bytes:
    value = sock.recv(1)
    if len(value) != 1:
        raise PreflightError("GDB socket closed during packet")
    return value


def readonly_rsp(sock: socket.socket, request: str) -> str:
    if request not in (FEATURE_QUERY, "?", "g", "m080000c0,4", "m08000100,2"):
        raise PreflightError("RSP command not on generated-fixture read-only allowlist")
    # Once ANY packet is sent, a transport failure poisons this connection.
    # Never retry the request, reconnect, or infer that debugger is ready.
    try:
        payload = request.encode("ascii")
        sock.sendall(b"$" + payload + (b"#%02x" % (sum(payload) & 255)))
        if read_byte(sock) != b"+":
            raise PreflightError("no RSP command ACK")
        if read_byte(sock) != b"$":
            raise PreflightError("missing RSP response frame")
        body = bytearray()
        while True:
            value = read_byte(sock)
            if value == b"#":
                break
            body.extend(value)
            if len(body) > 8192:
                raise PreflightError("RSP response exceeds safe limit")
        trailer = read_byte(sock) + read_byte(sock)
        try:
            checksum = int(trailer, 16)
        except ValueError as error:
            raise PreflightError("nonhex RSP checksum") from error
        if checksum != (sum(body) & 255):
            raise PreflightError("RSP response checksum mismatch")
        sock.sendall(b"+")
        try:
            return body.decode("ascii")
        except UnicodeError as error:
            raise PreflightError("nonascii RSP response") from error
    except OSError as error:
        raise PreflightError("RSP transport failed after connection; never retry") from error


def validate_supported_breakpoint_features(reply: str) -> tuple[str, ...]:
    """Fail closed on partial, contradictory or duplicated qSupported features.

    The mGBA 0.10.5 source replies with feature tokens after processing the
    offered swbreak+ AND hwbreak+ flags. Valid response alone proves only the
    protocol exchange; it does not prove a breakpoint stop or a game event.
    """
    if not isinstance(reply, str) or not reply or len(reply) > 1024:
        raise PreflightError("malformed qSupported response")
    tokens = reply.split(";")
    if any(not token for token in tokens):
        raise PreflightError("empty qSupported feature")
    for capability in ("swbreak+", "hwbreak+"):
        if tokens.count(capability) != 1:
            raise PreflightError(f"qSupported missing/duplicated {capability}")
    if any(token.startswith(("swbreak", "hwbreak"))
           and token not in ("swbreak+", "hwbreak+") for token in tokens):
        raise PreflightError("contradictory qSupported breakpoint capability")
    return tuple(tokens)


def negotiate_breakpoint_features(sock: socket.socket) -> tuple[str, ...]:
    """Advertise both stop-reason flags before any future Z1 use.

    This synthetic readiness preflight sends NO Z1, watchpoint, step or continue.
    A later authorized client must negotiate on its OWN connection: the state
    is connection-local and any subsequent qSupported resets the server flags.
    """
    reply = readonly_rsp(sock, FEATURE_QUERY)
    return validate_supported_breakpoint_features(reply)


def require_exact_z1_stop(stop: str, registers: str, expected_pc: int) -> dict:
    """Pure validator only; requires an independently obtained stopped 'g'.

    S05k is mGBA's fallback when both negotiated flags or the breakpoint
    metadata are missing. A checksum-correct stop packet alone is insufficient.
    Only exact T05hwbreak:; + independently matching PC is admissible.
    """
    if stop == "S05k":
        raise InconclusiveStop("S05k: breakpoint details absent; never infer Z1 hit")
    if stop != "T05hwbreak:;":
        raise InconclusiveStop("unexpected/ambiguous breakpoint stop reason")
    if type(expected_pc) is not int or not (0x08000000 <= expected_pc < 0x0A000000) or expected_pc % 2:
        raise PreflightError("invalid expected Thumb instruction address")
    if not isinstance(registers, str) or not re.fullmatch(r"[0-9A-Fa-f]{136}", registers):
        raise InconclusiveStop("missing/malformed stopped register packet")
    pc = int.from_bytes(bytes.fromhex(registers[120:128]), "little")
    if pc != expected_pc:
        raise InconclusiveStop("hardware breakpoint stop PC mismatch")
    return {"reason": "hwbreak", "pc": pc}


def connect_until_listening(process: subprocess.Popen, *, timeout: float = 12.0,
                            dial=socket.create_connection) -> tuple[socket.socket, int]:
    """Retry only PRE-CONNECT transient errors. Do not reconnect after RSP starts."""
    end = time.monotonic() + timeout
    tries = 0
    while time.monotonic() < end and tries < 100:
        if process.poll() is not None:
            raise PreflightError("emulator exited before debugger became ready")
        tries += 1
        try:
            return dial((HOST, PORT), timeout=min(1.0, max(.05, end-time.monotonic()))), tries
        except (ConnectionRefusedError, ConnectionAbortedError, socket.timeout):
            # ECONNREFUSED: no listener yet. ECONNABORTED: handshake aborted.
            # Both are preconnect-only and bounded by a real monotonic deadline.
            time.sleep(min(.15, max(0.0, end-time.monotonic())))
        except OSError as error:
            raise PreflightError("non-retryable initial TCP error") from error
    raise PreflightError("no GDB listener before bounded readiness deadline")


def assert_only_loopback() -> None:
    # This must execute inside a brand-new unshare --net user namespace.
    subprocess.run(["ip", "link", "set", "lo", "up"], check=True, timeout=3,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    links = subprocess.run(["ip", "-o", "link", "show"], check=True, text=True,
                           capture_output=True, timeout=3).stdout.splitlines()
    if len(links) != 1 or not re.match(r"^1: lo: <[^>]*UP", links[0]):
        raise PreflightError("namespace has non-loopback interface or lo is down")
    route = subprocess.run(["ip", "route"], check=True, text=True,
                           capture_output=True, timeout=3).stdout
    if "default" in route:
        raise PreflightError("unexpected external route in namespace")
    print("PASS isolated namespace has exactly one enabled loopback interface", flush=True)


def read_program_version(exe: Path) -> None:
    version = subprocess.run([str(exe), "--version"], check=True, text=True,
                             capture_output=True, timeout=10)
    if "0.10.5" not in (version.stdout + version.stderr) or MGBA_VERSION_COMMIT not in (version.stdout + version.stderr):
        raise PreflightError("mGBA executable self-reported version mismatch")


def inside_namespace(exe: Path) -> None:
    assert_only_loopback()
    read_program_version(exe)
    with tempfile.TemporaryDirectory(prefix="sg_public_rsp_fixture_") as temporary:
        root = Path(temporary)
        fixture = root / "GENERATED_THUMB_ONLY.gba"
        fixture.write_bytes(generated_fixture())
        fixture.chmod(0o400)
        home = root / "home"
        home.mkdir(mode=0o700)
        env = {k: os.environ[k] for k in ("PATH", "DISPLAY", "XAUTHORITY") if k in os.environ}
        env.update(HOME=str(home), XDG_CONFIG_HOME=str(home), QT_QPA_PLATFORM="xcb",
                   SDL_AUDIODRIVER="dummy", LIBGL_ALWAYS_SOFTWARE="1", QT_OPENGL="software")
        process = subprocess.Popen([str(exe), "-g", str(fixture)], cwd=root,
                                   env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            sock, tries = connect_until_listening(process)
            with sock:
                sock.settimeout(4.0)
                # Explicit feature negotiation precedes all future Z1 use.
                # This tool does not install Z1. Its own packet allowlist stays
                # limited to qSupported + read-only synthetic inspections.
                caps = negotiate_breakpoint_features(sock)
                print("PASS qSupported:swbreak+;hwbreak+ accepted and both supported", flush=True)
                # An ACK + checksummed response proves server processes packets.
                stop = readonly_rsp(sock, "?")
                registers = readonly_rsp(sock, "g")
                arm = readonly_rsp(sock, "m080000c0,4")
                thumb = readonly_rsp(sock, "m08000100,2")
                if stop != "S02":
                    raise PreflightError("mGBA ? did not return expected synthetic S02")
                if len(registers) != 136 or not re.fullmatch(r"[0-9A-Fa-f]{136}", registers):
                    raise PreflightError("invalid genuine synthetic register packet")
                if arm.lower() != "00009fe5" or thumb.lower() != "fee7":
                    raise PreflightError("GDB mapped program not the pinned synthetic fixture")
                print(f"PASS actual mGBA GDB: TCP attempt {tries}; ?={stop}; g={len(registers)} hex; synthetic ARM={arm}, Thumb={thumb}", flush=True)
                print("PASS GDB READY: qSupported + ?/g/m only; no private game or breakpoints", flush=True)
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


def verify_host(appimage: Path, script: Path) -> None:
    if appimage.name != "mGBA-0.10.5-appimage-x64.appimage" or not appimage.is_file():
        raise PreflightError("expected existing original mGBA AppImage; game path forbidden")
    if appimage.stat().st_size != APPIMAGE_SIZE:
        raise PreflightError("mGBA AppImage size mismatch")
    with appimage.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest() != APPIMAGE_SHA256:
            raise PreflightError("mGBA AppImage digest mismatch")
    for tool in ("Xvfb", "xauth", "xdpyinfo", "unshare", "ip"):
        if not shutil.which(tool):
            raise PreflightError(f"required host prerequisite not available: {tool}")
    print("PASS pinned Drive mGBA AppImage size + SHA256", flush=True)
    with tempfile.TemporaryDirectory(prefix="sg_mgba_toolonly_rsp_") as temporary:
        root = Path(temporary)
        copied = root / "mgba.appimage"
        shutil.copyfile(appimage, copied)
        copied.chmod(0o700)
        subprocess.run([str(copied), "--appimage-extract"], check=True, cwd=root,
                       timeout=90, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        exe = root / "squashfs-root/usr/bin/mgba-qt"
        if not exe.is_file():
            raise PreflightError("extracted Qt executable absent")
        read_program_version(exe)
        print("PASS verified extracted mGBA 0.10.5", flush=True)
        candidates = [i for i in range(151, 198)
                      if not Path(f"/tmp/.X11-unix/X{i}").exists()
                      and not Path(f"/tmp/.X{i}-lock").exists()]
        if not candidates:
            raise PreflightError("no free isolated Xvfb display")
        display = f":{candidates[0]}"
        authority = root / "Xauthority"
        authority.touch(mode=0o600)
        subprocess.run(["xauth", "-f", str(authority), "add", display, ".",
                        secrets.token_hex(16)], check=True, timeout=8)
        env = {**os.environ, "DISPLAY": display, "XAUTHORITY": str(authority),
               "QT_QPA_PLATFORM": "xcb", "SDL_AUDIODRIVER": "dummy"}
        xvfb = subprocess.Popen(["Xvfb", display, "-screen", "0", "800x600x24",
                                 "-nolisten", "tcp", "-auth", str(authority)],
                                env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(70):
                if xvfb.poll() is not None:
                    raise PreflightError("Xvfb exited unexpectedly")
                if subprocess.run(["xdpyinfo", "-display", display], env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                  timeout=2).returncode == 0:
                    break
                time.sleep(.1)
            else:
                raise PreflightError("isolated Xvfb did not become ready")
            # -n maps user ID; network namespace begins with lo DOWN, child enables it.
            subprocess.run(["unshare", "--user", "--map-root-user", "--net",
                            sys.executable, str(script), "--_internal_synthetic", str(exe)],
                           env=env, check=True, timeout=32)
        finally:
            if xvfb.poll() is None:
                xvfb.terminate()
            try:
                xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                xvfb.wait(timeout=3)
    print("PASS all private tool-only processes/resources stopped and removed", flush=True)


def main() -> None:
    # Internal switch is not a user-supplied ROM mode; its sole code path creates
    # our exact public synthetic fixture. Keep this outside any gameplay harness.
    if len(sys.argv) == 3 and sys.argv[1] == "--_internal_synthetic":
        inside_namespace(Path(sys.argv[2]))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--appimage", required=True, type=Path)
    args = parser.parse_args()
    verify_host(args.appimage, Path(__file__).resolve())


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as error:
        raise SystemExit(f"FAIL CLOSED: {type(error).__name__}: {error}") from None
