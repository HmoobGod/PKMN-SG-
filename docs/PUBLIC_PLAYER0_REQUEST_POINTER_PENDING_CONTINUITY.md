# Original player0 44-byte request copy: prevent transient context laundering

This is an isolated SOURCE-ONLY C recorder and fake-CPU test draft
stacked on PR77 final unchanged exact
`d03ef914d267cdfbf3c2756fef7ba3d475a41f18`.
PR77 checks whether each watched destination change is explained by
a 16-bit Thumb STRB source operand and effective destination;
this follow-up checks **request-context continuity** across the same
45 observed guest instructions.

## Previously unverified original request state

The recorder sampled the original EWRAM request-copy destination buffer
pointer at ENTRY_PC and the pending word at ENTRY/POST, but previously
did not fail closed if the pointer or pending word changed *during* the
44 copied bytes and was restored before POST. That could launder a
mid-request replacement of the engine's request buffer or a pending
ownership transition into a plausible looking completed fake copy.

## Public read-only fail-closed guard

Every pre-step and immediate post-step of the staged candidate checks
the exact request buffer pointer at `0x02001C6C` still equals
`dest-0x10`, and the pending word at `0x02001D2C` equals the
captured entry value. Any mutation returns a bounded observational
error 15 and never counts a successful candidate. The source observer
does not write or repair RAM, repeat an action, invent engine ownership,
modify the original game or suppress manual fallback.

The PUBLIC synthetic fake CPU now changes its request pointer after
store index 7 then restores it at index 8, changes its pending word
likewise, and separately changes pending immediately after ENTRY.
All three must be denied at the earliest post-instruction check.
The strict existing v4 Python gate now also compares the recorded
pending ENTRY and POST values, reports only a SOURCE-ONLY
continuity-check flag, rejects forged pending-post data and extends
the C→Python fake modes. Existing source-byte, destination-prefix,
all-source, Thumb STRB, overflow, opcode and one-use candidate
limitations from PR77 remain intact.

## Limits

Real engine-pending state could legitimately change in some original
request flows. This intentionally conservative *candidate recorder*
would then reject those flows as UNPROVEN; it never labels them
cancellations or gameplay failures. Matching every pointer/pending
read does NOT authenticate an original-ROM instruction, prove a
unique engine-issued one-use request epoch, or certify a real move,
target, PP debit, battle result or overworld return. All results
remain lab/synthetic, with no private game files or emulator used.

Formal original-game native acceptance: 0/20 = 0%.
Production Smart Auto-Battle: 0%.
Historical two PP-unmatched causes classified: 0/2.
