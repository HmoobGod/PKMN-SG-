# Pokémon SoulGold — R5 proposed Choice field literal correction (SOURCE REVIEW ONLY)

**Exact approved R4 remains unchanged.** This isolated candidate is **not** a permitted deployed patch, not an independent approval, and not a ROM or save. Do not merge, release, install, or put private game bytes in this branch.

## Scope

Change exactly one assembly source line in a *separately named* candidate:

```diff
-.Lchoiced_offset:  .word 364
+.Lchoiced_offset:  .word 380
```

R4 source SHA256 `ce8d38b718939243a99eed560d250ed30e15b29255a0b4f0c21f3cd3ced12333`.
R5 review-only source SHA256 `1f3fc5570adeabbbdc2dcbddf4a0b86334aececd074a77b4ce29e7276e2f6daf`.
Original compiled R4 Thumb section: 252 bytes, SHA256 `d588d77c7096afcf9130b445d184ef06842f7599da92649c65ae73d637abc584`.
New compiled R5 Thumb section: 252 bytes, SHA256 `8a923d145a8718ded7b8e32b33aaa1de88a85c2c314cdeb34c79135821cc6d89`.
**The entire output byte comparison contains only one changed byte: zero-based offset 236, `0x6c`→`0x7c`.** No instruction, veneer, branch, guard or payload length changes.

## Why

The public-source header-only `gBattleStruct->choicedMove[0]` layout calculation used `+364`. On the **owner's already-authorized private, original-ROM** native mGBA 0.10.5 run, the compiled original-engine `CancelerChoiceLock` guest routine was mapped at `0x08099F2C` and its live store at `0x08099F92`: with legitimate Choice Band 442, original engine-selected Shadow Punch 325 and valid pointer `0x0201B2F0`, one CPU instruction wrote 0→325 at pointer **+380**, while +364 stayed zero. Later native R4 hook entry saw lock 157 at +380 and zero at +364 during a natural Lickitung encounter. See GitHub issue #151 comments `6957876617`, `6958002061`. This file contains **no private disassembly, copyrighted game bytes or native raw traces**.

## Independent review checklist

1. Verify both source hashes, full file diff, and `python3 test_r5_choice_literal.py` (**four source-only checks**). No private ROM required.
2. Verify `+380` is the player0 16-bit move lock on **this exact installed compiled ROM**, and that the R4 `+364` dereference could return an unrelated field value. Independently assess safety and all other constraints.
3. Verify that checking the *real* lock before independent held Choice item and Gorilla Tactics fail-closed gates is sound; discuss sentinel values and nonmatching/cleared lock cases, including active Encore/Disable/Torment/Imprison.
4. Verdict APPROVE / REQUEST CHANGES on **only this new candidate hash**, no approval transfer from R4. The native locked-Taunt/Oblivious strict negative case and authentic Gorilla/other restrictions are NOT certified.

No build script is modified to accept this candidate, so the approved R4 fail-closed builder still **rejects R5**. The current R4 source remains the sole approved candidate. Formal independent native acceptance remains **0/20** and production **0%**.
