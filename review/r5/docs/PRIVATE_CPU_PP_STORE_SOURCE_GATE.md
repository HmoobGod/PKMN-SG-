# Private mGBA CPU PP-write audit — source-only gate

This audit is public **source code** designed for read-only *private* use against
the owner's exact, hash-attested ROM and the private test adapter's store logs.
No ROM, save, screenshots, RAM snapshots, private traces or identifying hashes
are to be committed to GitHub or Google Drive.

The emulator's CPU r15 is the executing Thumb PC plus 4 at a Store8 callback;
its `op` value is separately prefetched and **must not** be treated as the
executing opcode. The verifier rereads the precise 16-bit instruction in the
exact private ROM from `raw_pc - 4` and admits only a single-byte Thumb STRB
immediate whose pre-step r0-r7 snapshot proves **both** its destination and
stored byte, with exact observed 1-PP decrement in original EWRAM. A direct
store can show PP consumed, but cannot by itself attribute engine request
ownership, move/target legality, cancellation cause, manual fallback, enemy
isolation, or a completed battle. Formal native acceptance stays 0/20.

Example private invocation, executed ONLY in a private directory:

```
python3 tools/audit_private_cpu_pp_store.py \
  --private-rom /PRIVATE/TEST_COPY.gba \
  --private-trace /PRIVATE/pp_engine_trace.jsonl \
  --expected-rom-sha256 YOUR_PRIVATE_EXPECTED_ROM_HASH \
  --battle-ui-frame 1234
```

Only synthetic generated fixtures are run in public CI:

```
python3 tools/test_private_cpu_pp_store_audit.py
```

Source-review limitations: this assumes the observed pinned emulator ABI and
Thumb pipeline behavior, which require independent review before extending to
other emulator builds. A PP drop with a changed full word/copy or a side-effect
outside the direct byte store is intentionally not promoted. This tool does
not trace the complete original actor0 emitter/reply/validator chain.
