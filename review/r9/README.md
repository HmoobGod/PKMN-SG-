# R9 — Original-ROM CPU Fight → Move → PP candidate verifier

**Read-only; source/test/security review only.** This verifier consumes three **private**, local, SHA-guarded mGBA observation logs from the user's *existing unmodified* game. It detects one narrowly defined original CPU store sequence and emits only a redacted summary.

## What has actually been run (private only)

- The user-supplied 32 MiB GBA ROM and 128 KiB save were each copied to a disposable private session and verified against both source and copy fingerprints before/after emulation.
- The exact unstripped `mgba-rom-test` embedded in the supplied source archive was fingerprinted and executed for 8,000 frames. The original ROM handled a wild battle.
- In the PP-focused replay, the original player0 emitter wrote action-0 Fight at frame 2892 from original LR `0x08017211` and action-10 Move at 2893 from original LR `0x08065f2d`. The original Thumb PP store at executable PC `0x0809e6ba` (mGBA raw PC `0x0809e6be`) changed a compatible candidate PP byte 20 → 19 at frame 2947, while the separate actor1 emitter was excluded.
- One **UNVERIFIED** source-ROM CPU chain candidate was observed and audited using these actual local logs. No new R7, R8 or R9 game code was executed.
- This replay still had *directional movement* requested during the battle transition. It is NOT an input-free-move acceptance scenario. Shorter-input replays did not reproduce the battle.

## Verification boundaries

The source-only auditor requires complete save/load metadata, original CPU store PC and LR matching, exact player0 action values, original Thumb PP-writer PC, one-byte decrement, ordering, duplicate rejection and opponent exclusion. It explicitly refuses to claim full ownership, dynamic legality, manual fallback, Switch reachability or source-to-ROM ABI certification. Candidate remains `UNVERIFIED`; acceptance stays **0/20**, production **0%**.

Use `PYTHONPATH=review/r9 python3 -m unittest discover -s review/r9 -p 'test_*.py'` for entirely synthetic unit fixtures. **Never** upload, attach or commit real private input logs, original game files, emulator binaries, RAM or screenshots. The Python CLI itself may be reviewed publicly; actual input files stay in the private lab.

## What is still blocked

1. An actual original engine request buffer / authenticated controller callback and matching exact-ROM ELF/MAP are not yet verified. Scanning memory for the `17` / `19` byte is insufficient; unrelated memory writes produced false positives.
2. The R7 and R8 source-only adapters are **not installed** and their engine legality and ownership are not proven.
3. No real functioning manual UI fallback was demonstrated. The existing automatic Switch branch remains a capability and needs an enforceable player0-only guard.
4. PP correlation is observed, but formal move attribution, the two older unexplained PP cancellation causes, and overworld-return acceptance are not established by this verifier.

PR125 (lifecycle) and R8 PR126–145 have no independently supplied Claude verdict at the R9 checkpoint. Do not merge or treat CI-green as independent approval.
