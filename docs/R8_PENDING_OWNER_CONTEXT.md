# 16266R8 — Live controller context correlated to original copy+pending

**Status:** Research-only positive native observation in ONE wild-single saved-battle fixture, plus a ROM-free request-state correction. **No gameplay code, ROM, save, foe/NPC AI, or original command emitter changed.** No automatic commands; acceptance remains **0/20**. The frozen isolated Smart AI source checklist is not a playable completion percentage.

## Why this follow-up matters

R7 verified that the original actor-0 move-request buffer-A 44-byte copy completes at frame 14369, but the native pending bit is still **clear** at the byte-copy boundary. The original engine sets it **23 guest instructions later**, in the same frame. A research lease cannot become active on the copy alone.

## Fresh read-only emulator correlation (same temporary session)

`tools/probe_live_context.py` replays the original human A input from R7, with the exact SHA-pinned experimental 16266 ROM, unmodified original user save, same pinned wild-battle state, and the alternative mGBA host from the user archive. It runs entirely on copied files, with an exact guarded Thumb prefetch refresh required due to the **savestate version warning**. This is NOT Android/device certification.

At **immediately after original copy** and **when the native actor-0 pending bit transitions to 1**, a read-only engine snapshot agrees on all these supported fields:

| Original engine property | Observed at both locations |
|---|---|
| Raw battle flags/count | `4` / `2` (ordinary wild single) |
| Battler positions | `[0, 1]` |
| Controller kind, actor 0 / actor 1 | `[1, 3]` (player signature, opponent signature) |
| Original completion callbacks | `[0x080625F9, 0x080616D9]` |
| Original controller runners | `[0x080619D5, 0x08060AC5]` |
| Public present mask | `3` |
| Actor-0 request opcode | `19` |
| Actor-0 live moves vs request moves | All four IDs matched |
| Actor-0 PP | Four values stable; original values privately retained, not published |
| Own-only native negative restriction cache | Zero in this particular fixture; **not** permission |
| Own-only Disable/Encore/repeat context | Unchanged across the observed 23 guest steps |

The only changed recorded field between those two snapshots is the **actor-0 pending word: 0 -> 1**. The request bytes also remain unchanged and match the independent older original `confirm` record by SHA256 `b92746c4fe980c1d9b05da0eddbff8a6765524390a67fd6f97950b6a41b2cf24`. This positively corroborates the native request context in this ONE emulated wild-battle fixture. It does **not** prove exclusive ownership, positive move/target legality, original-installer execution in this same process, or a current game-owned session/epoch token.

No foe move, PP, HP, ability or item memory is read. Only original controller-class metadata and the user's own battler moves/restrictions are collected. The full private observation report and actual move list are excluded from the public GitHub repository.

`tools/verify_live_context.py` runs the previously merged R7 complete-copy validator first, then checks the two consistent context snapshots, exact known public controller signatures, move-buffer equality, plausible own-only fields, raw pending bit 0->1, and restrictive no-auto/no-fabricated-installer annotations. Its public synthetic tests do **not** contain private user request bytes; they use a synthetic request and an explicit synthetic hash only for testing.

## Research state-machine correction (R4 model update)

- On confirmed original buffer-A copy, `SG_ChoiceLease` now enters **STAGED**, not OPEN.
- `sg_lease_on_original_pending(...)` opens the model lease only when a separately paired actor0 original pending event is observed for the same host-local epoch with the same verified request, opcode19 and pending bit0 *exactly* one. Wrong/stale/incomplete actor0 signals fail closed.
- Stage and open have **no gameplay authority**; `sg_lease_claim_model` still requires hypothetical positive player ownership, move/target legality and native-emitter exclusivity inputs that the actual ROM does not provide. Claims cannot run in STAGED; duplicate claims are rejected. Replaced requests, stale events, cancellation and counter overflow fail closed. Actor1 events do not open actor0 leases.
- This model is **not compiled into the ROM**. The source uses only host synthetic inputs; there is no actual engine-origin epoch identity or action gate installed.

Tests: two host C configurations (optimized and UndefinedBehaviorSanitizer) each **104 assertions PASS**. Public synthetic context tests **7 methods PASS** with missing/altered fields, false ownership, player/foe controller swap, stale pending, hidden-foe data and false auto claims denied. Public CI also runs unchanged previous source suites. Real alternative mGBA live-context replay **PASS** on the original pinned wild fixture, and read-only offline validation **PASS**; no native automatic moves executed.

## Next genuinely playable blocker

An original native controller type and matched request/own-move bytes are a *signature*, not authorization. Before any disposable automated submission, independently prove this controller was installed by the real engine for this session, a copy-to-pending lease maps to that installed player without stale callbacks, and complete choice-item/trait, target, move/PP and original rejection conditions are known **without extra side-effecting validator calls or hidden opponent reads**. Then run the first isolated native auto-move/battle tests in a disposable ROM, receive independent source/native review, and only much later consider Current promotion. Trainer doubles and NPC-partner cases remain separately uncertified.

Manual gameplay stays available. Never use in-battle items or capture automatically; never auto-select Master Ball. Do not change enemy or NPC-partner AI. No Android or speed-up certification follows.