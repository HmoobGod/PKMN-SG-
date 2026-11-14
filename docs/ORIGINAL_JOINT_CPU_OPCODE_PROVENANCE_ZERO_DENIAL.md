# Original joint CPU evidence — mandatory ROM program counter on every event

**Scope:** isolated source-first research DRAFT stacked on independently
Claude source/test/security-approved PR49
`fcd708663f85ce198af4913925729fe2d7224c64`, unchanged. No
game binary, ROM, save, emulator, original trace or guest execution.

## Proven provenance defect in existing offline verifier

The original `verify_exact_joint_player_terminal.audit()` permitted
`pc=0,opcode=0` in *any* event as an "unknown" original CPU PC, including
native Main.clear and callback memory transitions. The corresponding
`attest()` loop intentionally **skipped** such events:
`if not e["pc"]: continue`. Therefore, even when exact immutable ROM/save
input hashes were checked, any tampered or imperfect event with
PC=0 avoided its own original modified-ROM opcode comparison.

One synthetic transcript could claim Main.inBattle cleared and a callback
followed, without any known original CPU PC for the purported Main clear.
The audit still returned descriptive main-clear/callback evidence. That
is **not suitable** for eventual original-game outcome attribution.

## Fail-closed change

- Every recorded CPU event must originate at an aligned halfword
  `0x08000000..0x09FFFFFE` ROM PC and carry a 16-bit instruction opcode.
  Unknown, RAM, BIOS, odd and zero PC are rejected. This deliberately
  rejects some formerly tolerated incomplete C trace captures.
- `attest()` no longer skips ANY event when checking the exact original
  modified-ROM instruction opcode at that address.
- No change to the actual C observer, its original CPU marker identities,
  user game, player controller, PP policy, outcome classification, or
  approval/promotion flags.
- Existing strict original joint audit tests remain source-only; eight
  added negative/positive cases cover zero PC on Main clear, callback1,
  callback2, PP, odd PC, RAM PC, oversized opcode and intact original
  fake complete sequence with no production promotion.

This change complements review-pending PR57 C tracer chronological PC
hardening but does not depend on it, merge it or alter its head. If the
live original game ever legitimately executes ROM-adjacent RAM code,
a separately reviewed byte-authenticated provenance format is required
rather than silently accepting unknown instruction identity.

**Limit:** An exact opcode on *recorded events* does not prove the
provenance of skipped or unrecorded guest instructions between events,
or establish engine-owned player0 one-use request, dynamic move/target
legality, PP cancellation, native battle outcome decision, return to
overworld, safe manual fallback, or game/save compatibility.

Formal original modified-ROM native gameplay **0/20 (0%)**.
Production player0 Smart Auto Battle **0%**.
Two historically unmatched PP causes classified **0/2**.

Keep new head DRAFT/unmerged and require completed full Source CI and
a fresh independently Claude exact-head source/test/security review;
PR49 approval does not transfer. Protected main, source-first,
original Current ROM/save and all approved exact-head parents untouched.
