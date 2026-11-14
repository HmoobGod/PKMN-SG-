# Original battle callback pointer — candidate CPU word-store provenance

## Existing evidence limitation

Original-game observer source recorded callback1 and callback2 pointer
watcher transitions (32-bit values at gMain and gMain+4) and sometimes
associated them with original CPU program counters. A changed pointer
and an r3/r4 base register alone do not establish that the observed
instruction actually **wrote a full 32-bit word** to that address.
An unrelated LDR, STRB, STRH or instruction with a different effective
address could coincide with a callback transition.

## Fail-closed strict source-only verifier

Building on draft PR78 original outcome candidate STRB evidence, the
offline verifier now separately reports callback word-store candidate
matches and unattributed callback transitions. For each original
callback pointer watcher, only a PRE-step 16-bit Thumb-1 `STR Rt,[Rb,#imm5*4]`
or `STR Rt,[Rb,Rm]` qualifies when the CPU r0..r7 effective byte
address is the exact watched pointer location, aligned to four bytes,
and the full 32-bit `Rt` source register equals the POST-step watcher
value. Overflows, incomplete register snapshots, LDR, byte/halfword
stores and wrong address or pointer value stay unattributed. The
reported writer CPU PCs are deduplicated and sorted; old total
callback transition count and strict watcher chronology are retained.

Public synthetic regressions include a hypothetical STR r2,[r4,#0]
to gMain.callback1, STR r2,[r3,#4] to gMain.callback2, a
register-offset STR variant, nonstores, invalid registers,
unaligned writes, overflow, and mismatched stored pointer values.

**This does not prove a terminal or an overworld return.** A
CPU-consistent callback pointer store is not the semantic callback
decision, and original modified-ROM opcode bytes have NOT been
authenticated on a real game. This draft makes no source-level
controller, ROM, save or gameplay changes, no new native claim,
and no change to the always-false result, terminal or promotion
flags. All tests use synthetic Python rows. No owner Current ROM,
save, savestate, original game or private emulator is accessed.

Native acceptance 0/20 (0%), production Smart Auto 0%, historical
unmatched PP causes classified 0/2.
