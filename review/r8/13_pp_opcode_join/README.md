# R8-13: Original CPU PP store and move-request correlation

**Scope:** Standalone, source-only, mock-data gate. Nothing is linked, installed, or executed in the private game. No native move or manual-menu acceptance is earned; production=0%, formal native=0/20.

**Contract:** `patch13_pp_opcode_join.evaluate` checks a normalized request/evidence object and returns a **candidate_UNVERIFIED** boolean. The module never emits GBA actions, changes a ROM/save, or claims that caller-provided booleans are authentic.

**Important limitation:** Provenance labels are caller-supplied and must be validated with original mGBA CPU evidence; not native acceptance.

**Synthetic tests:** 9 independently named negative cases, plus successful non-certifying candidate and malformed top-level type coverage. All inputs are invented fixtures; private traces, ROM, save, screenshots, memory, emulator binaries, and game data must not be uploaded.

**Review:** Independent Claude exact-head source/test/security review required. No inherited approval, no merge/release, and no game installation. Other R8 patches are sibling reviews and have not been combined here.
