# Original outcome-writer PC discovery — bounded Thumb STRB scout

**Checkpoint scope:** SOURCE-ONLY read-only research on `source-first/rom-identity`, based on authenticated commit `f3d5547bf5f5eab228e15c72fcece3a352ce13ec`. No active installed hook. Do not modify protected Current ROM, save, experimental modified ROM, public main or opponent/NPC-partner AI.

## Problem actually addressed

Three independent natural wild-single fixtures exist. The third establishes a real original `gMain` callback1/2 handoff at exact Thumb PCs `0x0808E33C` and `0x081AED58`, with `gMain.inBattle` cleared while older battle flags remain `4`. **No exact original battle-outcome decision/writer PC, outcome variable address or full no-input battle-end result is authenticated.** The older second fixture has 8 original player-owned move submissions/commits but only 6 original PP *snapshot* deductions. The two unmatched submissions cannot be called executed, canceled, misses or freebies without original CPU/PP-write instruction coverage in the SAME fixture.

Prior source-only watcher (`trace_exact_outcome_pp_edges.c`) requires a caller-provided candidate outcome RAM byte address; inventing it is unsafe. This patch adds **`tools/trace_exact_thumb_byte_stores.c`** to scout original CPU Thumb-1 `STRB` write instructions without hardcoding that missing outcome variable address.

## What the source-only observer does

- Reads the CPU's pre-instruction register values, original Thumb halfword from original ROM bytes and a caller-bounded EWRAM or IWRAM interval. Supports **Thumb-1 `STRB` immediate** (`0x7000` family) and **Thumb-1 `STRB` register** (`0x5400` family), using decoded base/source/offset registers.
- Advances **one original guest CPU instruction** through the pinned mGBA host's existing guest-step callback, reads the guest destination again, and emits a candidate only when the observed byte **actually changes** and equals the original source register's low byte. Records original source PC, opcode, registers, address, original frame, and battle flags/battlers/pending/Main inBattle/callback1/callback2 context.
- Limits values to **0..7** on both sides of the transition to reduce noise. The real battle outcome might have other values; failure to observe a write has **no negative significance**.
- Accepts one bounded RAM region per run: EWRAM `0x02000000`–`0x0203FFFF` **or** IWRAM `0x03000000`–`0x03007FFF`. It rejects MMIO/save/video ranges, empty/oversized steps or event capacities, and returns explicit status 3 when event capacity overflows. Status **1** means full requested frame budget was reached; **2** means instruction budget exhausted; only status 1 is accepted by the offline verifier. This observer cannot itself assert that a battle terminated, even if all callbacks changed.
- Does **not** decode ARM-mode, DMA, `STR`/`STRH`, indirect buffer copies or other code paths. It also does not prove the CPU's Thumb state from the host's register layout alone. Thus it can identify candidate native byte-store PCs, not establish that the outcome variable has been found.
- The code makes no guest memory, ROM, save, controller, input or player/enemy AI writes. Its use assumes the **existing pinned host ABI** (offsets `0x13E8`, `0x1428`, `0x1488`, `0x1498`); these callbacks are not re-certified by this source-only build against an actual emulator host.

## Exact trusted input identity for the next genuine private replay

- Protected Current ROM: SHA-256 `7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32`, length 33,554,432 bytes.
- Separate exact modified test ROM: SHA-256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44`, length 33,554,432 bytes. **This file was not mounted in this source-only session.** Do not substitute Current ROM, source-lab compiled ROM, or unrelated older mod ROM.
- Original protected save: SHA-256 `8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4`, length 131,072 bytes.
- Prior third-fixture Main callback original CPUs/writer windows have already been authenticated separately; no new original runtime witness is claimed here.

## One real protected-ROM static instruction anchor (not a replay)

The user-supplied protected Current ROM SHA-256 `7b9ac66d...` was read *without modifying it*. At original native own-PP writer CPU PC `0x0809E6BA` the exact two bytes are `0E 70` (Thumb halfword `0x700E`), correctly decoded by the scout as **`STRB r6,[r1,#0]`**. This is consistent with the earlier 64-byte protected/modified writer-window parity and establishes the scout handles a known real native Thumb byte-store encoding. It **does not** identify the missing battle-outcome writer or prove another original PP debit; no modified game replay occurred.

## Suggested two-pass disposable exact-ROM replay

1. Use a **copy** of exact modified `4b2585e1` ROM, protected original save and pinned mGBA host, ideally replaying privately retained second/third wild original pending states. Never write these assets. Begin with no player move-menu buttons, no guest RAM mutation, and no new gameplay hook.
2. Run `sg_trace_exact_thumb_byte_stores` first with whole EWRAM range, then separately with IWRAM range, spanning **original pre-terminal action through the Main callback handoff**. Supply a generous but bounded original guest step budget and buffer cap; if status 2/3, *no completed witness*—restart with a narrower RAM range or larger appropriate budgets, never silently suppress events. Watch event rate/host performance; every recorded candidate must have a pre-instruction register/memory write relationship.
3. Marshal its C event struct (19 scalar fields plus `registers[8]`) and run summary into strict JSON schema `sg-exact-thumb-strb-store-scout-v1`. Use `tools/verify_exact_thumb_byte_stores.py --private-trace TRACE.json --current CURRENT.gba --modified EXACT_MODIFIED.gba --save ORIGINAL.sav` **locally only**. The verifier requires exact SHA-256 ROM/save identities, completed frame budget, strict event types/order, mathematically decoded Thumb STRB source/target and the *real original modified ROM bytes* for each purported instruction. It reports protected Current 16-bit opcode parity separately; non-parity is not proof of an unchanged original instruction.
4. Compare candidate byte-store events from frames around the previously authenticated callback1/2 handoff against independently derived original `gBattleOutcome` storage (source symbol/global pointer mapping + original CPU address/register evidence). **Only then** narrow the original outcome address and rerun the existing `trace_exact_outcome_pp_edges.c` outcome address watcher; independently establish original outcome decision branch PC, result meaning, native terminal and return to functioning overworld, including an uninterrupted no-button replay. Do not infer outcomes from a single callback or `flags4/battlers2/pending0`.
5. For the older **8 submissions / 6 PP snapshot deductions**, replay the **same original second wild** under `trace_exact_outcome_pp_edges.c` and `verify_exact_actor_epoch.py`, with exact original native PP debit PC `0x0809E6BA` and known confounding `0x081FB8DA` and bulk-copy stores. If a submitted action lacks a matching original PP writer event, investigate original restriction, faint, cancellation and outcome/turn sequencing; classify only after instruction and result witnesses.
6. Test original Disable/Encore/Choice/Imprison and target changes, one-use player request ownership, denied/canceled submissions and manual fallback on exact modified ROM. Preserve automatic gameplay preference and fail closed on uncertified doubles/trainer/forced switches/Struggle and all automatic item/capture/Master Ball actions. Independent safety review and 20/20 real acceptance remain mandatory before any production modification.

## Tests and promotion limits

- `cc -std=c11 -Wall -Wextra -Werror -pedantic -O2 -o /tmp/sg_test tools/test_exact_thumb_byte_stores.c && /tmp/sg_test` runs a **mock CPU core** with real guest-like pointer-step/read callback ABI and actual simulated Thumb STRB changes. The mock is not the real modified ROM.
- `python3 tools/test_exact_thumb_byte_stores.py` runs strict **synthetic denial** and schema/decode tests, not original gameplay.
- `python3 -m py_compile tools/verify_exact_thumb_byte_stores.py` checks Python compile.
- `source-check.yml` should include all three after integration; unchanged `source-first/wild-single-lab.patch` requires **no new GNU ARM build** for this diagnostic-only batch, and its previous ARM-green result must never be credited as native modified-ROM gameplay proof.
- No new playable ROM, battle outcome, matched old PP deficit, dynamic legality or safe terminal is certified by this source-only observer. **Formal native gameplay acceptance 0/20 (0%) and production hybrid installation 0%.**

**Privacy:** Only bounded source, tests, documentation and SHA-256 hashes may be pushed to public GitHub/Drive. Do not upload exact modified ROM, Current ROM, save, original guest CPU/raw RAM transcript, mGBA host or savestates. Keep them private for authenticated local replay.
