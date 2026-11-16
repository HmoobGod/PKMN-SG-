# R7 source-to-engine compatibility map and unproven native gates

Source context inspected locally from the **user-supplied** `soulgold-master.zip`
`src/battle_controller_player.c`. Only symbolic references and line locations
are documented here; the private uploaded ROM is NEVER included. The source
archive is **not** a linked ELF/map for the exact ROM, so these are *candidate
source seams* rather than certified address equivalences.

1. `sPlayerBufferCommands` dispatch (source approx. lines 137–159); commands
   `CONTROLLER_CHOOSEACTION` (17) and `CONTROLLER_CHOOSEMOVE` (19) dispatch to
   `PlayerHandleChooseAction` and `PlayerHandleChooseMove` in public source.
2. `PlayerBufferRunCommand` (approx. line 220) owns the original command dispatch.
   The future R7 hook must obtain an engine-created request without inventing a
   second command or borrowing an opponent/partner request.
3. `PlayerHandleChooseAction` (approx. line 2194) builds the action menu and the
   controller ultimately uses `HandleInputChooseAction`. This is the possible
   source-level manual path, **not** a working entrypoint in the uploaded auto ROM.
4. `PlayerHandleChooseMove` (approx. line 2292) reads the original
   `ChooseMoveStruct` from `bufferA[battler][4]`, initializes the move menu and
   later uses `HandleInputChooseMove`. The complete original header and move/PP
   menu payload must be bound to the same request epoch.
5. `HandleInputChooseAction` (approx. lines 389–409) can emit Fight, Item,
   Switch and Run on **actual human input**. The adapter must not alter the
   user's normal manual choices; the automatic proposer is limited to Fight.
6. `HandleInputChooseTarget` (approx. line 501) accepts a selected target on
   actual human A input and emits `B_ACTION_EXEC_SCRIPT`. The auto proposer
   requires independently verified **original** target legality, not guessed
   target indices or an inferred cursor. Its action is only the proposal.
7. The earlier private runtime checkpoint observed original-ROM action/move
   response and PP byte-store candidates. Their addresses are kept in the
   private checkpoint, not declared as an exact source link here.

## R7 R2 source-only payload layout assumption

Original source `BtlController_EmitChooseMove` writes the four controller header
bytes followed by `ChooseMoveStruct`. The proposed 16-byte minimum is the
header plus four 16-bit move IDs and four 8-bit `currentPp` fields. The adapter
now cross-checks payload bytes 4–11 and 12–15 against the independent move and
PP fields supplied by the host, before using those fields for move selection.
The exact uploaded ROM's compiled enum/structure ABI is **not certified** by
this public source-level correlation. Missing or disagreeing bytes fail closed.
The returned `manual_defer_requested` still does not open any native menu.

## Remaining exact integration requirements

- **Engine-owned request**: hook the original controller only when the engine
  actually dispatches player-owned battler 0, wild single, no NPC partner;
  prove request ID/epoch, buffer payload and one-use consumption from native
  CPU state. R7 callbacks do not establish such provenance.
- **Dynamic legality**: original limitations, move choice restrictions,
  Encore/Choice/Disable/Imprison/PP and target-check functions must run and
  be verified *in the current turn*, including side-effect-free continuity.
  Status-move ineffectiveness (e.g., repeated Taunt) needs the actual target
  state, not a heuristic that two slot-3 writes imply redundancy.
- **No forced switch**: the uploaded original ROM has a separate automatic
  Switch path. An isolated patched *test copy* must prevent that branch in
  auto mode without preventing legitimate human/manual switching or enemy AI.
  The R7 library is not installed and cannot protect the current ROM.
- **Actual manual fallback**: map original menu initialization/callback state
  against the exact ROM, request manual control on genuine ineligibility,
  visually confirm the original menu, supply a deliberate **human** input,
  and observe original controller completion. A `DEFER` result alone is not
  native fallback and a fake event log is not proof of controllability.
- **PP execution and cancellation**: join the exact original actor0 Fight and
  Move request/response, actual selected move/target, original byte-store CPU
  writer and before/after PP, then confirm battle outcome/return. Require
  exactly one attributable PP event or a proven original cancellation path.
  The approved R6 PP model stays a candidate verifier, never certification.
- **Build identity**: obtain exact-ROM-compatible linker map/symbols or a
  validated reversible translation and inspect the changed bytes of a
  disposable-only patch. Do not claim that addresses from a separate build
  are the target game's addresses.
- **Independence**: combined source changes require fresh exact-head Claude
  source/test/security review and native gameplay certification remains 0/20.

**No private game-data uploads, no original-file edits, no merges, no releases.**
