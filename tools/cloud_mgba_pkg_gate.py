#!/usr/bin/env python3
"""Public-only exact package identity gate. No ROMs, networks, or private inputs."""
from __future__ import annotations
import subprocess
import sys

# Locked to the Ubuntu 26.04 repository build observed in PR35.
EXPECTED_MGBA_SDL_VERSION = "0.10.5+dfsg-3build1"


def require_version(version: str) -> str:
    if type(version) is not str or version != EXPECTED_MGBA_SDL_VERSION:
        raise RuntimeError("mGBA Ubuntu package exact version mismatch")
    return version


def verify_package_version() -> str:
    value = subprocess.check_output(
        ["dpkg-query", "-W", "-f=${Version}", "mgba-sdl"],
        text=True,
        timeout=6,
    ).strip()
    return require_version(value)


def main() -> None:
    if len(sys.argv) != 1:
        raise RuntimeError("version gate does not accept external file arguments")
    print("EXACT_MGBA_SDL_PACKAGE_VERSION: " + verify_package_version())


if __name__ == "__main__":
    main()
