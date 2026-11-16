# Native acceptance gate — separate from real-ROM observation

- Existing uploaded ROM/save fingerprints: checked privately before/after; do not include them in GitHub.
- Emulator: original pinned mGBA Linux executable extracted privately from the user-supplied source archive.
- 8,000 frames, one authentic original Fight→Move→PP CPU candidate under source/target register and PP checks.
- The CPU-writer PP decrement is a **candidate**, not a certificate of selected move and player-owned request provenance.
- `new_smart_auto_patch_executed`: **false**. No new gameplay patch installed, compiled into ROM, merged or released.
- `input_free_auto_battle_certified`: **false**; D-pad direction was requested into the battle transition.
- `original_request_buffer_abi_certified`, `player0_request_and_legality_certified`, `original_manual_menu_fallback_certified`, `no_forced_switch_safety_certified`: **all false**.
- Formal native Smart Auto acceptance: **0/20**. Production **0%**.

A later native acceptance attempt must instrument actual source-to-ROM-mapped engine command 17/19 payloads, dynamic move/target legality, request leases, manual fallback with human inputs, player0-only Switch suppression, PP cause and outcome/overworld return. Replay from **disposable** originals only. No private game files, trace data or screenshots may be uploaded to GitHub/Drive.
