# Public host-C behavioral test for actual PR51 player0 proposal code

This isolated source-only DRAFT follows independently Claude-approved
PR51 exact `85d262f05385cce2cb9b0fabc5a3db573e58459b`.
Neither PR51 nor its pending-review parent PR48 R4 is changed.

PR51 Claude A3 observed the old Python behavioral surrogate was
trivial, whereas Claude's independent review had actually compiled
the C `SourceFirstWildSingleMove` against host stubs and injected
candidate-helper mutation. This draft adds a reproducible version of
that behavioral source check to the public CI.

`tools/test_wild_single_pre_target_pool_host.py` extracts the
unaltered live C function added by the actual player-controller
source patch, compiles it with strict host-C flags and minimal
read-only player-owned mocks, and tests 19 deterministic cases:
2 legal baseline outcomes, 16 distinct move/PP mutations across
each of four player-owned slots with the first candidate eligible or
skipped, and one invalid original command fallback. The helper
mutates state at the first candidate target check. Any mutation must
reject with FALSE, leave reply unchanged and never inspect another
candidate. Source CI and the separate pinned public disposable
GNU ARM workflow both run this host C test before source claims.

The harness does NOT model all game engine side effects, verify the
second-stage ChooseMove engine lease, reproduce commercial game CPU
execution, prove actual dynamic legality, or certify native gameplay.
It never reads/executed private ROM/save, never calls external tools,
and does not change game patch or target source semantics.

Parent PR51 source/security approval does not transfer to this
new head; require its own exact-head Source CI, public compiler and
independent Claude source/test/security review. DRAFT/unmerged.
Actual native 0/20 (0%), production 0%, PP unmatched 0/2.
