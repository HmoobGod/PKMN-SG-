# mGBA 0.10.5 source-backed GDB `S05k` investigation and generated-only handshake

This source-first audit DOES NOT stage, read, copy or run any commercial ROM, SAV or
savestate. PR36 exact package gate and independently approved PR37 R2 stay untouched.
This isolated draft is stacked directly on PR37 R2 (92cc0266b286dfec0143c84687ad0659b53f91b4)
and is SOURCE/TEST/SECURITY ONLY until independently reviewed.

## Exact upstream source

Upstream tag: https://github.com/mgba-emu/mgba/tree/0.10.5
Source file: https://github.com/mgba-emu/mgba/blob/0.10.5/src/debugger/gdb-stub.c
Source Git blob SHA: 0e3b1538cbb35f4471b36ce324c1a4d2fd32956a

- Lines 67–78: mGBA's _gdbStubEntered for DEBUGGER_ENTER_BREAKPOINT uses
  `T%02x%cwbreak:;` if supportsHwbreak AND supportsSwbreak AND info; otherwise
  it literally formats `S%02xk`. With SIGTRAP=5 this produces the
  exact observed `S05k`. It is **authentic mGBA output**, not a standard
  accepted GDB `S05` stop reply. This explains the extra k at the source level.
- Lines 440–467: _processQSupportedCommand starts with both supports flags
  set false, then recognizes literal `swbreak+` and `hwbreak+` in the
  client's qSupported request. The response advertises both features.
- Lines 573–613: the Z0/Z1 breakpoint path uses BREAKPOINT_HARDWARE for the
  debugger platform. When the feature flags are both advertised and breakpoint
  info is present, the source predicts `T05hwbreak:;`.

## Narrow experiment and decision boundary

The NEW public-only probe sends exactly `qSupported:swbreak+;hwbreak+` as one
read-only capability negotiation command, and requires the exact source-advertised
feature response *before* `? / g / m`, generated-byte validations,
`Z0,08000100,2`, one `c`, a canonical byte-exact `T05hwbreak:;`
stop and r15 PC within the same generated-only allowlist, then one `z0`
cleanup. If negotiation, stop bytes, PC or anything else differs, fail closed
and terminate/await disposable mGBA rather than interpreting malformed frames.

The previously approved original public `S05k` diagnostic is unchanged and
still runs separately, with its own mGBA process. The original strict PR26
parse_stop implementation remains untouched, still rejects `S05k`, and
accepts `T05hwbreak:;` according to pure tests. Do NOT update or invoke
private PR26 probe negotiation as part of this draft.

The Ubuntu-packaged mGBA 0.10.5 package may differ from the upstream tag.
Therefore upstream source analysis is a strong mechanism explanation, but actual
package behavior requires its own real hosted run and exact-head logs. Do not
claim mGBA spec conformity or actual-game compatibility without evidence.

No real commercial SoulGold CPU, no private game breakpoints, player0 ownership,
automatic legal move/target, PP/cancellation, terminal, fallback or production.
Formal native acceptance 0/20 (0%), production 0%, historical PP 0/2.
No merge, private game staging, release, manual-control changes, auto-items,
capture, enemy/NPC-partner modifications or uncertified doubles.
