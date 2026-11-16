# R6 patch 09 — Require real menu and human input before marking fallback candidate

Status: local independent source-only draft; no game integration, no native acceptance.

An ordinary faint/switch prompt does not demonstrate the ChooseMove manual fallback. Exact UI+human+engine witness remains missing.

Test: `PYTHONPATH=r6 python3 r6/test_patch09_fallback_witness.py`

Review requirement: independent Claude source/test/security review before integration.
