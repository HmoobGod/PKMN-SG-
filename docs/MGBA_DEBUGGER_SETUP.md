# Pokémon SoulGold — known-good mGBA 0.10.5 tool environment

**Status (2026-11-20): TOOL-ONLY VERIFIED.** This document is a reproducible host-environment check, **not** authorization to start Pokémon SoulGold or an endorsement of a new gameplay patch. The first permitted Current-native diagnostic still requires a new, explicitly bounded authorization. R5 remains **NATIVE HOLD**; formal general native acceptance remains **0/20**.

## Recover existing AppImage first

1. In the connected Google Drive, check the existing [`mGba` folder](https://drive.google.com/drive/folders/1nGhdid4412IR0sauJHcCqxgmPuB6CN9B) before requesting another upload or downloading anything externally.
2. The recovered file is [`mGBA-0.10.5-appimage-x64.appimage`](https://drive.google.com/file/d/11bqOyPlwEEZwkNkoFepmSq3oXtPKAZYW/view), **25,208,000 bytes**. SHA-256 of this Drive-sourced artifact as checked locally: `fdf0a5c1588e1606c38315735cf48a9f9dca3573f32a3947ebc956f8297e85cd`.
3. The extracted `usr/bin/mgba-qt --version` returns `0.10.5 (26b7884bc25a5933960f3cdcd98bac1ae14d42e2)`. Its `--help` advertises `-g, --gdb` (default TCP port **2345**) and `-d, --debug`. These checks confirm the binary's self-reported version and advertised option, not an independent official-signature attestation or a live GDB/game session.
4. The source archive's separate `tools/mgba/mgba-rom-test` is **not** this Qt/GDB AppImage; do not silently substitute it.

## Repeatable *no-game* verification (tested 2026-11-20)

Prerequisites on the Linux x86_64 host: Python 3, `Xvfb`, `xauth`, `xdpyinfo`, `xev`, `stdbuf`, and `libX11`/`libXtst`. Run from a checkout of this PR; the script does not accept ROM/save arguments:

```sh
python3 tools/verify_mgba_host_tooling.py \
  --appimage /path/to/existing/mGBA-0.10.5-appimage-x64.appimage \
  --probe-input
```

The script fails closed on a wrong AppImage digest, extracts **program resources only** to a private temporary directory, executes only extracted `mgba-qt --version` / `--help`, starts a separate Xvfb display with local-only X11 transport and temporary Xauthority, and opens the **harmless `xev` window**, *not mGBA*. It focuses that test window via Xlib (`XSetInputFocus`) and uses XTest keypress/release events. Required X11 receipt: `Return`, `x`, `z`, `Left`, `Right`, `Up`, `Down` (7/7). All temporary processes and files are stopped/removed. The script does not start mGBA with a game, connect GDB, read any game file, create a ROM/save copy, alter project files, or write GitHub.

Observed on this host: exact SHA-256 PASS; mGBA version/commit PASS; advertised `-g` port2345 PASS; isolated Xvfb focus and all seven X11 key events PASS; unknown argument `--rom example.gba` is rejected at argument parsing. The Qt mGBA **GUI keyboard reception has not been retested** here—`xev` success is a **host input transport check**, not native game proof.

## Known-good historical gameplay environment (not re-executed here)

- `Xvfb` with a separately targeted `DISPLAY`, `QT_QPA_PLATFORM=xcb`, and `SDL_AUDIODRIVER=dummy` supported mGBA 0.10.5 Linux Qt historically.
- Historical mGBA keyboard mapping: **X → GBA A/Confirm**, **Z → GBA B/Cancel**, **Enter/Return → Start**; arrows move the cursor. A past attempt using Z at the Continue menu returned to title because it was **B**, not A.
- Qt window focus is independent from debugger `?` stop replies or `c` continues; neither GDB `S02` nor `c` alone proves advancing visible GBA frames. Confirm progress before any debugging when later expressly authorized.
- `pauseOnFocusLost` is a separate possible Qt setting that must be verified in the *isolated* configuration when real GUI testing is authorized; do **not** assume its value or mutate protected settings.
- In this 2026-11-20 harmless Xvfb probe, host `wmctrl -l` exited with `-11` (segmentation fault). **Do not depend on `wmctrl` to establish focus here.** The `xev` outer-window ID and direct X11 focus verification worked both with and without a window manager. This does **not** certify focusing the actual mGBA Qt game window.
- For later authorized gameplay: isolate `HOME`, Xauthority, `DISPLAY`, save paths and configuration. Explicitly disable `.bps`/`.ups`/`.ips` autoload before opening copies. Bind GDB to an isolated local interface where supported, never expose guest debugging publicly; stop if the actual listener cannot be constrained.

## Scope and safety boundary

- This PR contains **only this Markdown file and a host-only Python verifier**, no private ROM, save, savestate, patch, executable, binary image, gameplay dump, memory trace, or private absolute filesystem path.
- Tool-only success does **not** authenticate Current's player0 callbacks, reject-vs-new-turn lifecycle, action2/response15 origin, shiny/manual fallback under a new build, or any native acceptance scenario.
- A later live diagnostic requires a **fresh explicit authorization** and separate verified disposable ROM/save copies. No game launches as part of this setup check. Do not merge a gameplay change, patch Current, or run a game based solely on these tool checks.

## Public source checkpoints

- [Issue #151 — historical Current mGBA Auto gameplay](https://github.com/HmoobGod/PKMN-SG-/issues/151#issuecomment-6930984110)
- [Issue #151 — verified X/Z input mapping in real native test](https://github.com/HmoobGod/PKMN-SG-/issues/151#issuecomment-6956903093)
- [Issue #151 — extracted 0.10.5 runtime / GDB tool-only milestone](https://github.com/HmoobGod/PKMN-SG-/issues/151#issuecomment-6976474932)
- [Issue #151 — canonical project checkpoint and safeguards](https://github.com/HmoobGod/PKMN-SG-/issues/151)
