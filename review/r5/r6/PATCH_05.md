# R6 patch 05 — Forbid every player0 automatic action except Fight and Move

Status: local independent source-only draft; no game integration, no native acceptance.

Static policy alone cannot disable existing ROM switch branch; must attach at original emitter and test native rejection.

Test: `PYTHONPATH=r6 python3 r6/test_patch05_switch_block.py`

Review requirement: independent Claude source/test/security review before integration.
