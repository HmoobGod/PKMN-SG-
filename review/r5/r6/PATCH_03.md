# R6 patch 03 — Require consecutive authenticated slot-3 CPU writes in the same battle epoch

Status: local independent source-only draft; no game integration, no native acceptance.

Must run inherited exact-ROM private cursor auditor before this reducer; cannot certify move failure or actual Taunt status.

Test: `PYTHONPATH=r6 python3 r6/test_patch03_slot3_repeat.py`

Review requirement: independent Claude source/test/security review before integration.

## R2 schema bridge
The R6 normalized `slot_cpu_store/frame/battle_epoch` rows do not match R5's
raw `cursor_store/f` schema. `from_r5_authenticated_cursor_trace` accepts the
R5 source-audited report AND its matching raw rows, checks writer PC/count/slot
continuity, and converts only original CPU slot stores. It does **not** certify
provenance independently; a caller must attest the R5 audit on identical rows.
