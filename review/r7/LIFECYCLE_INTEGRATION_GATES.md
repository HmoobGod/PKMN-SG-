# R7 R5 native prerequisites (unverified)

The lifecycle wrapper is a conservative host-side *model*. Before connecting it to a private disposable ROM test, independently locate and validate the original-game:

1. Engine-owned request-id and battle epoch values; prove their identity, lifetime and whether IDs can be reused or wrap. The wrapper assumes the host exposes nonzero 32-bit identities from the original controller; it does **not** manufacture evidence of their provenance.
2. Original controller buffer mapping for ChooseAction (4 bytes) and ChooseMove (source-hypothesized 40 bytes), original dynamic legality and target checks, and proof that game state cannot change undetected across the required read–legality–read sequence.
3. An original battle-close/idle witness for `read_verified_boundary`, preferably independent of the caller constructing leases. The callback's return value and event fields alone are not an authentication certificate.
4. An original, actually controllable manual menu takeover witness for `verify_original_manual_takeover`. Until found, do not invoke this API to claim fallback: leave automation deferred and keep the existing menu untouched.
5. Exhaustive original auto-Switch route testing, cancel/back behavior, PP writer causality, win/lose and overworld return using **disposable** game copies. Do not modify enemy/NPC AI, auto items, capture, original ROM/save or player-choice behavior.

The session refuses to auto-resume a battle from a stale Fight ticket. It can retire that ticket on a verified engine epoch transition, or lock the rest of an epoch to manual after a verified original menu takeover. It **cannot** safely expire a same-epoch ticket solely because time or frame count passed.

No source-only test promotes formal native acceptance: **0/20 scenarios; production 0%**. No PR is merge-eligible until independent exact-head review and separate authorization.
