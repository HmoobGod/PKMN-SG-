# v1.1.4 isolated engine reconstruction — cycle 1

Status: **source overlay only; hard-disabled, non-production; Current replacement prohibited**.

Upstream: https://github.com/Eemeliri/soulgold/tree/afd290f7f8f965c73aa1ac6a1ae3196895d971db
Recovery checkpoint: https://github.com/HmoobGod/PKMN-SG-/pull/158#issuecomment-7154266395
Patch commit: c6fa19c649b88c11525ae1819bf2579530c3015f
Patch blob: d57e0188a361153e112218715243c139556b33f7

This is a unified diff against the actual upstream engine, not a standalone lifecycle model and not a fixed-address ROM patch. The reconstruction branch is a child of PR158; it does not contain the full upstream engine tree. Use a separate checkout at the exact upstream commit to apply the overlay. Do not apply it to the supplied v1.2 archive: battle_util.c and battle_main.c in that archive differ from the pinned upstream files.

## Source changes

- Source-native player action entry contains a hard-disabled Fight-only branch. Held B and the original menu path are preserved. Only ordinary actor0 wild singles, living player/foe, correct positions and party index bounds are eligible in the future. All shiny foes are conservatively excluded until the exact existing registry and save-bit semantics are reconstructed. There is no new flag or save field.
- Battle utility contains linker-owned EWRAM receipt storage, bound to actual battle resources, turn and party indices. Static storage was chosen instead of a separate heap allocation so it cannot itself starve subsequent checked heap allocations; actual linker RAM placement and budget remain unverified.
- Original CheckMoveLimitations is invoked exactly once in the natural Fight consumer. Original no-valid-moves side effects and normal AreAllMovesUnusable callers remain. The new internal capture path records the mask and the actual typed ChooseMove buffer at its existing producer/issue site only for a marked automatic Fight. It does not grant legality, certify a complete copy or create a native lease.
- Reset at battle allocation/free, new actor0 action phase, non-Fight action, all-unusable branch, legacy Encore branch and original manual ChooseMove entry. No scorer, automatic Move response, target/ability permission, item/capture/switch emission or registry writes. Foe and NPC partner controllers are not edited. Do not enable the hard lock yet.

## Exact source admission

Before any separately authorized local build, verify the checkout HEAD and these five Git blobs:

- include/battle_util.h af6792f66093707b0493702cd494c8a4bfa1a478
- src/battle_util.c 366baa33513cd44a327e9397a2581e806bd429d6
- src/battle_controller_player.c c4b55a547dc42d49e03daa8c45098350b65660da
- src/battle_main.c 8e1b70ed9665424567c0b379a324cae178342602
- src/battle_util2.c 492ecdf76256cb08551695ec1dce4790ad87d81d

Use git apply --check against the exact clean checkout, then git apply only there. No Current ROM/save inputs. A separate build/validation cycle must verify source compilation, actual EWRAM placement and remaining RAM/stack, controller cancellation/reissue coverage and disabled-path parity. No whole-game compilation, ROM generation, emulator execution or native application was performed in this cycle.

## Evidence and open requirements

Independent readback reconstructed every hunk against all five authenticated upstream files (12/12 hunks, exact context and line counts); reverse substitutions restored the originals during generation. The patch hard-lock and one original restriction-call site were checked as source text. This is not compiler or runtime validation. The supplied archive locally matched three of five exact blobs; battle_util.c and battle_main.c differed. No source from private game ROM/save or raw gameplay artifacts was published.

Current remains untouched. Historical restoration/3x EXP, native toggle, shiny generation/registry, custom trainer/ability/move/balance content, save layout, hidden-menu Auto and the other custom modifications still need reconstruction and parity evidence before any replacement. Historical installation report: https://drive.google.com/file/d/1Qm6hGKHE3tUYbWX-OhhkfbxgXpaQQUsV/view . The original developer source by itself does not preserve these custom features. No automatic items/capture, no automatic switching, no enemy/NPC AI changes. Formal native acceptance 0/20; R5 NATIVE HOLD; Auto-Switch2 NO-GO.

Next: compile/check this exact disabled engine overlay in an isolated upstream checkout with a verified local toolchain; correct only actual compiler/linker issues, inspect static EWRAM fit, and then recover exact custom save toggle and shiny registry binding before enabling any automatic path. Do not restart a detached model or test Current.
