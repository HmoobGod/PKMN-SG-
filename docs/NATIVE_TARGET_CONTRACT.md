# Target resolver checkpoint — 16265, evidence follow-up

No shipped C/Thumb or ROM change. Automatic acceptance remains 0/20. The preview still requires human confirmation. These are local results, not independently reproduced game tests.

## Original resolver coverage

The native manual menu obtains a target mode from the resolver at 0x080E0748. Its ordinary path reads the 72-byte move table's target field, but three effect IDs can override it. The optional `tools/check_native_target.py` reads an explicitly supplied, hash-pinned private 16265 ROM and executes that resolver's original instructions under Unicorn. It publishes no original bytes.

Local result: **10,192 executions**, **637 move IDs**, comprising **635 metadata-eligible damaging moves** and two additional override cases. Every tested return matches the decoded branch model. For each move, the matrix covers actor 0/2, species 25/0x599, ghost/non-ghost type-reader output and effect-predicate false/true. SP and r4-r11 are restored; executed CPU stores remain inside the bounded test stack.

| Effect | Move IDs in this ROM | Result in the tested matrix |
|---|---|---|
| 83 | 174 | Raw mode 1 with ghost output; mode 7 otherwise. Zero power excludes it from the damage preview. |
| 4 | 725 | Mode 1 or 6 depending on the conditional predicate. |
| 4 | 730 | Mode 11; excluded by the preview's mode filter. |
| 4 | 732, 827 | Mode 1; the conditional override flag is clear. |
| 321 | 834 | Mode 6 for species 0x599; mode 1 otherwise. |

For the **current immutable ROM table**, no metadata-eligible move tested returns a mode outside 1/6 through these overrides. This resolves the specific concern that these branches change an admitted raw mode into an unsupported mode. It does not prove what every targeting mode means or that every move is safe to automate.

## Reproduction and limits

Install Unicorn separately, then run:

```
python3 -m pip install unicorn==2.1.4
python3 tools/check_native_target.py --rom /private/SoulGold_16265.gba --output build/native_target/resolver.json
```

Local dependency: Unicorn 2.1.4, TI925T model executing ARMv4T-targeted Thumb instructions. The type-reader and effect predicate are **stubbed**, with both result classes exercised. This is an isolated instruction test with constructed inputs, not native gameplay, timing, IRQ, hardware or complete helper verification. No command is emitted. Public CI does not have the ROM and does not run this test. The expected branch model comes from the same resolver decode; it is not an independent engine oracle.

## Remaining automatic adapter contract

The existing native traces distinguish submission, restriction rejection and subsequent engine commit writes. They must remain separate. A zero restriction-helper return is not complete target or ownership authorization.

Before any automatic adapter, establish all of the following:

- Positive ownership of the current player choice, supported battle/session and controller callback; canonical positions and a player-like signature alone are insufficient.
- Binding to the current choice epoch, move ID, slot and PP. Cache bits remain negative exclusions and cannot authorize a move.
- Native target-selection semantics and target presence at consumption, including effect and move locks. The mode result above is only one input.
- Exactly one original submission, followed by observed native acceptance or manual recovery on rejection. Never call the side-effecting restriction helper an extra time to obtain permission.
- Cancellation, held-B, disabled settings and controller/session changes must prevent automatic submission. No items, capture, Master Ball, NPC-partner AI or doubles automatic choices are authorized here.

The next implementation task is the ownership/choice-epoch contract around the original consumer, not removing human confirmation on the strength of these resolver tests.
