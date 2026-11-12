# Pokémon SoulGold — exact customized-ROM PP slot + original-controller candidate lineage, 2026-11-12

**Scope:** original modified-ROM CPU research only. This is not a Smart Auto-Battle source-LAB patch and does not grant production approval. The private test ROM is SHA256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44` (32 MiB). Exact PC markers in both ROMs have matching short opcode windows, but that static parity does not authorize transplanting findings between the ROMs.

## Live new diagnostic capture

* `native_v6`: A fresh encounter reached the wild Electabuzz opening line but stopped there without a host text-confirm key; **zero PP CPU stops**. This is an actual no-progress blocker for an uninterrupted text-to-battle test; DO NOT claim uninterrupted auto play from it.
* `native_v7`: The operator explicitly sent **one host `x` inside the wild encounter to advance its opening text**, logged as `HOST_DIAGNOSTIC_BATTLE_NARRATION_ACK_NOT_UNATTENDED`. It captured in the SAME mGBA process original PC `0x0806BD80` actor0 emitter markers, original `0x0806B370` actor0 copier **entry** (not completion), original `0x0806261C` completion PC and original validation/move/target program counters. Original PP source, actor0/foe PP address and proposed new values were seen, but the adjacent-breakpoint stepping skipped the final `0x0809E6BA` store stop. **No certified new PP byte-store in v7**.
* `native_v8`: A separate fresh exact-ROM process, same explicit host narration confirmation (thus NOT unattended) and a corrected two-step single-instruction probe, captured **two full original PP-read/decrement/effective-address/store chains**, one foe and one player:
  - Opponent r0=1, move slot 1, original PP address `0x02001F8A`, actual GDB memory **15→14** after original Thumb STRB CPU PC `0x0809E6BA`.
  - Player r0=0, move slot 0, PP address `0x02001EF1`, actual GDB memory **20→19** after original Thumb STRB CPU PC `0x0809E6BA`.
  - The CPU computations are from original `0x0809E69A` PP read; `0x0809E69E` decrement comparison; `0x0809E6B0` stack move slot/new PP; `0x0809E6B4` actor-indexed base (`base + actor*0x98`); `0x0809E6B8` address plus 0x25; and a **second single-step** through `0x0809E6BA` store. The read-before/write-after values match actual RAM.
  - Original actor0 emitter, actor0 copier-entry, move-commit and candidate copy-postloop PC hits are real, but **not linked by an authenticated one-use engine request epoch**. A postloop hit is not linked to the particular player request unless source/destination/count match and is not an AI authority grant.
  - One trailing incomplete PP instruction chain excluded from complete count.

## Validator and fail-closed claims

`tools/verify_original_pp_slot_lineage.py` reads the original CPU event JSON, the explicit host log and optionally *rehashes the private exact test ROM*. It audits chronological original Thumb PP source, actor, slot, stride, computed PP/new PP, and a twice-single-stepped final STRB. It keeps original emitter/copier/commit PCs as candidate markers only, and reports that this test was host-input contaminated. The **16 synthetic tests** exercise successful actor0 and foe PP chains, host-input disclosure, ROM identity refusal, invalid PP/slot/actor/stride, step ordering, truncated chains, and the limits on controller inference. Synthetic pass is not original guest execution. No material from the original private ROM/SRAM/savestate is embedded.

**Unresolved:** Two historical PP-unmatched submissions #1/#2 remain each **UNCLASSIFIED (0/2)**, without stitching to v7/v8. No source-LAB native installed auto-control, one-use request/response generation, command acceptance with legal move/target, dynamic legality, cancellation cause, terminal-independent manual fallback, or fully unattended text-to-battle-to-next-wild replay certified. Formal native acceptance **0/20 (0%)**, production hybrid 0%. No change to protected Current ROM/save/main, foe or NPC-partner AI, automatic items/capture, or uncertified doubles.

## Integrity

Private original ROM and input SRAM are read-only, with the emulator running disposable copies. The exact protected Current ROM SHA256 `7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32` and save SHA256 `8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4` are rehashed unchanged. ZIP includes JSON CPU event transcripts, host key/CPU console logs, source verifier/test, verified v8 report and SHA256 manifest. **No ROM, SRAM, or savestate bytes.**

## Development policy

This is a separate lab-only batch. PR #21 stays Claude-approved only at `1666676d8b158c585033266c7f71e7a4ba545cd8` and draft. PR #22 stays draft at `8025b6a6aa2985e4090f4fef653e3824e98bc60f` pending independent review. This new source/test tool must be independently reviewed at its OWN exact head and pass GitHub CI before any research merge; never count these observations toward native acceptance.
