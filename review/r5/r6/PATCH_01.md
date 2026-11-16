# R6 patch 01 — Player0 request snapshot and byte-accurate epoch continuity

Status: local independent source-only draft; no game integration, no native acceptance.

Only an adapter-derived immutable byte snapshot may grant a source-only candidate; no engine ownership certified.

Test: `PYTHONPATH=r6 python3 r6/test_patch01_request_snapshot.py`

Review requirement: independent Claude source/test/security review before integration.
