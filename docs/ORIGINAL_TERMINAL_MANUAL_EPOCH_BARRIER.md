# Public original result/overworld research: pre-clear and same-step barriers

## Proven evidence gap in PR87
The public-only original result -> Main.inBattle clear -> callback1 ->
callback2 ordering research previously kept a result candidate alive
across a *prior* manual-menu marker (kind8) because it only cancelled
when an active post-Main-clear sequence existed. It also counted one
plausible outcome STRB as a sufficient prior result even if a second
unattributed watcher transition changed the same candidate outcome byte.

The original C observer reports marker records before execution and
watchers after the SAME CPU step; JSON row order cannot grant auto
ownership when a manual marker shares that step with a result watcher.

## Isolated conservative correction
- Run the inherited strict original CPU event verifier FIRST.
- Build a set of witnessed manual-menu CPU steps. A manual step closes
  all previous result candidates and active field-return sequences.
  Candidate-result and callback watchers on the same CPU step are
  denied regardless of JSON row ordering.
- Require exactly ONE watched outcome-byte change before the observed
  inBattle clear, and the SAME event must be a Thumb STRB source/address
  matching writer candidate. Any second result-byte transition, even
  an unsupported or unwitnessed instruction, makes the sequence ambiguous.
- A new outcome-byte transition during post-clear callback routing
  invalidates the old field-return hypothesis.
- Do not interpret a synthetic ordered candidate as authenticated
  original gBattleOutcome, native terminal, overworld callback execution,
  a one-use actor0 request or valid production behavior.

This is hosted Python source-only evidence (no GNU ARM compile needed);
all fixture data are generated public fake CPU rows and must preserve
same-step PC/opcode/register consistency. Original Current ROM/save/
savestate, private original trace, modified game and emulator remain
untouched. Protected main/source-first and reviewed PR heads unchanged,
no merges or enemy/NPC AI, auto-items/capture, manual fallback edits.
Native gameplay 0/20, production 0%, PP missing causes 0/2.
