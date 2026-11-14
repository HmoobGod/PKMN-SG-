# Original outcome / PP instruction trace v2: per-event Thumb opcode parity

This isolated source-research DRAFT is stacked on PR56 exact
`133b5e1f090c0c08d8a1b99a46fc8627636fe3a2`, which
remains unchanged, unmerged and independently review-pending.
Its original host CPU observer, tester and verifier are PUBLIC source;
no user Current ROM/save, exact modified ROM, savestate or emulator
is staged, loaded or executed in this patch.

## Gap: pinned callback windows did not authenticate arbitrary events

The original `verify_exact_outcome_pp_edges.attest()` verified
immutable private ROM/save hashes and three 64-byte unchanged code
windows: original PP writer and callbacks. However the same
instruction-event trace contains OTHER CPU PCs (including the
optional original battle-outcome RAM candidate writer) that were not
byte-authenticated. Without recording and comparing their original
Thumb opcode, a candidate Main/PP/outcome transition's CPU address
could be spoofed in an otherwise valid-looking trace. The three
existing known windows cannot validate every candidate instruction.

## New intentionally incompatible v2 trace contract

- Real original read-only C observer `SG_OutcomeEdge` stores a
  new 16-bit `opcode` value in its u32 event struct immediately after
  the PC. The value is read at original raw CPU PC-2, **before**
  the original CPU instruction executes and before observing RAM
  mutation. No guest writes or new input paths.
- Offline `verify_exact_outcome_pp_edges.py` now accepts only
  `sg-original-outcome-pp-instruction-edges-v2`, exact per-event
  `opcode` field and original 0x08/0x09 ROM CPU PC. Missing,
  odd, RAM/BIOS or unbounded CPU opcode fails closed. v1 evidence
  is not silently reinterpreted as v2, and the C event layout has
  changed: a future owner-local host would need to adopt v2 explicitly.
- `attest()` keeps verifying immutable original ROM/save hashes
  and all three existing known unchanged original windows. It NOW
  also verifies each event's recorded opcode against the actual
  exact private modified-ROM halfword at its recorded CPU PC.
  Synthetic `audit()` alone is NOT private byte attestation.
- Public Python mutation tests reject missing field, old v1 schema,
  CPU PC=0, RAM/odd PC, oversized opcode and individual opcode
  mutations; a fake 2MB bytearray demonstrates the exact parity
  validator without original game or save bytes.
- Real C fake-core test verifies the event marker and pre-store
  RAM-mutation event both carry the actual fake halfword opcodes
  at their observed PRE-instruction CPUs. Old PR56 regression
  remains intact. Full Source CI compiles/tests both.

## Meaning and strict limits

A successful v2 opcode comparison would establish that recorded
event PCs correspond to halfwords in an authenticated private image;
it would NOT prove the original game executed every instruction
between sparse events, that the owner provided a genuine emulator
trace, or that a guessed outcome byte really is `gBattleOutcome`.
The outcome RAM address and genuine victory/loss/cancellation decision
PC remain UNKNOWN, and the original two historically PP-unmatched
submissions remain unexplained. Real original instruction execution,
one-use engine-owned request lease, dynamic move/target legality,
PP debit versus cancellation, full battle terminal/overworld callback
and manual fallback require separately authorized owner-local
same-run witnessed evidence.

The v2 recorder currently allows RAM Thumb PCs in its base
`sg_original_thumb_pc` helper inherited from PR56, but the v2
offline verifier intentionally **rejects any RAM-origin event** because
the ROM image cannot attest RAM opcodes. A legitimate original
RAM-executing event will therefore fail closed, pending a separately
reviewed RAM provenance protocol; this is not a claim RAM is invalid
execution. That limitation is preferable to inventing code identity.

No change to protected main/source-first, approved heads,
Current ROM/save, player-only behavior, manual fallback,
opponent/NPC-partner AI, auto items/capture or uncertified doubles.
No native hook, guest write, merge or release. Draft/unmerged until
exact-head Source CI and an INDEPENDENT Claude exact-head
source/test/security verdict. Neither PR56 nor ancestors transfer
approval.

Formal native modified-game acceptance **0/20 (0%)**.
Production player0 Smart Auto-Battle **0%**.
Unmatched PP causes resolved **0/2**.

## Isolated PR65 follow-up: one CPU step, one CPU identity

The original C observer can emit an instruction marker before stepping
and multiple changed-memory watcher records after that same step. The v2
Python auditor previously allowed multiple records with the same step and
PC to disagree about the **opcode, CPU registers or frame**, which permits
an internally split/spliced step to masquerade as a corroborated native
PP/terminal observation. It now requires one exact (frame, PC, opcode,
r0..r4) snapshot for all records in a single step, while still allowing
observed RAM/context fields to change due to the step. The fixed top-level
trace envelope also rejects extra client-supplied promotion claims and
boolean stand-ins for the status or guest-write integer fields.

Public-only synthetic tests exercise an actual marker+memory-change
same-step pair, plus opcode/register/frame corruption, injected promotion
metadata, and boolean schema misuse. The approved/other draft SHA heads
are not modified. This is a stricter source-evidence consumer, **not**
proof of an original game instruction, action-ownership lease, PP cause,
original outcome identity, full overworld return or production readiness.
Real modified-ROM native acceptance remains 0/20 (0%), production 0%,
old two PP-unmatched submissions 0/2. No private game assets staged or run.
