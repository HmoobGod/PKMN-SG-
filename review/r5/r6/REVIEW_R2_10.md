# R6-10 R2 — strict source-only privacy preflight

The R1 name/suffix-only gate was **unsafe** and is superseded. R2 rejects disguised double extensions (including `rom.gba.txt` and `x.sav.py`), untrusted JSON, nonworkflow YAML, symlinks, traversal, duplicate/case-colliding names, unsafe file modes, entry count and decompressed size overruns, suspiciously compressed payloads, embedded NUL/binary data, large base64/hex blobs and C hex byte arrays. Mutation-sensitive negatives are registered in a test source file.

**Limit**: This is a conservative static screening heuristic, NOT a security boundary guaranteeing absence of private data. A short text secret, creative encoding, low-volume CPU data, or arbitrary bytes embedded in source comments may still bypass detection. Never upload unless a human/independent reviewer manually checks contents. A review is a separate required gate; no private ROM/save/traces needed or shipped. No original-game acceptance or release implication.
