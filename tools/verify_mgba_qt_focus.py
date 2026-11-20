#!/usr/bin/env python3
"""Fail-closed, ROM-free mGBA 0.10.5 Qt focus probe on isolated Xvfb.

Only launches the EMPTY mGBA Qt GUI and opens/closes a harmless file dialog.
Never accepts or opens a ROM, save, debugger session, patch, or game file.
"""
from __future__ import annotations

import argparse
import ctypes as C
import ctypes.util
import hashlib
import os
import re
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import time

APPIMAGE_SHA256 = "fdf0a5c1588e1606c38315735cf48a9f9dca3573f32a3947ebc956f8297e85cd"
MGBA_COMMIT = "26b7884bc25a5933960f3cdcd98bac1ae14d42e2"
IS_VIEWABLE = 2
# Running games add a title/FPS. Exact Qt identity, map state and dimensions
# are separately required; never match the word mGBA fuzzily.
MAIN_TITLE = re.compile(r"^mGBA - (?:0\.10\.5|[A-Za-z0-9][A-Za-z0-9 ._()\-]{0,95}(?: \([0-9]{1,3}(?:\.[0-9])? fps\))? - 0\.10\.5)$")


class XWindowAttributes(C.Structure):
    _fields_ = [
        ("x", C.c_int), ("y", C.c_int), ("width", C.c_int), ("height", C.c_int),
        ("border_width", C.c_int), ("depth", C.c_int), ("visual", C.c_void_p),
        ("root", C.c_ulong), ("window_class", C.c_int),
        ("bit_gravity", C.c_int), ("win_gravity", C.c_int),
        ("backing_store", C.c_int), ("backing_planes", C.c_ulong),
        ("backing_pixel", C.c_ulong), ("save_under", C.c_int),
        ("colormap", C.c_ulong), ("map_installed", C.c_int),
        ("map_state", C.c_int), ("all_event_masks", C.c_long),
        ("your_event_mask", C.c_long), ("do_not_propagate_mask", C.c_long),
        ("override_redirect", C.c_int), ("screen", C.c_void_p),
    ]


class XClassHint(C.Structure):
    _fields_ = [("res_name", C.c_void_p), ("res_class", C.c_void_p)]


class XErrorEvent(C.Structure):
    _fields_ = [("type", C.c_int), ("display", C.c_void_p),
                ("resourceid", C.c_ulong), ("serial", C.c_ulong),
                ("error_code", C.c_ubyte), ("request_code", C.c_ubyte),
                ("minor_code", C.c_ubyte)]


XERROR_CB = C.CFUNCTYPE(C.c_int, C.c_void_p, C.POINTER(XErrorEvent))


class XClient:
    def __init__(self, display: str):
        x11_path = ctypes_or_fail("X11")
        xtst_path = ctypes_or_fail("Xtst")
        self.x = C.CDLL(x11_path)
        self.xt = C.CDLL(xtst_path)
        self.errors: list[tuple[int, int]] = []
        self.x.XOpenDisplay.argtypes = [C.c_char_p]
        self.x.XOpenDisplay.restype = C.c_void_p
        self.x.XDefaultRootWindow.argtypes = [C.c_void_p]
        self.x.XDefaultRootWindow.restype = C.c_ulong
        self.x.XQueryTree.argtypes = [C.c_void_p, C.c_ulong,
                                     C.POINTER(C.c_ulong), C.POINTER(C.c_ulong),
                                     C.POINTER(C.POINTER(C.c_ulong)), C.POINTER(C.c_uint)]
        self.x.XQueryTree.restype = C.c_int
        self.x.XFetchName.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_void_p)]
        self.x.XFetchName.restype = C.c_int
        self.x.XGetClassHint.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(XClassHint)]
        self.x.XGetClassHint.restype = C.c_int
        self.x.XGetWindowAttributes.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(XWindowAttributes)]
        self.x.XGetWindowAttributes.restype = C.c_int
        self.x.XFree.argtypes = [C.c_void_p]
        self.x.XSetInputFocus.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_ulong]
        self.x.XGetInputFocus.argtypes = [C.c_void_p, C.POINTER(C.c_ulong), C.POINTER(C.c_int)]
        self.x.XSync.argtypes = [C.c_void_p, C.c_int]
        self.x.XStringToKeysym.argtypes = [C.c_char_p]
        self.x.XStringToKeysym.restype = C.c_ulong
        self.x.XKeysymToKeycode.argtypes = [C.c_void_p, C.c_ulong]
        self.x.XKeysymToKeycode.restype = C.c_uint
        self.xt.XTestFakeKeyEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
        self.xt.XTestFakeKeyEvent.restype = C.c_int
        self.x.XStoreName.argtypes = [C.c_void_p, C.c_ulong, C.c_char_p]
        self.x.XCloseDisplay.argtypes = [C.c_void_p]
        self.x.XSetErrorHandler.argtypes = [XERROR_CB]
        self.x.XSetErrorHandler.restype = C.c_void_p

        def handle_error(_dpy: C.c_void_p, event: C.POINTER(XErrorEvent)) -> int:
            self.errors.append((int(event.contents.error_code), int(event.contents.request_code)))
            return 0

        self._handler = XERROR_CB(handle_error)
        self.x.XSetErrorHandler(self._handler)
        # Inherit XAUTHORITY from the caller environment, set before XOpenDisplay.
        self.dpy = self.x.XOpenDisplay(display.encode())
        if not self.dpy:
            raise RuntimeError("XOpenDisplay failed: DISPLAY/XAUTHORITY mismatch")

    def check(self) -> None:
        self.x.XSync(self.dpy, 0)
        if self.errors:
            raise RuntimeError(f"X11 request failed; first X error={self.errors[0]}")

    def windows(self) -> list[dict]:
        root = self.x.XDefaultRootWindow(self.dpy)
        root_out, parent = C.c_ulong(), C.c_ulong()
        children = C.POINTER(C.c_ulong)()
        count = C.c_uint()
        if not self.x.XQueryTree(self.dpy, root, C.byref(root_out), C.byref(parent),
                                 C.byref(children), C.byref(count)):
            raise RuntimeError("XQueryTree failed")
        ids = [int(children[i]) for i in range(count.value)]
        if children:
            self.x.XFree(C.cast(children, C.c_void_p))
        found = []
        for wid in ids:
            attr = XWindowAttributes()
            if not self.x.XGetWindowAttributes(self.dpy, wid, C.byref(attr)):
                continue
            raw_name = C.c_void_p()
            name = ""
            if self.x.XFetchName(self.dpy, wid, C.byref(raw_name)) and raw_name.value:
                name = C.string_at(raw_name.value).decode("utf-8", "replace")
            if raw_name.value:
                self.x.XFree(raw_name)
            hint = XClassHint()
            klass = ("", "")
            if self.x.XGetClassHint(self.dpy, wid, C.byref(hint)):
                klass = (C.string_at(hint.res_name).decode("utf-8", "replace") if hint.res_name else "",
                         C.string_at(hint.res_class).decode("utf-8", "replace") if hint.res_class else "")
                if hint.res_name:
                    self.x.XFree(hint.res_name)
                if hint.res_class:
                    self.x.XFree(hint.res_class)
            found.append({"id": wid, "name": name, "class": klass,
                          "map_state": attr.map_state, "width": attr.width,
                          "height": attr.height})
        self.check()
        return found

    def focus_main_window(self) -> dict:
        windows = self.windows()
        # Never select Qt helper windows by fuzzy matching the word "mGBA".
        candidates = [w for w in windows
                      if MAIN_TITLE.fullmatch(w["name"])
                      and w["class"] == ("mgba-qt", "mGBA")
                      and w["map_state"] == IS_VIEWABLE
                      and w["width"] >= 240 and w["height"] >= 160]
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one visible Qt main window; got {len(candidates)}")
        target = candidates[0]
        # An exact positive match rejects 1x1 mGBA and 3x3 selection-owner helpers.
        if any(w["id"] == target["id"] for w in windows
               if w["map_state"] != IS_VIEWABLE or w["width"] <= 3 or w["height"] <= 3):
            raise RuntimeError("Unmapped or tiny helper selected")
        self.x.XSetInputFocus(self.dpy, target["id"], 2, 0)
        self.check()  # Reject asynchronous BadMatch or BadWindow.
        focused, revert = C.c_ulong(), C.c_int()
        self.x.XGetInputFocus(self.dpy, C.byref(focused), C.byref(revert))
        self.check()
        if focused.value != target["id"]:
            raise RuntimeError("XGetInputFocus does not match verified Qt main-window ID")
        return target

    def key(self, text: str, down: bool) -> None:
        sym = self.x.XStringToKeysym(text.encode())
        code = self.x.XKeysymToKeycode(self.dpy, sym)
        if not code or self.xt.XTestFakeKeyEvent(self.dpy, code, int(down), 0) != 1:
            raise RuntimeError(f"XTest refused {text} ({'down' if down else 'up'})")
        self.check()

    def open_dialog(self) -> None:
        self.key("Control_L", True)
        try:
            self.key("o", True)
            self.key("o", False)
        finally:
            self.key("Control_L", False)
        for _ in range(50):
            dialogs = [w for w in self.windows()
                       if "Select ROM" in w["name"] and w["map_state"] == IS_VIEWABLE
                       and w["width"] > 100 and w["height"] > 100]
            if len(dialogs) == 1:
                print("PASS Ctrl+O opened the empty Select ROM dialog (no file chosen)")
                return
            time.sleep(0.12)
        raise RuntimeError("Ctrl+O did not open exactly one visible Select ROM dialog")

    def close(self) -> None:
        self.x.XCloseDisplay(self.dpy)


def ctypes_or_fail(name: str) -> str:
    path = ctypes.util.find_library(name)
    if not path:
        raise RuntimeError(f"Missing library {name}")
    return path


def checked_run(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=80, **kwargs)


def verify(appimage: Path) -> None:
    if not appimage.is_file() or appimage.name != "mGBA-0.10.5-appimage-x64.appimage":
        raise RuntimeError("Expected existing mGBA 0.10.5 AppImage; never supply a game")
    with appimage.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest != APPIMAGE_SHA256:
        raise RuntimeError("AppImage checksum mismatch")
    for tool in ("Xvfb", "xauth", "xdpyinfo"):
        if not shutil.which(tool):
            raise RuntimeError(f"Missing {tool}")
    with tempfile.TemporaryDirectory(prefix="sg_mgba_qt_focus_nogame_") as directory:
        folder = Path(directory)
        local = folder / "mGBA-0.10.5-appimage-x64.appimage"
        shutil.copy2(appimage, local)
        local.chmod(0o700)
        checked_run([str(local), "--appimage-extract"], cwd=str(folder))
        exe = folder / "squashfs-root/usr/bin/mgba-qt"
        version = checked_run([str(exe), "--version"])
        if "0.10.5" not in (version.stdout + version.stderr) or MGBA_COMMIT not in (version.stdout + version.stderr):
            raise RuntimeError("Extracted executable version mismatch")
        # Pure title tests, before launching the harmless Qt GUI.
        if not (MAIN_TITLE.fullmatch("mGBA - 0.10.5")
                and MAIN_TITLE.fullmatch("mGBA - POKEMON EMER (45.3 fps) - 0.10.5")):
            raise RuntimeError("Expected Qt title patterns rejected")
        for invalid in ("mGBA", "Qt Selection Owner for mGBA", "mGBA - 0.10.4",
                        "mGBA - POKEMON EMER - 0.10.4", "mGBA - (45.3 fps) - 0.10.5"):
            if MAIN_TITLE.fullmatch(invalid):
                raise RuntimeError("Invalid Qt title accepted")
        print("PASS bounded title allowlist and helper/mismatch rejection")
        print("PASS existing AppImage SHA256 and extracted mGBA 0.10.5 version")
        free = [i for i in range(101, 150)
                if not Path(f"/tmp/.X11-unix/X{i}").exists() and not Path(f"/tmp/.X{i}-lock").exists()]
        if not free:
            raise RuntimeError("No isolated display candidate available")
        display = f":{free[0]}"
        authority = folder / "Xauthority"
        authority.touch(mode=0o600)
        checked_run(["xauth", "-f", str(authority), "add", display, ".", secrets.token_hex(16)])
        env = {**os.environ, "DISPLAY": display, "XAUTHORITY": str(authority),
               "HOME": directory, "XDG_CONFIG_HOME": directory,
               "QT_QPA_PLATFORM": "xcb", "SDL_AUDIODRIVER": "dummy",
               "LIBGL_ALWAYS_SOFTWARE": "1", "QT_OPENGL": "software"}
        procs: list[subprocess.Popen] = []
        original_display, original_authority = os.environ.get("DISPLAY"), os.environ.get("XAUTHORITY")
        try:
            procs.append(subprocess.Popen(["Xvfb", display, "-screen", "0", "800x600x24",
                                           "-nolisten", "tcp", "-auth", str(authority)],
                                          env=env, stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL))
            for _ in range(50):
                if subprocess.run(["xdpyinfo", "-display", display], env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                    break
                if procs[0].poll() is not None:
                    raise RuntimeError("Xvfb exited")
                time.sleep(0.1)
            else:
                raise RuntimeError("Xvfb did not become ready")
            # Launch GUI with NO arguments. Isolated config ensures no prior auto-open file.
            procs.append(subprocess.Popen([str(exe)], env=env,
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            # The parent Python Xlib client needs XAUTHORITY, not just its children.
            os.environ["DISPLAY"], os.environ["XAUTHORITY"] = display, str(authority)
            client = XClient(display)
            try:
                for _ in range(80):
                    if procs[1].poll() is not None:
                        raise RuntimeError("Empty Qt GUI exited unexpectedly")
                    try:
                        target = client.focus_main_window()
                        break
                    except RuntimeError as exc:
                        if "Expected one visible Qt main window" not in str(exc):
                            raise
                    time.sleep(0.1)
                else:
                    raise RuntimeError("No correctly mapped main Qt window")
                print(f"PASS exact main title/WM_CLASS, IsViewable, dimensions {target['width']}x{target['height']}")
                print("PASS XSetInputFocus and XGetInputFocus same window ID")
                # Harmless test: change the EMPTY Qt window title to the exact
                # historically observed gameplay/FPS shape. No game is loaded.
                simulated = "mGBA - POKEMON EMER (45.3 fps) - 0.10.5"
                client.x.XStoreName(client.dpy, target["id"], simulated.encode())
                client.check()
                changed = client.focus_main_window()
                if changed["id"] != target["id"] or changed["name"] != simulated:
                    raise RuntimeError("Runtime-title focus failed Qt window identity")
                print("PASS simulated gameplay/FPS title on the same visible Qt window")
                client.open_dialog()
            finally:
                client.close()
        finally:
            for k, original in (("DISPLAY", original_display), ("XAUTHORITY", original_authority)):
                if original is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = original
            for proc in reversed(procs):
                if proc.poll() is None:
                    proc.terminate()
            for proc in reversed(procs):
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)
    print("PASS fail-closed focus test; empty mGBA only, no ROM/save/GDB")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--appimage", type=Path, required=True,
                        help="Existing authenticated mGBA AppImage; no ROM/save path accepted")
    args = parser.parse_args()
    verify(args.appimage)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as e:
        raise SystemExit(f"FAIL CLOSED: {e}") from None
