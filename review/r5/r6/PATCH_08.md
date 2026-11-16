# R6 patch 08 — Strict epoch-level player0 response-to-PP candidate join

Status: local independent source-only draft; no game integration, no native acceptance.

Candidate join only. Requires authenticated event source plus exclusion of relevant missing events; cannot prove causality or actual move legality.

Test: `PYTHONPATH=r6 python3 r6/test_patch08_pp_epoch_attribution.py`

Review requirement: independent Claude source/test/security review before integration.
