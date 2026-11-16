# R6 patch 07 — Single-use player request lease with exact identity checks

Status: local independent source-only draft; no game integration, no native acceptance.

One-use in a host model is not proof of a native engine-owned request: must be bound to command lifecycle at real game boundary.

Test: `PYTHONPATH=r6 python3 r6/test_patch07_one_use_lease.py`

Review requirement: independent Claude source/test/security review before integration.
