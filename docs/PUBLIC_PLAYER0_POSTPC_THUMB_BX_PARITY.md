# Public post-copy CPU continuation: Thumb BX instruction/successor parity

## Independent evidence defect in PR81's synthetic fixture
Parent PR81's fake POST_PC halfword is `0x4718` (Thumb-1 `BX r3`).
Its generated fake CPU nevertheless advanced to `POST_PC+2` while `r3`
held the previous copy's byte source, not the branch target. That
contradiction permitted an instruction/PC pair that could NOT represent
the declared Thumb branch execution. PR81's exact head stays unmodified,
pending independent source review.

## Strict separate source-only research
This isolated PR adds a bounded PRE-step Thumb `BX Rm` decoder and
successor-PC check to the optional one-step probe, allowing no inference
from an arbitrary fake PC jump. The supported case requires exact
`0x4700` class with bit-field validation, a known source register
(r0-r14, not PC), an odd Thumb-state target within the GBA ROM window,
and a poststep PC equal to the PRE-step register target with bit0
cleared. All unsupported instructions, target/ARM-state ambiguity, RAM
targets and wrong next PC fail closed. This is narrower than the
original game and intentionally rejects potentially legal cases
outside this observational gate rather than inferring ownership.

The public fake fixture now explicitly sets a generated `r3`
branch target and its step callback actually uses `r3 & ~1`. Both
same-PC and wrong-successor modes must fail AFTER exactly one
fake step. Invalid BX source/target/opcode cases must fail BEFORE any
fake step. Additional negative tests reject malformed BX, BLX,
load and high-register PC source. All synthetic checks still require
no native promotion fields.

## Safety and limits
The new PRE-step source-PC parity on a PUBLIC FAKE CPU is not an
authenticated original modified-ROM instruction, a genuine engine
one-use actor0 request or original move/target legality. It does not
identify two historical PP debit/cancellation causes, result writer PC,
overworld callback return, manual fallback or production acceptance.
No owner Current ROM/save/savestate/private emulator/CPU trace is
staged/read/hashed/executed. Existing PR80/81, approved exact heads,
protected main/source-first and enemy/NPC AI remain byte-unchanged.
No merge. Native 0/20, production 0%, PP causes 0/2.
