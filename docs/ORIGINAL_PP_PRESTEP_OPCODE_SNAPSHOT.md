# Original outcome/PP read-only C observer — PRE-step opcode freeze

This isolated public source-only research draft descends from independently
source-approved PR72 (exact `5ed836f6f4b3ac594e55e9f53c9f86b6cf36567d`).
It addresses a concrete original CPU provenance defect identified by
independent Claude in PR63 (B1): the original observer used to call
`read8(core, pc-2)` from inside `sg_edge_append` even for PP/outcome
watchers emitted AFTER `step(core)`. Any instruction-space mutation or
unstable read during the step could make the recorded halfword differ
from the instruction that actually preceded the watched memory change.

The C observer now captures `pre_opcode` once per guest CPU step, after
validating raw Thumb PC and before emitting markers or stepping. It passes
this immutable snapshot into the marker and all post-step watcher
append calls, retaining the existing 23-word C event ABI and strict
Python v3 field names and no guest writes. The C append no longer reads
instruction bytes. ROM-origin Thumb halfwords are recorded from
`pc-2`/ `pc-1`; RAM-origin instructions are explicitly left at
0/UNATTESTED, not guessed. No extra rights are conferred by a zero value.

The modified public fake CPU opcode fixture now **mutates its fake ROM
halfwords and r5-r7 after each step**, then checks that the post-step PP
edge has the pre-step 0x1234 value (not the mutated 0x5AA5 value), the
post-step Main/terminal-candidate edge has the pre-step 0x700E value
(not the mutated 0xD2C3 value), and each step's pre-step r5-r7 snapshot
is not laundered by that CPU step. This is a disposable FAKE memory test,
not evidence of actual commercial ROM self-modification.

No protected original/modified ROM, owner's save/savestate, emulator,
original CPU traces, or private data are accessed or run. Source CI
tests the C read-only observer on public fake CPU only. PR63 B2
owner-original instruction attestation/host wiring remains unresolved.
No real engine-issued one-use player0 request, original move/target
legality, historical PP debit/cancellation, genuine game outcome PC,
overworld return, manual fallback or production Smart Auto is certified.
Formal original-game native 0/20 (0%), production 0%, historical
unmatched PP cause classifications 0/2.
