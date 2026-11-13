# Source-only C observer negative-context boundary for original joint evidence

This independent DRAFT research follow-up starts directly from Claude
source-approved PR49 exact `fcd708663f85ce198af4913925729fe2d7224c64`
and leaves that approved source/test/security head unchanged.

## What is new

The original `sg_trace_exact_joint_player_terminal` **C observer itself**
now receives adversarial FAKE core conditions through a separate test
translation unit; unlike Python-authored fake event dictionaries, the real
C observer captures the CPU marker fields and PP/Main/callback changes.

- The exact fake actor0 emitter and original writer PC are present,
  but wild battle flags are zero: raw writer context remains flagged zero.
- Same writer PC and byte debit with battler count zero: the C observer
  records `battlers=0`, never silently substitutes the usual two.
- Original `Main.inBattle` initially clear with stale battle flags: raw
  writer context remains clear, and no genuine Main-clear transition
  is invented by the observer.
- Original writer marker reached without a PP byte decrement: no
  original PP mutation event is fabricated, regardless of valid PC.
- Genuine synthetic complete event sequence remains captured, including
  both original callback changes, without promoting the trace to a
  gameplay result.

The standalone workflow compiles this exact public C fixture with
`-std=c11 -Wall -Wextra -Werror -pedantic`, runs it, and rechecks
the existing PR49 Python joint audit, using no commercial game,
save or opcode access. It touches a NEW C unit test, NEW isolated
workflow, and this doc only; no overlap with PR50's synthetic
writer-context verification implementation or its source-check workflow.

## Interpretation

C recording of a writer PC/PP byte is **descriptive**, not an
authenticated actor0 ownership or effective legality proof. The
separate Python verifier must still reject stale Main/wrong flags/
battlers before any original player0 attribution. Historical
two PP-unmatched causes remain unresolved. No new modified-ROM
replay is executed or certified.

Preserve original main/source-first, PR42 and PR49 approved exact
heads, PR48/PR50 pending heads, private ROM/save, no guest writes,
no automated items or capture, no enemy/NPC partner AI changes
and no uncertified doubles.

Formal actual-game acceptance 0/20 (0%), production 0%, PP 0/2.
Require completed exact-head C workflow plus independent Claude
exact-head source/test/security review; keep DRAFT/unmerged.
