# R8-01: Original controller command shape

**Scope:** Standalone, source-only, mock-data gate. Nothing is linked, installed, or executed in the private game. No native move or manual-menu acceptance is earned; production=0%, formal native=0/20.

**Contract:** `patch01_command_shape.evaluate` checks a normalized request/evidence object and returns a **candidate_UNVERIFIED** boolean. The module never emits GBA actions, changes a ROM/save, or claims that caller-provided booleans are authentic.

**Important limitation:** Source-layout hypothesis, not proof of uploaded-ROM ABI. No command is issued.

**Synthetic tests:** 12 independently named negative cases, plus successful non-certifying candidate and malformed top-level type coverage. All inputs are invented fixtures; private traces, ROM, save, screenshots, memory, emulator binaries, and game data must not be uploaded.

**Review:** Independent Claude exact-head source/test/security review required. No inherited approval, no merge/release, and no game installation. Other R8 patches are sibling reviews and have not been combined here.
