# Capture reasons and diagnostic statuses — 16266

These are two separate return domains. Capture reasons report an observation failure; diagnostic statuses select wrapper behavior. Neither domain grants action authority.

## Capture reasons

| Code | Meaning |
|---|---|
| 0 | Capture succeeded within the sampled scope; no ownership/legality certificate |
| 1 | Actor outside sampled indices0/2 |
| 2 | Battler count does not include actor or exceeds4 |
| 3 | Selection/resource/cache pointer rejected by existing bounds/alignment checks |
| 4 | Null output pointer |
| 5 | Controller kind/completion signature excluded |
| 6 | Unsupported flags/count, noncanonical layout, mismatched controller tables, absent self or malformed restriction-cache byte |
| 7 | Actor pending bit clear or buffer-A request opcode is not19 |

The output is zeroed after a non-null pointer is supplied. Early reasons1/2/5 and the early context/pointer checks return before field assignment. Reasons3/6 can also arise in the later cache checks, after fields were assigned. Code7 currently occurs before those assignments. The caller must use the return code rather than assuming any partially filled fields are valid.

## Diagnostic statuses and wrapper routes

| Status | Cause | Wrapper route |
|---|---|---|
| 0 | Non-eligible diagnostic context after successful work, or second capture specifically returns7 | Original native chain |
| 2 | Any first-capture failure, including7; no allocation | Original native chain |
| 3 | Allocation returned null in a context not initially eligible for manual preview | Original native chain |
| 4 | Eligible recommendation passes all rechecks; existing cursor byte written | Manual chooser; human confirms |
| 5 | Initially eligible but no recommendation, allocation returned null, other second-capture failure, or recheck mismatch | Manual chooser; cursor unchanged |

Result initialization temporarily sets1; it is not a completed return path. The wrapper branches to the assist/manual exit only for4 or5. On every successful allocation the scratch is freed once before a second capture. Null allocation performs no free.

The special second-capture7 split returns0 after cleanup, so a completed/replaced request does not cause the preview to install a manual chooser. Other failed second captures still use5, based on eligibility captured once at the start. The same-call second-capture changes are fault-injection tests, not demonstrated natural events. Returning to the original chain does not certify how native auto behavior handles synthetic inconsistent inputs.
