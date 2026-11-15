# Public original actor0 joint witness: Thumb STMIA same-step callback pair

The PR92 joint triage only admitted two DISTINCT original CPU steps with
one Thumb STR for each full32 callback writer. In PR82 source work the
real original CPU witness schema already supports a Thumb STMIA base
plus register-list multiword store, where ONE original instruction may
change Main.callback1 and Main.callback2 at the SAME CPU step, producing
two poststep watcher rows. PR92 would reject even this syntactically
plausible candidate without distinguishing a gap in instrument coverage
from a real gameplay failure.

This isolated PR94 adds a separately named pure Python Thumb STMIA
word decoder equivalent to the public PR82 source-only decoder:
only Thumb-1 STMIA, nonempty register list, base not in list,
aligned effective addresses, no overflow, source register value
matching 32-bit callback watcher. PR92's existing STR candidates are
unchanged. For callbacks observed on distinct CPU steps, accept a
witnessed full-word STR or STMIA candidate at each step; for callbacks
sharing one CPU step require BOTH words be witnessed from one STMIA,
same captured original PC/opcode/low-register PRE snapshot and
consistent full poststep context, as enforced by inherited strict
original CPU auditor. The actor0 -> PP -> guessed result ->
Main.inBattle clear ordering remains strict BEFORE callback write(s).

The two accepted callbacks remain candidates, not confirmation that
the original callback function executed or the game returned to the
overworld. The guessed EWRAM result byte is NOT authenticated as
gBattleOutcome. This change does NOT classify missing PP, certify
original move/target legality or engine one-use request, or authorize
native gameplay. Nonmatches remain unverified, not failed gameplay.

All tests are public synthetic CPU rows and decoder mutations. No
original private ROM/save/savestate, modified game, emulator or CPU
trace staged/read/hashed/executed; no enemy/NPC AI, auto items/capture,
manual fallback, protected main/source-first or approved SHA changed.
Host Python Source CI only; public GNU ARM not applicable.
Draft/unmerged, independent Claude review needed.
Formal native 0/20, production 0%, historic PP 0/2.
