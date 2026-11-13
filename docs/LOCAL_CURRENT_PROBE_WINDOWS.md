# SoulGold: local one-step Current-copy RSP handoff (source-only)

**No automatic move here.** This runner performs a verified **probe-only** connection to an **already paused**, **already running** mGBA GDB server on the user's PC. It never uses a host key to pick a battle command, never resumes CPU execution, never sends GDB breakpoints or memory writes, and never touches the protected originals. The underlying observer at PR #28 **must receive its own independent review** before use.

## What is required

- Windows PC with Python 3 and mGBA, already installed by the user. mGBA 0.10.5 CLI has a `-g` / `--gdb` option with default port 2345, but **start the GDB server through your existing mGBA UI**, with a *paused* game. No automated emulator startup is implemented, because debug/pause semantics need real verification.
- **Disposable files** (not renamed or symlinked originals) called `Pokemon_SoulGold_TEST_COPY.gba` and `Pokemon_SoulGold_TEST_COPY.sav`, identical SHA-256 to the protected Current game/save. The launcher refuses any other filenames, sizes, or hashes.
- Exact PR #28 file `tools/capture_original_request_rsp.py` from head `41ab3cdf45e249f321b4cb206a1d843fe5639b57` with SHA256 `7d1e30f8a3a51b586708b37a2e0f5793f835723ad3df935144dc8962d2156d2a`. If that PR is repaired and its head changes, **update and re-review the launcher**: it is SHA-locked.
- This launcher `tools/run_current_copy_probe_local.py` plus these docs; no other ROM source or secret is uploaded to GitHub.

## Local-only procedure

Put your duplicate ROM/save in a new *scratch* folder and the two `tools/` scripts in its `tools` subfolder. In PowerShell in the scratch folder:

```powershell
# First prove file IDs, script IDs, and output safety with zero debugger traffic.
py -3 .\tools\run_current_copy_probe_local.py --observer .\tools\capture_original_request_rsp.py

# Only after independent PR28 + launcher source approval AND after pausing mGBA
# and starting its local GDB server on port 2345:
py -3 .\tools\run_current_copy_probe_local.py --observer .\tools\capture_original_request_rsp.py --run-probe
```

For a double-click workflow, after the independent reviews are complete, keep `Run_SoulGold_Current_Probe.cmd` in the scratch folder alongside the copies and `tools/` scripts, start your paused mGBA server, and double-click the `.cmd`. It runs the same single safe command. It never automatically launches mGBA, because the debugger must already be paused.

The one command intentionally invokes the PR28 code with `--current-copy-probe-only --probe-only --rom <named copy> --save <named copy>` and a random private report path. It never downloads anything. The report stays in `SoulGold_Private_Probe_Reports` on the PC. **Don't put this raw report in public GitHub**. Share privately only after inspecting sensitive contents. Raw wire traffic includes memory bytes and may include game-specific data.

If the GDB server rejects a packet, the underlying observer normally writes a partial private report; the launcher labels it partial, never gameplay success. If no report is created, it labels failure. Windows report file privacy depends on the local account/ACL; no blanket claim of 0600 ACL protection is made. Close the debugger afterwards; the launcher never closes or resets it for you.

## Explicit non-claims

All checks are source-only until the actual PC run. Passing local hash checks does not prove which ROM the emulator loaded, even when the same file is open in its UI. The `?`/`g`/`m` response cannot prove breakpoint handling, automatic legal moves, PP debit, battle outcome, overworld return, or a second wild encounter. The Current ROM copy is not the historical experimental modified ROM. No source/tool approval authorizes merging, installing native hooks, player automatic items/capture, foe/NPC AI control or uncertified doubles.

Formal native acceptance **0/20**, production integration **0%**, historical unmatched PP **0/2** classified. Keep all evidence from each emulator process separate.