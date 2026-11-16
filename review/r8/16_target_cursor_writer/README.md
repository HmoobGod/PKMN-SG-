# R8-16: Original target cursor CPU store provenance

**Scope:** Standalone, source-only, mock-data gate. Nothing is linked, installed, or executed in the private game. No native move or manual-menu acceptance is earned; production=0%, formal native=0/20.

**Contract:** `patch16_target_cursor_writer.evaluate` checks a normalized request/evidence object and returns a **candidate_UNVERIFIED** boolean. The module never emits GBA actions, changes a ROM/save, or claims that caller-provided booleans are authentic.

**Important limitation:** Source-only evidence model; target-instruction semantics must be confirmed in private native replay.

**Synthetic tests:** 11 independently named negative cases, plus successful non-certifying candidate and malformed top-level type coverage. All inputs are invented fixtures; private traces, ROM, save, screenshots, memory, emulator binaries, and game data must not be uploaded.

**Review:** Independent Claude exact-head source/test/security review required. No inherited approval, no merge/release, and no game installation. Other R8 patches are sibling reviews and have not been combined here.
