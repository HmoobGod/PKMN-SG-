# Original Thumb STRB r0–r7 full effective-address proof

Independent Claude source-approved PR72 already captures original PRE-step CPU
registers r0 through r7 in its read-only 23-word outcome/PP C event ABI,
and requires that the STRB Rt source low byte equals the observed
POST-step player-owned PP byte. However its Python address verifier still
supports only base/offset registers r0–r4: when a legitimate Thumb-1
STRB encoded Rb or Rm r5–r7 it returned UNKNOWN even with those exact
values present in the already captured snapshot. This was a nonblocking
reviewer advisory; the refusal was safe, but could miss genuine evidence.

This separate source-only branch extends **only** the offline Python
Thumb STRB 16-bit immediate/register-offset effective-address interpreter
to all eight low registers. The existing source byte check already uses
all eight, and the trace audit now supplies one identical r0–r7 snapshot
to both target-address and Rt-byte decoders. No new CPU or pointer state
is inferred. Unsupported instructions, unrecorded/malformed CPU registers,
32-bit address overflows, wrong PP watch addresses and non-byte stores
still fail closed.

New synthetic regression cases prove STRB r6,[r7,#0], STRB
r6,[r5,r7], high-register overflows, inconsistent source byte and
watcher address, and an original PP value changing 21→19 (a -2,
**not** one native PP debit). They keep the original native one-use
ownership, execution-versus-cancellation, terminal/outcome and promotion
booleans false. The address-derived evidence still counts only a
**candidate** byte-store, never proof of its originating action.

This branch is independent of the sibling new public C observer
pre-step opcode snapshot branch PR74. Both are SOURCE ONLY: no
owner Current ROM/save/savestate, emulator, private original CPU
trace, gameplay release or integration. PR63 opcode timing/attestation
wiring remains blocked separately until independently reviewed and
verified. Formal native original modified-game acceptance 0/20 = 0%,
production 0%, two unmatched historical PP cause classifications 0/2.
