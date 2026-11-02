# Development status — 16266

Local baseline imported November 2, 2026. Source-only GitHub migration; original playable ROM and save remain separate.

## Verified locally before import

16265 adds a negative raw-target-mode filter (1/6) to the assisted preview and preserves 16264 held-B bytes. Local results: 348 shipped-C cases, 18 consistency cases, 32 trainer/controller regressions, native preview/override checks, and paired 1208-frame trainer parity. These are historical local results; public CI does not reproduce them.

16263's eligibility refactor received independent static review with no defect found. The combined 16264/16265 code review remains pending. No automatic enablement, Current promotion or phone trial approval.

## Current behavior and constraints

16266 adds pending-request exclusions to both captures. A missing actor pending bit or a request opcode other than19 rejects the first capture before allocation. If this specific phase check fails after scoring, status0 chains the native path without writing the cursor or installing the preview chooser. Other failed rechecks retain the reviewed status5 manual fallback. This is a negative phase check, not ownership or an epoch token. Claude approved the exact PR5 source change at8dfe5b8db4ffca6b6b76fcf738c18bce66b1d5ad with no blocking finding. Original dispatcher provenance and runtime/build claims remain unverified by that reviewer.

- Human confirmation is required; a recommendation is not action authority.
- Supported held-B override: actor 0, player-controller signature, flags 4/count 2 wild context only.
- Unsupported raw target modes are excluded conservatively, potentially prompting manual choice for legal moves.
- A clear restriction-cache bit grants no permission. Cache freshness is unproven for natural restrictions.
- Native submission, restriction-return and later commit writes are distinct stages. A zero restriction return is not complete target/ownership authorization.
- Preserve manual/default-disabled behavior, the existing player save, enemy/NPC-partner AI, and no automatic items/capture/Master Ball.

## Next work

1. Finish combined 16264/16265 independent source review.
2. Effect-specific target resolver overrides now have isolated original-instruction coverage (see NATIVE_TARGET_CONTRACT.md). Native target selection, controller/session ownership and automatic submission remain unproven.
3. Private-input build migration implemented: tools/build_private.py reproduces the exact16266 hashes from a SHA-pinned private16265 ROM. Native replay migration and reconstruction of that base remain pending.
4. Expand natural encounters, settings-screen default tests and metadata/UI checks; stack headroom, IRQ, Android/speed-up and cave reference closure remain open.

The historical source checklist being complete does not mean in-game Smart AI integration is complete. Overall percentage estimates are retired; track these milestones and automatic acceptance 0/20.

## Import review and build migration

PR1 at0a5648b378e25b412c817192ea597b34563cecce received source-import approval with no blocker (reviewer inspected the archive, did not independently verify GitHub identity/CI). GitHub CI was independently checked before merging. That approval does not certify installed hooks, native replay or automatic enablement.

checkpoint.json base_sha256 is now the private16265 ROM (deef0016...). The earlier PR2 builder consumed16264 (db9142...). Both bases inherit the held-B hooks and safety patch. The current builder replaces only the scorer cave; exact local16266 reproduction passed for ROM, cave and IPS.

## Review scope clarification

PR5 source-level phase-guard review is approved; exact-head CI was rechecked before source merge. Capture and diagnostic return meanings are in STATUS_CODES.md. PR1 approved the source import, PR2 the builder/boundary tooling, and PR5 the phase-guard diff. Those scopes do not constitute the earlier combined16264/16265 installed-hook and target-filter implementation review. That earlier scope remains open deliberately; it is not resolved by relabeling it. No automatic enablement, ownership or choice-epoch claim is approved.
