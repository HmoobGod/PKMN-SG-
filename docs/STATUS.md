# Development status — 16265

Local baseline imported November 2, 2026. Source-only GitHub migration; original playable ROM and save remain separate.

## Verified locally before import

16265 adds a negative raw-target-mode filter (1/6) to the assisted preview and preserves 16264 held-B bytes. Local results: 348 shipped-C cases, 18 consistency cases, 32 trainer/controller regressions, native preview/override checks, and paired 1208-frame trainer parity. These are historical local results; public CI does not reproduce them.

16263's eligibility refactor received independent static review with no defect found. The combined 16264/16265 code review remains pending. No automatic enablement, Current promotion or phone trial approval.

## Current behavior and constraints

- Human confirmation is required; a recommendation is not action authority.
- Supported held-B override: actor 0, player-controller signature, flags 4/count 2 wild context only.
- Unsupported raw target modes are excluded conservatively, potentially prompting manual choice for legal moves.
- A clear restriction-cache bit grants no permission. Cache freshness is unproven for natural restrictions.
- Native submission, restriction-return and later commit writes are distinct stages. A zero restriction return is not complete target/ownership authorization.
- Preserve manual/default-disabled behavior, the existing player save, enemy/NPC-partner AI, and no automatic items/capture/Master Ball.

## Next work

1. Finish combined 16264/16265 independent source review.
2. Classify effect-specific native target resolver overrides and controller/session ownership before any automatic adapter.
3. Migrate build scripts to explicit private input paths, eliminating older-checkpoint directory assumptions.
4. Expand natural encounters, settings-screen default tests and metadata/UI checks; stack headroom, IRQ, Android/speed-up and cave reference closure remain open.

The historical source checklist being complete does not mean in-game Smart AI integration is complete. Overall percentage estimates are retired; track these milestones and automatic acceptance 0/20.
