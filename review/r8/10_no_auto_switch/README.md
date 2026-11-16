# R8-10: Original-command action exclusion

**Scope:** Standalone, source-only, mock-data gate. Nothing is linked, installed, or executed in the private game. No native move or manual-menu acceptance is earned; production=0%, formal native=0/20.

**Contract:** `patch10_no_auto_switch.evaluate` checks a normalized request/evidence object and returns a **candidate_UNVERIFIED** boolean. The module never emits GBA actions, changes a ROM/save, or claims that caller-provided booleans are authentic.

**Important limitation:** No guest action is emitted. Original ROM forced-switch branch remains a native blocker.

**Synthetic tests:** 13 independently named negative cases, plus successful non-certifying candidate and malformed top-level type coverage. All inputs are invented fixtures; private traces, ROM, save, screenshots, memory, emulator binaries, and game data must not be uploaded.

**Review:** Independent Claude exact-head source/test/security review required. No inherited approval, no merge/release, and no game installation. Other R8 patches are sibling reviews and have not been combined here.
