# Public synthetic mGBA Z0/z0 handshake — draft research

Separate stacked draft on the unchanged Claude-approved PR30 exact head
6a6252c263d1998ba41a3430d68cc9adfb8b25f5. Independent source review
required for this patch; approval of PR30 does not authorize it.

The generated 32 KiB noncommercial GBA fixture is the *only* input. A real
Ubuntu-hosted mGBA 0.10.2 debugger must first return correctly validated
?, g and m replies. The tool then sends exactly Z0,080000c0,4 to install
and z0,080000c0,4 to remove one *ARM-width* breakpoint at the known fixture
loop address, demanding a checksum-correct OK for each. No c, s, Ctrl-C,
host battle input, reset, guest memory writes, watchpoints or ROM patches.

The diagnostic marks Z0 as **attempted before sending it**, so even a malformed,
missing, or timed-out install reply triggers **one bounded z0 cleanup attempt**
before exit. Failed removal is reported explicitly and is never classified as
success. Full roundtrip tests assert the order of real read-only preflight,
Z0, z0, plus no Z0 on invalid read-only replies; a scripted socket stub verifies
cleanup after a lost/corrupt install ACK. No successful cleanup is assumed from
an exception alone.

A successful install/remove handshake does NOT prove a breakpoint can be
hit or establish the T05/S05 stop grammar after execution. PR26's original
Thumb breakpoint uses size 2, not this fixture's ARM size 4; no approval
carries over. The actual GDB listener can bind to 0.0.0.0. NEVER reuse
the public script or public hosted runner for a private game ROM or save.
Future private sessions require verified network isolation and separate
review. Do not include copyrighted ROM or save bytes in GitHub.

All existing protected files, main, source-first, enemy/NPC AI, no auto
items/capture, uncertified doubles and manual fallback are unchanged.
Formal native acceptance 0/20, production gameplay 0%.
