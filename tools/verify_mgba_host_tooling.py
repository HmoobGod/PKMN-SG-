#!/usr/bin/env python3
"""Tool-only mGBA AppImage/X11 verification. NEVER loads a ROM, save or debugger session.

Requires Python 3; optional harmless keyboard probe uses Xvfb, xauth, xev,
xdpyinfo, X11 and XTest libraries. No game arguments are accepted.
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import hashlib
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile
import time

EXPECTED_SHA256 = "fdf0a5c1588e1606c38315735cf48a9f9dca3573f32a3947ebc956f8297e85cd"
KEYS = ("Return", "x", "z", "Left", "Right", "Up", "Down")


def run(argv: list[str], *, env: dict[str, str] | None = None, cwd: str | None = None,
        timeout: int = 40) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                          timeout=timeout, check=True)


def verify_appimage(path: Path) -> None:
    if not path.is_file():
        raise RuntimeError("AppImage is missing; retrieve existing Drive copy first")
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError("AppImage SHA-256 differs from the reviewed Drive copy; stop")
    print("PASS AppImage SHA-256 matches pinned Drive file")
    with tempfile.TemporaryDirectory(prefix="sg_mgba_tool_only_") as temp:
        root = Path(temp)
        local = root / "mgba.appimage"
        shutil.copyfile(path, local)
        local.chmod(0o700)
        run([str(local), "--appimage-extract"], cwd=temp, timeout=90)
        qt = root / "squashfs-root" / "usr" / "bin" / "mgba-qt"
        if not qt.is_file():
            raise RuntimeError("Extracted AppImage has no mgba-qt executable")
        version = run([str(qt), "--version"], timeout=15)
        help_text = run([str(qt), "--help"], timeout=15)
        info = version.stdout + version.stderr
        flags = help_text.stdout + help_text.stderr
        if "0.10.5" not in info or "26b7884bc25a5933960f3cdcd98bac1ae14d42e2" not in info:
            raise RuntimeError("Unexpected extracted mGBA version/commit")
        if "--gdb" not in flags or "2345" not in flags:
            raise RuntimeError("mGBA -g/GDB CLI option not advertised")
        print("PASS extracted mGBA 0.10.5 commit and -g GDB CLI (port 2345)")
    # Only --version and --help were run. No ROM was loaded; no GDB socket tested.


def verify_input() -> None:
    for name in ("Xvfb", "xauth", "xev", "xdpyinfo", "stdbuf"):
        if not shutil.which(name):
            raise RuntimeError(f"Missing host tool: {name}")
    if not ctypes.util.find_library("X11") or not ctypes.util.find_library("Xtst"):
        raise RuntimeError("X11/XTest shared library unavailable")
    with tempfile.TemporaryDirectory(prefix="sg_xev_nogame_") as temp:
        root = Path(temp)
        authority = root / "Xauthority"
        authority.touch(mode=0o600)
        # Do not attach to an existing display. Fail closed if no free display.
        candidates = [n for n in range(92, 120)
                      if not Path(f"/tmp/.X11-unix/X{n}").exists()]
        if not candidates:
            raise RuntimeError("No free isolated Xvfb display available")
        display = f":{candidates[0]}"
        run(["xauth", "-f", str(authority), "add", display, ".", secrets.token_hex(16)])
        env = {**os.environ, "HOME": temp, "XDG_CONFIG_HOME": temp,
               "DISPLAY": display, "XAUTHORITY": str(authority),
               "QT_QPA_PLATFORM": "xcb", "SDL_AUDIODRIVER": "dummy"}
        procs: list[subprocess.Popen] = []
        with (root / "xev.log").open("w") as log:
            try:
                procs.append(subprocess.Popen([
                    "Xvfb", display, "-screen", "0", "800x600x24",
                    "-nolisten", "tcp", "-auth", str(authority)],
                    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
                for _ in range(60):
                    if subprocess.run(["xdpyinfo", "-display", display], env=env,
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL).returncode == 0:
                        break
                    time.sleep(0.1)
                else:
                    raise RuntimeError("Isolated Xvfb did not start")
                procs.append(subprocess.Popen([
                    "stdbuf", "-oL", "xev", "-name", "SG No Game Input Probe",
                    "-event", "keyboard", "-geometry", "350x180"],
                    env=env, stdout=log, stderr=subprocess.DEVNULL))
                window = None
                for _ in range(70):
                    log.flush()
                    m = re.search(r"Outer window is (0x[0-9a-fA-F]+)",
                                  (root / "xev.log").read_text())
                    if m:
                        window = int(m.group(1), 16)
                        break
                    time.sleep(0.1)
                if window is None:
                    raise RuntimeError("Harmless xev window did not appear")
                libx11 = ctypes.CDLL(ctypes.util.find_library("X11"))
                libxtst = ctypes.CDLL(ctypes.util.find_library("Xtst"))
                libx11.XOpenDisplay.argtypes = [ctypes.c_char_p]
                libx11.XOpenDisplay.restype = ctypes.c_void_p
                libx11.XCloseDisplay.argtypes = [ctypes.c_void_p]
                libx11.XSetInputFocus.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
                                                 ctypes.c_int, ctypes.c_ulong]
                libx11.XGetInputFocus.argtypes = [ctypes.c_void_p,
                                                 ctypes.POINTER(ctypes.c_ulong),
                                                 ctypes.POINTER(ctypes.c_int)]
                libx11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
                libx11.XStringToKeysym.argtypes = [ctypes.c_char_p]
                libx11.XStringToKeysym.restype = ctypes.c_ulong
                libx11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
                libx11.XKeysymToKeycode.restype = ctypes.c_uint
                libx11.XFlush.argtypes = [ctypes.c_void_p]
                libxtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p,
                                                     ctypes.c_uint, ctypes.c_int,
                                                     ctypes.c_ulong]
                libxtst.XTestFakeKeyEvent.restype = ctypes.c_int
                previous_display = os.environ.get("DISPLAY")
                previous_authority = os.environ.get("XAUTHORITY")
                os.environ["DISPLAY"] = display
                os.environ["XAUTHORITY"] = str(authority)
                dpy = libx11.XOpenDisplay(display.encode())
                try:
                    if not dpy:
                        raise RuntimeError("XOpenDisplay refused isolated display")
                    # wmctrl segfaulted on this host; direct X11 focus passed.
                    libx11.XSetInputFocus(dpy, window, 2, 0)
                    libx11.XSync(dpy, 0)
                    focused = ctypes.c_ulong()
                    revert = ctypes.c_int()
                    libx11.XGetInputFocus(dpy, ctypes.byref(focused),
                                         ctypes.byref(revert))
                    if focused.value != window:
                        raise RuntimeError("Focus did not reach harmless xev window")
                    for key in KEYS:
                        sym = libx11.XStringToKeysym(key.encode())
                        code = libx11.XKeysymToKeycode(dpy, sym)
                        if not code:
                            raise RuntimeError(f"No X11 keycode: {key}")
                        if libxtst.XTestFakeKeyEvent(dpy, code, 1, 0) != 1:
                            raise RuntimeError(f"Key press refused: {key}")
                        if libxtst.XTestFakeKeyEvent(dpy, code, 0, 0) != 1:
                            raise RuntimeError(f"Key release refused: {key}")
                        libx11.XFlush(dpy)
                        time.sleep(0.09)
                finally:
                    if dpy:
                        libx11.XCloseDisplay(dpy)
                    for key, old in (("DISPLAY", previous_display),
                                     ("XAUTHORITY", previous_authority)):
                        if old is None:
                            os.environ.pop(key, None)
                        else:
                            os.environ[key] = old
                time.sleep(0.4)
                log.flush()
                received = set(re.findall(r"keysym\s+0x[0-9a-fA-F]+,\s+([^)]*)\)",
                                          (root / "xev.log").read_text()))
                if not set(KEYS).issubset(received):
                    raise RuntimeError("Keyboard receipt incomplete: " +
                                       ",".join(sorted(set(KEYS) - received)))
                print("PASS isolated Xvfb focus and seven xev keyboard events")
            finally:
                for p in reversed(procs):
                    if p.poll() is None:
                        p.terminate()
                for p in reversed(procs):
                    try:
                        p.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.wait(timeout=2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--appimage", required=True, type=Path,
                        help="Existing mGBA 0.10.5 AppImage; NEVER a game file")
    parser.add_argument("--probe-input", action="store_true",
                        help="Exercise seven keys against a harmless xev window")
    args = parser.parse_args()
    verify_appimage(args.appimage)
    if args.probe_input:
        verify_input()
    print("PASS TOOL-ONLY; no game executed, GDB gameplay untested")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        raise SystemExit("FAIL CLOSED: " + str(exc)) from None
