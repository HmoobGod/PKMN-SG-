# Pokémon SoulGold — source-only original cursor writer R4

**Research draft only. Not an installable ROM patch. Not merged, released, or certified.** Formal original-game Smart Auto-Battle acceptance **0/20**, production **0%**. All private ROM/save, EWRAM snapshots, CPU logs, executable, and screen captures remain outside this package.

## R4 changes over R3

- `sg_frame_probe_cursortrace.c`: **private, exact-binary mGBA-only** read-only observer of CPU memory-store callbacks. Dynamically resolves the live pointer at EWRAM `0x02001E90`, captures the original store that writes `pointer+0x106` (move slot), `pointer+0x10A` (target cursor), and pointer initialization/clear. Preserves execution of the original CPU store exactly once and fails closed if both PP and cursor trace modes are enabled. Source contains no ROM/save or CPU logs.
- `tools/run_private_cursor_probe.py`: a guarded local replay launcher. Requires SHA256 pins for ROM/save/mGBA, creates disposable read-only copies in a fresh private output folder, verifies original and copied bytes after execution, and logs privately. It never starts uploads or uses GitHub. Only use with a compiled private `.so` built from this source for the exact pinned emulator.
- `tools/audit_private_original_cursor_writer.py`: reads local private CPU trace and exact local ROM, verifies `0x08018620` Thumb BL into selector `0x080183F0`, pins slot writer `0x0801862E` / target writer `0x08016FB6`, and independently checks write address/source byte, player slot 0, pointer lifetime, and terminal counters. A store with the same before/after value still counts as an *observed store*, not a *changed selection*.
- `tools/audit_private_player0_switch_emitter.py`: checks the monitored original controller emitter for player0 Fight (0), Move (10), and Switch (2) with distinct LR call-site attribution. No Switch observed in a bounded trace cannot prove the Switch branch unreachable; formal no-forced-switch certification stays false.
- **22 new synthetic-only tests** (11+6+5) are registered in three additional test suites. R3's earlier five suites remain unchanged.

## Reproduce on the private host

Run from this folder:

```bash
for test in tools/test_private*.py; do PYTHONPATH=tools python3 "$test"; done
gcc -std=gnu11 -Wall -Wextra -Werror -fsyntax-only sg_frame_probe_pptrace.c
gcc -std=gnu11 -Wall -Wextra -Werror -fsyntax-only sg_frame_probe_ownertrace.c
gcc -std=gnu11 -Wall -Wextra -Werror -fsyntax-only sg_frame_probe_cursortrace.c
gcc -fPIC -shared -O2 -std=gnu11 -Wall -Wextra -Werror -o /path/to/private/sg_frame_probe_cursortrace.so sg_frame_probe_cursortrace.c -ldl -pthread
python3 tools/run_private_cursor_probe.py --help
python3 tools/audit_private_original_cursor_writer.py --help
python3 tools/audit_private_player0_switch_emitter.py --help
```

The pinning, ABI offsets and CPU buffer pointer layout are specific to one mGBA build. `LD_PRELOAD` must be set **only on the emulator process**, not on a timeout wrapper or unrelated program. A deliberate no-PP/move, invalid target or forced-switch native acceptance scenario is **not** established by these tests.

## R4 conclusions and restrictions

1. Two isolated original-ROM private battles independently reached the original slot writer and target writer; they did **not** establish that the older GitHub Smart Auto code was installed.
2. The slot writer receives its return value from `BL 0x080183F0`; this is a grounded selector-to-writer connection, **not** a full identified planner or proof of move legality.
3. Slot value remained `0` in those observed writer events. An earlier battle's slot-3 snapshots could be repeated selections or persistent cursor reuse; a real slot-3 CPU writer trace is still needed to distinguish them.
4. Two player0 Fight/Move pairs and **no** player0 Switch were observed in each completed trace's monitored emitter window. The original ROM still contains the action-2 branch and the requirement to prevent forced switches is **not** certified.
5. Original manual fallback cannot be certified: the previous RAM-only PP-zero experiment did not reach a controllable manual move UI. Future work should add explicit player0-only fail-closed gating and a fresh native fallback acceptance test, not change enemy/partner behavior.

No private game file, original saved data, emulator executable, or private test log may be committed to public GitHub or uploaded to Google Drive. No merges or releases.


## R5 addendum — new direct selector trace, no forced switches, manual-defer design

- `tools/audit_private_slot3_timeline_r5.py` validates every cursor write through the inherited exact ROM/store audit before counting genuine slot-3 selection writes, changes, and consecutive repetitions. Runtime inputs MUST remain private. No native promotion.
- `source-first/player0_fail_closed_guard.{h,c}` is a **pure C, unintegrated reference gate**: only player-owned wild singles, engine-backed move legality and target checks, fresh request continuity, positive ineffective-move evidence, and no automatic item/switch/capture action. On any ineligibility it requests original manual controller deferral; it does **not** actually activate a manual menu.
- `tests/test_player0_fail_closed_guard.c` exhaustively probes the reference gate with generated inputs. This does not attest original game safety or any executable patch.
- The native slot-3 writer evidence stays private; the package never includes ROM/save, RAM, emulator executable, screenshots, or CPU logs. Main/approved GitHub heads are untouched; no merge, release or production acceptance.
