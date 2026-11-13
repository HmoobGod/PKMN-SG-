# PR26 fresh-session feature negotiation: BaseException poison follow-up

Source-only experimental correction stacked **only** on independently
Claude-approved PR41 exact `e9e5b9f837de47a7555ea1c74860fa998bdd0515`.
Original PR41, PR26 and approved public PR42 and all prior exact heads
remain unchanged. The existing PR43/44/45 pending-review heads also stay
untouched. This source change requires a NEW independent exact-head
source/test/security review before any promotion.

## Defect addressed

PR41's opt-in negotiation already poisons an instance after an Exception,
but `KeyboardInterrupt` and `SystemExit` inherit BaseException rather
than Exception. Either could occur after a partial qSupported write or
ACK before a validated reply. Previously the finally block cleared the
temporary negotiating flag without poisoning the RSP session, leaving
later commands potentially available even when framing was uncertain.

The opt-in-only negotiation method now catches BaseException, marks the
RSP instance irrecoverably poisoned, clears the temporary flag, and
re-raises. The ordinary initial freshness check executes **before**
the try, so declining a late negotiation after harmless earlier read
does not poison a session when no qSupported bytes were sent.

## Narrow tests

- KeyboardInterrupt between qSupported ACK and reply poisons forever;
  no further `?`, `g` or negotiation is transmitted.
- KeyboardInterrupt and SystemExit during a partial wire send poison
  and prevent later packets on the same instance.
- Late opt-in after a prior legitimate read fails without poisoning;
  no negotiation traffic is sent.
- Existing malformed one-nibble checksum trailer is rejected by the
  original exact two-hex-digit receive parser; the receiver itself
  remains byte-unchanged.

The original **private `run_capture`, generic resume, parse_stop, ROM
and save SHA gates, private read windows, one-use player0 PP controls,
and gameplay code are byte-unchanged**. No private path or original game
code is executed in CI. Source-only test evidence, not actual-game
native acceptance.

## Acceptance limits

No private ROM/save staging, no release, merge, NPC-partner AI changes,
automatic item or capture use, or uncertified doubles. PR44/45 already
use a separate one-use generated-only strict post-resume adapter and
must retain their own independent review; this PR is not combined
approval or evidence of their integration.

Formal original-game native acceptance 0/20 (0%), production 0%,
historical unmatched PP 0/2.
