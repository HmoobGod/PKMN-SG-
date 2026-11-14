# Original joint actor0/PP/Main CPU chronology: bounded fail-closed evidence

This isolated source-research DRAFT builds DIRECTLY on independently
Claude source-approved PR49 exact
`fcd708663f85ce198af4913925729fe2d7224c64`.
PR49 and other approved exact heads remain unchanged.

## Specific false-completion risk

The original joint player0 C CPU observer already rejected frames
earlier than its starting frame. However, a bounded capture could
still observe frames 3200 → 3201 → 3200. All values are greater
than or equal to the start, so the previous check would accept that
**in-window clock rollback**. A later frame 3202 could then mark the
capture complete despite an invalid chronology.

The old C observer also set `pc=0,opcode=0` for a CPU instruction
outside the authenticated GBA ROM execution window, including raw
PC=0 or odd CPU addresses. This permitted unknown-CPU guest steps
to appear in a trace of supposedly authenticated original ROM
code; downstream attribution can fail to detect silent unknown
execution where no event happened. Actual ROM opcode parity in
the offline `attest()` verifier cannot attest a non-ROM PC.

## Changes

- Store the previous frame observed at every guest instruction.
  Reject a decrease before even one more step, returning status=5,
  whether it falls below the start or only rolls back **within** the
  claimed frame window. Check final frame against the last observation.
- Before any event or guest step, require an aligned raw Thumb PC
  in the exact original ROM window. Deny raw PC=0, odd PC and
  execution from otherwise unproven RAM/BIOS; return status=6
  rather than laundering them as `pc=0,opcode=0`.
  This conservative rule may reject a legitimate but unapproved
  RAM-running trace; that trace would need a separate original
  RAM opcode/provenance contract instead of automatic acceptance.
- Preserve the existing 1024-event/10000-frame, 32-bit step bounds,
  unchanged marker PCs, real read-only original CPU observer,
  native RAM fields, event schema and offline strict Python audit.
  The change adds NO outcome or manual-fallback certification.
- A new strict C fake-core test uses the actual observer on a
  synthetic 11-step actor0/PP/Main/callback baseline, a rollback
  at 3201 → 3200, invalid PC at initial/after one step, odd PC,
  unapproved RAM PC, oversized event/frame boundaries and
  an original 49-test Python audit. CI additionally proves that
  `-DNDEBUG` cannot silently disable test assertions.

## Limitations and safeguards

This is a **research evidence-validity fix**, not a change to live
controller hooks or a playable game. All test CPU instructions,
frames, PP and callback fields are fake memory-only fixtures.
It does not stage, execute or modify private Current ROM/save,
original modified ROM, savestate or commercial emulator binary.
No guest writes, item use, capture, enemy/NPC-partner AI changes,
trainer/doubles certification or new automatic behavior.

Formal native modified-ROM acceptance 0/20 (0%).
Production Smart Auto-Battle 0%.
Two historical PP-unmatched actions resolved: 0/2.

Require exact-head independent Claude source/test/security review
and completed Source CI plus the isolated public C workflow;
remain DRAFT/unmerged. Older PR49 approval does not transfer.
