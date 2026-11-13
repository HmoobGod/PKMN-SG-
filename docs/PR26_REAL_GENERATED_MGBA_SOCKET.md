# PR26 receiver: real mGBA, generated Thumb ROM, isolated CI ONLY

This independent **draft** is stacked on the unmerged experimental PR44
head `70a152a237f19d6b67a14295e42652e40c08dee1`, itself based
on approved source-only PR41. PR26, approved PR41/PR42, and awaiting
Claude-review PR43 are unchanged. All heads remain DRAFT/unmerged.

## Concrete question

Will **PR26's actual original `RSP._transmit()/receive()` implementation**
and PR41's opt-in qSupported source extension communicate correctly with
Ubuntu mGBA 0.10.5 on a genuine loopback TCP socket, then will PR44's
one-use adapter strictly accept the observed canonical `T05hwbreak:;`
and corroborate r15 at the known Thumb-loop PC?

Prior PR42 real generated-ROM mGBA evidence used a separate public
receiver, while PR44's new tests use PR26 receiver but a fake OS socket.
This draft closes that *specific* interface gap, not the original game's
unverified CPU/gameplay evidence.

## Explicit source-only container and hard safety boundaries

The workflow builds a NEW, separate throwaway Ubuntu 26.04 container
from exactly seven source files: six explicitly named public GitHub
Python files and the new Dockerfile. It copies **no .gba, .sav, savestate,
original commercial game file, owner transcript or secret**. One of
the Python sources is the publicly versioned PR26 capture module, but
its private `run_capture()` and CLI are NEVER invoked. It is imported
only for its RSP class and read-only register/stop helpers.

The emulator ROM is generated inside a disposable tmpfs at runtime from
fixed bytes, with 32KiB length and an independently hardcoded SHA-256
`cfa20bc9ccad2131abeedaed0d1d5aa49425f8bce5616370d0b6659c7cd4804b`.
It is the same synthetic instruction sequence as the PR37/PR42 labs.
The runner accepts NO external CLI arguments or arbitrary ROM path,
and denies the `SOULGOLD_ALLOW_PRIVATE_INPUTS` flag.

The host verifies Docker `--network none` before start, and the
isolated runner checks only-loopback/failed egress both before launch
and after connecting to mGBA. Host deliberately tests bridge-network
rejection without starting an emulator. The container is rootless,
read-only, `cap-drop ALL`, no-new-privileges, bounded memory/PIDs/tmpfs,
and gets no secrets, private artifacts or cache.

## Bounded proof protocol

1. Exact Ubuntu package gate runs before any unit or emulator work.
2. The original PR26 RSP performs exact qSupported opt-in, RSP ? and g.
3. A separate *generated-ROM-only* sender permits only two exact m
   reads and synthetic Thumb `Z0,08000100,2` / `z0,08000100,2`.
   This helper does not extend the private PR26 command whitelist.
4. The PR44 adapter sends exactly one c, requires byte-exact
   `T05hwbreak:;`, uses PR26 actual receiver and poststop g,
   accepts only generated-target PCs. On uncertain replies/PC/ACK it
   poisons RSP and requires disposal of the entire test emulator.
5. Cleanup is attempted ONLY after a verified canonical stop and PC.
   All other failures terminate/await disposable mGBA without in-band
   guesses.

## Acceptance limitations

PASS would show only real mGBA 0.10.5 generated-ROM **wire
compatibility** for PR26's RSP receiver and a disposable strict stop,
NOT any original SoulGold CPU, automatic player0 move, runtime legality,
request ownership, PP cancellation, outcome, overworld transition,
manual fallback or private-game capture.

PR26's protected private ROM/save hash checks, original PC and memory
allowlists, default capture path, game features, enemy/NPC AI, no auto
items/capture, uncertified doubles and all approved branches remain
untouched. Future private testing requires a separate user-authorized
private-copy plan and independent source approval.

Formal original-game acceptance 0/20 (0%), production 0%, historical
PP unmatched 0/2.
