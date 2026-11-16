# R6 patch 10 — Reject ROM/save/traces and unsafe paths before source-only packaging

Status: local independent source-only draft; no game integration, no native acceptance.

Blocks common private game artifacts and archive path attacks; does not prove absence of pasted secrets inside source code. Review required.

Test: `PYTHONPATH=r6 python3 r6/test_patch10_private_artifact_boundary.py`

Review requirement: independent Claude source/test/security review before integration.
