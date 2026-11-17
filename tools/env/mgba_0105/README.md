# SoulGold — mGBA 0.10.5 Linux bootstrap (source only)

This branch provides a repeatable **Linux x86_64** mGBA runtime setup without checking a binary, private ROM, save, savestate, game-derived patch, or test data into GitHub.

**Pinned emulator:** [mGBA 0.10.5 official release](https://github.com/mgba-emu/mgba/releases/tag/0.10.5), asset `mGBA-0.10.5-appimage-x64.appimage` ([direct release URL](https://github.com/mgba-emu/mgba/releases/download/0.10.5/mGBA-0.10.5-appimage-x64.appimage)).

**Expected size:** 25,208,000 bytes. **Pinned SHA256:** `fdf0a5c1588e1606c38315735cf48a9f9dca3573f32a3947ebc956f8297e85cd`, recomputed from the owner's existing Google Drive copy of the original release asset on 2026-11-17; official release asset metadata should be independently matched when a public download is available. The installer never silently accepts a different binary.

## Install

From a clone of this *isolated* branch (not merged to `main`):

```bash
# On a host that can reach the public official GitHub release:
bash tools/env/mgba_0105/setup_mgba_0105_linux.sh

# Offline alternative (e.g. the owner's existing PRIVATE Drive backup,
# downloaded locally outside the repository):
bash tools/env/mgba_0105/setup_mgba_0105_linux.sh \
  --source '/private/path/mGBA-0.10.5-appimage-x64.appimage'

# Optional explicitly private cache outside the Git worktree:
bash tools/env/mgba_0105/setup_mgba_0105_linux.sh \
  --source '/private/path/mGBA-0.10.5-appimage-x64.appimage' \
  --dest "$HOME/.cache/pokemon-soulgold/mgba/0.10.5"
```

The installer checks the exact hash and size **before extraction or execution**, then verifies that the extracted executable reports `mgba-qt 0.10.5`. Its default cache is `${XDG_CACHE_HOME:-$HOME/.cache}/pokemon-soulgold/mgba/0.10.5`. It fails closed if an existing installation does not match, and it refuses an installation directory in a Git worktree.

## Test bootstrap without any game

```bash
bash tools/env/mgba_0105/test_setup_mgba_0105_linux.sh \
  '/private/path/mGBA-0.10.5-appimage-x64.appimage'
```

The offline test installs into a temporary directory, tests idempotence, rejects corruption and missing inputs, and cleans up. **It never opens any ROM or save.** Linux only; `curl`, `sha256sum`, `realpath`, `mktemp`, and the standard core utilities are needed. No FUSE mount is required (`--appimage-extract`).

## ROM testing: separate, private, explicit

A verified emulator executable **does not certify R4 gameplay**. For owner-authorized native tests, use disposable copies of the ROM and SAV in a private folder outside GitHub/Drive or GitHub Actions. Verify originals remain unchanged. Do not upload game bytes, private savestates, screenshots, or traces to GitHub/Drive. R4 gameplay source remains SHA256 `ce8d38b718939243a99eed560d250ed30e15b29255a0b4f0c21f3cd3ced12333`, compiled 252-byte Thumb payload SHA256 `d588d77c7096afcf9130b445d184ef06842f7599da92649c65ae73d637abc584`.

Current **formal independent native acceptance: 0/20**. No automatic promotion, merge or release.
