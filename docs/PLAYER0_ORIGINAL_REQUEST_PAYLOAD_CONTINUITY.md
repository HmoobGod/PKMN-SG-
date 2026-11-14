# Public Source LAB: engine request payload continuity before reply

The inherited player-only disposable upstream Source LAB checks the
original CONTROLLER_CHOOSEACTION or CONTROLLER_CHOOSEMOVE command byte
and selected move. However a modded target helper could change
additional original request header bytes or a *different* move menu
slot while preserving the command byte and proposed slot; the guard
would accept a newly mutated request as the old proposal. That is
a concrete stale-command evidence gap, not proof of a live exploit.

This isolated public patch captures the four original ChooseAction
header bytes, original request buffer identity, all ChooseMove
moves[] and currentPp[] for MAX_MON_MOVES before any original move
limitation or targeting helper. Re-check all captured fields after
target helpers and BEFORE skipping any ineligible candidate or
emitting Fight/Move. A changed value => no automatic controller
reply, preserving the original manual input path. Does not modify
original request buffers; reading player-owned state only.

New Source CI static mutation controls and public synthetic fake
state tests enforce before-target capture, after-helper checks and
no response on stale buffers. Pinned PUBLIC upstream GNU ARM LAB
must apply this patch and compile on a disposable checkout to
verify C syntax, original source version and patch scope. The
result is source-only acceptance, NOT actual modified-ROM or
original-game request ownership, dynamic legality, PP debit or
native gameplay certification.

No Current original ROM/save/savestate, private emulator, original
CPU trace, enemy or NPC partner AI, auto items/capture, approved
head or protected main/source-first changed. DRAFT and unmerged;
new independent Claude exact-head review required. Native 0/20,
production 0%, historical two PP causes 0/2.
