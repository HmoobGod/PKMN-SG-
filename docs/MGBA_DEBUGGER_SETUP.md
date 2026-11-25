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

- This draft PR contains **public setup documentation and tool-only Python verifiers and regression tests**, no private ROM, save, savestate, patch, executable, binary image, gameplay dump, memory trace, or private absolute filesystem path.
- Tool-only success does **not** authenticate Current's player0 callbacks, reject-vs-new-turn lifecycle, action2/response15 origin, shiny/manual fallback under a new build, or any native acceptance scenario.
- A later live diagnostic requires a **fresh explicit authorization** and separate verified disposable ROM/save copies. No game launches as part of this setup check. Do not merge a gameplay change, patch Current, or run a game based solely on these tool checks.

## Public source checkpoints

- [Issue #151 — historical Current mGBA Auto gameplay](https://github.com/HmoobGod/PKMN-SG-/issues/151#issuecomment-6930984110)
- [Issue #151 — verified X/Z input mapping in real native test](https://github.com/HmoobGod/PKMN-SG-/issues/151#issuecomment-6956903093)
- [Issue #151 — extracted 0.10.5 runtime / GDB tool-only milestone](https://github.com/HmoobGod/PKMN-SG-/issues/151#issuecomment-6976474932)
- [Issue #151 — canonical project checkpoint and safeguards](https://github.com/HmoobGod/PKMN-SG-/issues/151)


## Verified mapped-Qt focus target and Xauthority handoff (2026-11-20, NO GAME)

The earlier `BadMatch` focus failures can occur if a fuzzy "mGBA" title match selects an **unmapped Qt helper window**, rather than the actual Qt main window. Actual empty mGBA 0.10.5 under isolated Xvfb exposed three distinct top-level IDs:

- `"mGBA"` — **1×1, unmapped, no WM_CLASS**: never focus.
- `"Qt Selection Owner for mGBA"` — **3×3, unmapped, no WM_CLASS**: never focus.
- `"mGBA - 0.10.5"` — **480×343, `IsViewable` (map_state=2), WM_CLASS res_name `"mgba-qt"` / res_class `"mGBA"`**: permitted target once *reverified in that exact run*. **IDs are ephemeral**; do not hard-code the observed hexadecimal window IDs.

The directly tested **tool-only** source is [`tools/verify_mgba_qt_focus.py`](../tools/verify_mgba_qt_focus.py). It accepts *only* the existing AppImage path (never ROM/save/game arguments), verifies its SHA-256 and extracted Qt version, then starts an **empty** mGBA Qt window inside a private `Xvfb` session.

```sh
python3 tools/verify_mgba_qt_focus.py --appimage /path/to/existing/mGBA-0.10.5-appimage-x64.appimage
```

Fail-closed focus rules:
1. Pass the same `DISPLAY` and `XAUTHORITY` credentials to **Xvfb, the Qt process, and the parent Python Xlib focus client**. Setting credentials for the child process *alone* causes `XOpenDisplay` to fail from the parent.
2. Enumerate root top-level windows with `XQueryTree`, read `XFetchName`, `XGetClassHint` (WM_CLASS) and `XGetWindowAttributes`.
3. Require **exactly one** window with name `mGBA - 0.10.5`, WM_CLASS `("mgba-qt", "mGBA")`, `map_state == IsViewable (2)` and dimensions at least **240×160**. Reject tiny/unmapped Qt helper windows and ambiguity before sending any input.
4. Call `XSetInputFocus`, `XSync` and immediately verify `XGetInputFocus` equals the selected window's ID. Trap and reject asynchronous X11 errors (`BadMatch`, `BadWindow`).
5. Deliver **only harmless** XTest `Ctrl+O` and verify one visible **Select ROM** dialog. **Do not select a file**. Shut down the Qt process, Xvfb and temporary workspace.

On this host, the exact new verifier passed **3/3** fresh empty-mGBA/Xvfb cycles, including a run with intentionally incorrect *parent* DISPLAY/XAUTHORITY values (which were overridden by isolated values). The script rejected an extra `--rom` argument at CLI parsing and a tampered AppImage before execution. The GitHub file blob matches the locally tested source. This is **Qt focus and harmless input readiness only**, not a game Start/Confirm, GDB, or native Auto Battle witness. The earlier X11 7/7 test remains separate.

Do not reuse old window IDs or rely on `wmctrl`. Any new ROM/game execution requires separately bounded owner authorization. This source-only PR stays **draft and unmerged**, with **R5 NATIVE HOLD / formal 0/20**.


### Runtime game/FPS title correction (2026-11-20, harmless validation)

The previous *empty-window-only* exact-title gate (`mGBA - 0.10.5`) caused an authorized native session to stop before Start: the recorded running-game title followed the pattern `mGBA - [redacted title] (45.3 fps) - 0.10.5`. The safer replacement is a **bounded, fully anchored versioned mGBA title pattern** admitting the empty title or a game-title/FPS segment, **not** substring matching. It retains exact WM_CLASS `("mgba-qt", "mGBA")`, `IsViewable`, minimum 240×160 dimensions, exactly one candidate, Xauthority, synchronous X11 error handling, and exact `XGetInputFocus` identity.

The updated ROM-free verifier also changes the title of its own *empty* Qt window to the historically observed gameplay/FPS shape using X11 `XStoreName`, reselects the same window, and checks harmless `Ctrl+O` opens the Select ROM dialog without choosing a file. A separate temporary empty-mGBA/Xvfb test passed the empty and changed titles, focus identity, Ctrl+O and multiple negative-title cases. **The changed title was simulated; it is not gameplay proof.** The old unmapped 1×1/3×3 helper windows remain rejected. Do not copy previously observed window IDs between sessions.

The resulting updated source is `tools/verify_mgba_qt_focus.py` on this draft PR. No game file was opened during title-fix validation. A real game still requires fresh owner authority and the exact bounded native test rules; R5 NATIVE HOLD and formal 0/20 remain.


## No-game GDB readiness: verified real RSP, not merely an open TCP port (2026-11-20)

A **real mGBA 0.10.5** run under fresh, isolated Xvfb and a Linux user+network namespace with **only enabled loopback** accepted the pinned public 32 KiB generated Thumb fixture from [PR #45](https://github.com/HmoobGod/PKMN-SG-/blob/f19db0d2c652a316a5ef4962fd1b0d6b87e6ef55/tools/pr26_generated_real_mgba_runner.py). The synthetic cartridge SHA-256 is `cfa20bc9ccad2131abeedaed0d1d5aa49425f8bce5616370d0b6659c7cd4804b`, with generated ARM `00009fe5` at `0x080000C0` and Thumb `fee7` at `0x08000100`. It is not SoulGold or any owner's game file; it is generated in temporary storage and deleted.

### Grounded cause of a misleading socket-ready state

An **invalid, newly invented** 32 KiB synthetic file produced mGBA's GUI error `Could not load game. Are you sure it's in the correct format?`. Meanwhile TCP 2345 still accepted a connection; an attempted RSP `?` received no ACK before timeout. Therefore **port acceptance alone is not readiness**. On the authenticated PR45 synthetic fixture, mGBA did process genuine read-only RSP with valid ACK, framing, checksums, `? → S02`, `g → 136 hex characters`, `m080000c0,4 → 00009fe5`, and `m08000100,2 → fee7`. One successful test had **3 initial ConnectionRefusedError retries before the 4th TCP attempt succeeded**. The independently verified host preflight and exact generated fixture were run again with PASS. This does **not** prove that the previous real-game ConnectionAbortedError was caused by the same startup race.

### Mandatory fail-closed readiness gate

1. Verify the existing Drive AppImage's exact size (25,208,000) and SHA-256 (`fdf0a5c1588e1606c38315735cf48a9f9dca3573f32a3947ebc956f8297e85cd`). Extract Qt program resources only and assert reported mGBA version `0.10.5 (26b7884bc25a5933960f3cdcd98bac1ae14d42e2)`.
2. Start an isolated Xvfb with matching `DISPLAY/XAUTHORITY`; create a **new** user+network namespace and explicitly set `lo` UP. Fail closed unless `ip link` shows **exactly one enabled loopback interface**, and no default external route. mGBA's listener may bind `0.0.0.0` *inside* this loopback-only namespace; never expose port 2345 to other networks.
3. Generate only the **SHA-pinned PR45 synthetic fixture** in a private temporary directory. Launch extracted `mgba-qt -g` on that fixture using isolated `HOME`, `QT_QPA_PLATFORM=xcb`, `SDL_AUDIODRIVER=dummy`, `LIBGL_ALWAYS_SOFTWARE=1` and `QT_OPENGL=software`. Do not supply private ROM/save paths or external runtime arguments.
4. Check the child process remains alive. Before a TCP connection is established, retry **only** `ConnectionRefusedError`, `ConnectionAbortedError`, and connect timeout with 150 ms backoff, up to a strict **12-second** monotonic deadline and 100-attempt cap. Unrecognized socket errors or early emulator exit are immediate failures. Distinguish pre-connect aborts from failures after any RSP request.
5. Once TCP connects, **never reconnect or replay** after sending a command. Require actual RSP `+` acknowledgment, properly delimited `$...#checksum` response with checked checksum, and a per-operation read timeout. **First send the exact `qSupported:swbreak+;hwbreak+` feature offer and require exactly one `swbreak+` and one `hwbreak+` token in the reply, without contradictory or duplicate tokens.** Only then require exact `?=S02`, a `g` payload of **136 hexadecimal characters**, and matching reads at the two *generated-only* addresses. `S02` alone does not prove actual CPU halt, and `g` alone does not prove a particular ROM identity.
6. Any modal load error, wrong synthetic digest, malformed ACK/frame/checksum, EOF, reset/abort **after connect**, RSP timeout, unexpected memory bytes, network ambiguity or child exit means **NOT READY: terminate the session**, do not issue `c`, `s`, `G`, `M`, `P`, `Z`/`z`, load another ROM, or silently retry.
7. Stop emulator and Xvfb, remove the synthetic fixture, config and temporary directories; record **tool-only** pass/fail and the already-verified public SHA/check outcomes, never game data.

The reusable **source-only** implementation and 13 deterministic negative/positive Python tests were generated in the owner chat as `verify_mgba_gdb_readiness.py` and `test_verify_mgba_gdb_readiness.py`. Local test evidence: **13/13** tests pass, plus real authenticated mGBA 0.10.5 generated-fixture handshake passes. No SoulGold ROM, save, game memory or gameplay session was accessed. Original source-first and approved gameplay code remain unchanged. **R5 NATIVE HOLD, formal 0/20; new explicit authorization is required before any Current-native session.**


## RSP stop-reason feature negotiation hardened (2026-11-20; PUBLIC SYNTHETIC ONLY)

The authenticated mGBA 0.10.5 source `src/debugger/gdb-stub.c` (`_processQSupportedCommand`, `_gdbStubEntered`) resets its two *client capability flags* on each new `qSupported` request. A breakpoint stop is reported as `T05hwbreak:;` only when **both** `swbreak+` and `hwbreak+` were offered by this client and debugger breakpoint metadata is present. Otherwise mGBA can deliberately produce `S05k`. `S05k` is a genuine stop packet format, **not itself a proven instruction address or completed copier transaction**. Source: https://github.com/mgba-emu/mgba/blob/0.10.5/src/debugger/gdb-stub.c

The isolated source-only experiment using the exact public PR #45 generated Thumb fixture previously reproduced `S05k` before both capabilities were offered and `T05hwbreak:;` afterward, both with the independently read synthetic PC `0x08000100`. The old Current session's negotiation state was not preserved, so its specific cause remains unproven.

The revised `tools/verify_mgba_gdb_readiness.py` now sends **exactly** `qSupported:swbreak+;hwbreak+` first on the same GDB socket as its subsequent `?`, `g` and synthetic `m` reads, and requires an ACK, good frame/checksum, and one each of `swbreak+`/`hwbreak+` in the server reply. Missing/duplicated/contradictory capability tokens fail closed. No arbitrary `qSupported` variants, guest writes, `c`, `s`, `Z` or `z` commands are allowlisted by this *readiness* verifier. The negotiation changes **RSP protocol state only**, not guest memory or registers.

The new **pure** helper `require_exact_z1_stop(stop, registers, expected_pc)` is a strict classifier for a separately authorized future diagnostic. It returns evidence only for exact `T05hwbreak:;` **plus** an independently read 136-hex-character register payload whose little-endian r15 equals the expected aligned GBA ROM instruction address. `S05k`, `S05`, `T05swbreak:;`, watchpoint stops, unexpected fields, missing registers and wrong PC are **INCONCLUSIVE / fail closed**, not proof of a player controller event. This helper installs no breakpoint and does not perform any RSP I/O. It cannot recover omitted stop metadata retrospectively.

Validation completed on the updated locally tested source: **23/23 deterministic tests PASS**, Python syntax checks PASS, and one bounded authenticated mGBA 0.10.5 *public generated fixture* run PASS, including actual `qSupported` + `?` + `g` + mapped synthetic ARM/Thumb readback with loopback-only networking and cleanup. No new `Z1` was installed in that final readiness run; the preceding exact-PC synthetic Z1 test is separate evidence, not a new game witness.

**Nontransferable boundary:** Each future debugger connection must negotiate its *own* capabilities before installing any separately authorized `Z1`; a second `qSupported` can reset them. Exact `T05hwbreak:;` and PC are necessary but insufficient for complete Current actor0 request→reply→execution provenance, controller write completeness or final Auto acceptance. No SoulGold ROM/save was read, hashed, copied, debugged or executed in this source-only change. Draft/unmerged; R5 NATIVE HOLD and formal acceptance **0/20**.
