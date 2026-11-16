# R10 — original-controller request/PP store lineage verifier (SOURCE ONLY)

This is a **read-only evidence-auditing research tool**, not a game patch, source-to-ROM exact-map attestation, emulator injection, action emitter, gameplay AI, or manual fallback implementation.

The owner-authorized private mGBA lab observed the **existing, unmodified original ROM** constructing and copying complete 40-byte player `ChooseMove` buffers, maintaining separate player/opponent receive buffers, and later executing the original one-byte PP-decrement instruction on a compatible player slot. Three bounded private instances satisfied this auditor; their full private CPU records, target addresses, ROM, save, memory snapshots, and emulator binaries **are not present in this PR**.

## What this checks

- CPU store events in chronological order, with a private caller-provided exact-binary pointer/PC pin set (never embedded in public source).
- Original command 19, 40-byte request, header 19/0/0/0, four little-endian 16-bit move identifiers, current PP and max PP consistency.
- Original producer's command-header store, later byte-by-byte payload construction, and later **byte-identical controller receive copy in the same frame**.
- Original player-owned Fight and Move responses with **separately observed actor 0**, original response store and two expected return sites.
- Separate non-player receiver, preventing attribution of the opponent request to the player.
- One original PP writer event, exact 1-PP debit to one of the four compatible player slots before the next request; later request reflects the earlier debit when present.
- Strict bounded records, malformed/duplicate/orphaned event rejection, no native/gameplay success flags.

## Review and usage

Run fake-only tests (requires Python 3):

```bash
PYTHONPATH=review/r10 python3 -m unittest discover -s review/r10 -p 'test_*.py' -q
```

Authorized private users may import `Pins` and `audit` inside their *private* game lab. The interface expects normalized CPU store rows, original response rows with **actor** explicitly identified, original PP writer rows, and a private exact-binary pin set. It produces only redacted candidate metadata. **Do not add a private config, raw dump, emulator binary, ROM, save, screen image or CPU trace to GitHub or Drive.** The official original-game binary and all unknown game state stay untouched.

This verifier is not itself a source of truth for its input records or pins. It trusts a private observer to authenticate emulator identity, CPU stores, actor decoding, before/after bytes and request episode boundaries. Fake tests do not prove such authentication.

**Important limitations:** These are **original-ROM candidate sequences**, not execution of a new Smart Auto-Battle adapter. The proof does not include engine-owned one-use request IDs, current dynamic move/target restrictions (Taunt, Disable, Encore and targeting), original manual control, absence of all forced-Switch paths, unambiguous cancellation attribution, or exact source-to-ROM complete symbols. An R7 adapter run in a private **read-only shadow** on the captured original request buffers properly **deferred** because the original legality callback was not authenticated; it never issued a guest move.

Formal native Smart Auto-Battle acceptance **0/20 (0%)**. Production **0%**. No merge, installation or release authorized. Independent exact-head Claude source/test/security review is mandatory for this isolated draft, and no sibling approvals transfer.
