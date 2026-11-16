# R5 R3 — Independent regression-only follow-up to PR107

Source-only, no private game material. Not gameplay integration and no native acceptance.

Adds `test_private_r7_cursor_regression.py` with an isolated nonzero-pointer re-point negative that does not depend on a later exception; exact [3,3], [1,1], [1,3], [3,1], [3,0], [2,3] slot-pair expectations; and explicit assertions that all original-game certification/production flags remain false. Separately checks the clear-state `before` half, the underlying-audit passthrough, and slot write count. Never reads ROM, save, RAM or CPU traces.

The existing PR107 R2 files and approvals remain untouched; this PR needs a fresh exact-head Claude source/test/security verdict. R5 still is not installed in the game. Formal native acceptance 0/20; no merges/releases.
