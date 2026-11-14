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


## Isolated PR66: watcher after-value binding and chronology (public synthetic)

The original C observer steps its guest CPU first, then records each
changed RAM watcher together with the poststep live core snapshot. The prior
v2 Python verifier checked addresses/before-after values, but could accept
a changed Main.inBattle, callback1/2, flags or pending watcher whose
poststep field contradicted its own recorded after-value. This patch
fails closed on such contradictions. It also requires subsequent edges
of the **same watcher** to begin at its last observed after-value,
with PP slots tracked separately; all poststep watcher rows attributed
to the *same* CPU instruction must share the final poststep context.
PRE-step instruction markers retain their own prestate and are never
incorrectly forced to equal the poststate.

Public negative tests cover forged Main/Callback/Flags/Pending snapshots,
missing intermediate watcher history, and multiple poststep records with
contradictory contexts. Legitimate simulated multi-watcher same-step
mutations and per-watcher continuity are permitted. This does not
certify a ROM instruction or a truthful original emulator transcript:
only authenticated owner-local, separately authorized replay could do
that. No private ROM/save/emulator is accessed by this source patch.

This is an isolated research child of PR65 (itself pending independent
Claude exact-head review); PR65, PR63, protected main/source-first,
approved original heads and Current ROM/save remain unmodified.
Native modified-game acceptance 0/20 (0%), production 0%; historical
two PP-unmatched causes classified 0/2. DRAFT, not promotion-ready.


## Isolated candidate outcome watch-address alias exclusion

The original outcome watch address is **unknown**. The read-only C
observer and strict Python v2 audit already reject candidate result
bytes colliding with the known player own PP, battle Flags, and pending
word. Two further EWRAM locations are already known **not** to be an
independent authenticated battle-outcome result byte: the original
wild battler count byte `0x02001AB8` (adjacent to flags), and the
original actor0 44-byte request copy buffer pointer word
`0x02001C6C..0x02001C6F`. The previous guards allowed both. A natural
battler-count change or pointer update could then be mislabelled as
an "outcome candidate byte transition", despite no outcome semantics.

Both C and Python now reject these aliases before counting any CPU
observations. C fake-core tests validate denial at boundary bytes and
permitted nearby addresses; Python synthetic tests mirror the exact
reserved ranges. Adjacent unknown RAM addresses remain candidates
ONLY, with `original_battle_outcome_decision_pc_certified=False`.
This is a conservative evidence-consistency gate, not an outcome map,
proof that a valid outcome address exists at any tested point, or
permission for original-game execution.

No private modified-ROM, Current ROM/save or emulator accessed, no
new native game hook or player inputs, no foe/NPC AI or fallback edits.
All previously independently approved exact heads and protected
main/source-first stay unchanged. Native original-game formal
acceptance 0/20, production 0%, historical PP causes 0/2.


## Isolated source follow-up: original PP STRB effective-address evidence

A mutation to one watched PP byte while the CPU reports original writer PC
0x0809E6BA, register r1 equal to that byte, and before=after+1 is **not by
itself** sufficient to classify an original PP writer instruction.
The previous Python audit could count such a mutation even when the
recorded instruction was a load, unrelated ALU operation, or a byte store
whose **actual effective address** pointed elsewhere.

The verifier now decodes the 16-bit original Thumb opcode from the C CPU
observer as either Thumb STRB immediate offset or STRB register offset.
Only if **all address operands are among the recorded r0..r4**, effective
address fits in 32 bits, equals the watched actor-owned PP slot address,
the original PC matches 0x0809E6BA, and exactly one PP was removed,
does it count a *candidate* original PP writer store. Unknown operand
registers, nonstore opcodes, mismatched address or arithmetic overflow
remain unclassified observations. The source byte value is not
authenticated because r5..r7 are not recorded; matching a byte store
cannot authenticate original action ownership or execution semantics.

Public synthetic tests exercise STRB r6,[r1,#0] 0x700E and register form
STRB r3,[r0,r1] 0x5443, while wrong base/offset, load, word store,
missing registers and overflow fail closed. The existing original-ROM
attestation path would still need independent, separately owner-authorized
immutable modified-ROM opcode parity and authentic guest replay; it is
NOT invoked. No new private data, original-game CPU stepping or
gameplay hook is involved.

This is independent source research stacked on the review-pending
outcome/PP PR69 and does not modify protected main/source-first, approved
exact heads, Current ROM/save or manual fallback. Formal native 0/20
(0%), production 0%, two historical PP causes 0/2.
