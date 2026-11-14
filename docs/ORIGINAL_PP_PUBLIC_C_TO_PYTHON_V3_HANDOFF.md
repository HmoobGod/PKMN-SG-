# Public original outcome/PP v3 C-to-Python evidence handoff

This is **source-only fake-CPU validation**, not authentic owner-game
attestation. The original PP/outcome observer is the actual C from
approved ancestor PR72 plus the pre-step halfword snapshot improvement
in review-pending parent PR74. The new C public fixture includes that
actual observer, executes it against a memory-only FAKE CPU core with
mutated instruction halfwords and r5–r7 after each guest step, and
prints all 23 typed C fields (the v3 event ABI) as an isolated JSON
record. It emits only fake CPU event data, not a ROM or save.

The new Python test compiles the C fixture with runtime asserts
enabled, runs it without any original game, accepts ONLY the expected
`status/steps/events` envelope, and feeds those actual C-produced
event rows into the strict existing Python v3 original PP/outcome
auditor. Independently frozen **fake 2 MiB instruction bytes** are
used for event opcode-parity testing and negative mutations.
The exact identity literals are taken from the source verifier
constants only to exercise schema parsing; they do not verify any
private original/modified ROM or save and cannot be interpreted as
provenance from an owner's protected files.

The integration suite enforces marker/PP change/Main-clear chronology,
pre-step opcode/register parity, C/Python 23-field schema match,
no unauthorized privilege/evidence fields, same-step invariant
failure when any register/PC/opcode is forged, denied instruction
byte mismatches, and perpetual source-only acceptance booleans FALSE.
It explicitly classifies the fake emitter-step PP change as
uncertified, because it is NOT at the original PP writer PC and
therefore is not a witnessed native debit. It cannot classify the
two historic PP-missing cases, a real battle terminal, a one-use
engine request, or an actual original game outcome PC.

Important limits: This **does not close PR63 B2** private exact-ROM
attestation/host collector wiring, nor certify native gameplay.
The offline `attest` path intentionally still requires separately
authorized private original/current/modified ROM and save inputs,
which are never staged, opened, hashed, or executed in this PR.
All generated compilation files exist only inside a disposable
public CI temporary directory. No private game, enemy/NPC AI,
manual fallback, items/capture, ROM/save or protected branches change.

Formal original modified-game native acceptance 0/20 = 0%,
production Smart Auto 0%, historic unmatched PP causes resolved 0/2.
