# Public hosted mGBA 0.10.5 compatibility gate (NO private game)

New isolated DRAFT stacked on independently source-approved PR #34 exact
409c71f89075b56b4cf0801c657842fbf7f95422. This new head needs
its own independent SOURCE/TEST/SECURITY review. No earlier approved
PR branch, main, canonical source-first, or protected game files edited.

## Public-only comparison

Prior approved exact PR34 Ubuntu 24.04 Docker image installed packaged
mGBA 0.10.2+dfsg-1.1build3; actual hosted real GDB/ARM and Thumb-size-2
synthetic handshakes passed (53/53 public unit tests; jobs 43481767435
and 43481767163). This isolated new patch changes the generated-only
container base to ubuntu:26.04 (whose mgba-sdl package is expected to
be 0.10.5). Runtime **fails closed** unless dpkg's reported package
version contains "0.10.5", then prints the actual frontend --version
and binary SHA256 to the GitHub Actions log. The image ID is printed
but upstream Ubuntu base and apt contents remain floating (not pinned).
The source and official build are DIFFERENT package revisions; this is
a same-test comparison, not proof of byte-identical executable builds.

The container remains ephemeral, capabilities dropped, non-root UID/GID
65534, resource-bounded, read-only root, tmpfs, Docker --network none
verified by the host. Inside, network inspection requires only lo and
both IPv4/IPv6 procfs listener tables; successful or inconclusive egress
fails closed. A separate intentionally bridge-networked container must
be rejected by the interface gate **without starting an emulator**.

Two *different original synthetic* ROM sessions exercise the same
approved protocol code as PR34:
1) Original generated 32KiB ROM -> real ?/g/m, exact original PR26
   parse_stop and parse_registers, generated memory mapping, ARM-size-4
   Z0 and z0 ACK and post-removal read-only ? grammar.
2) Original generated 32KiB ROM containing ARM LDR/BX and Thumb "B ."
   halfword at synthetic 0x08000100 -> read m08000100,2 == fee7,
   size-2 Z0,08000100,2 and matching z0 removal, PR26 parser checks,
   and post-cleanup read-only ? grammar.

Unit tests additionally independently pin literal ARM LDR and BX bytes,
not merely comparing the generated image to constants under test, and
verify the emulator subprocess receives only PATH, DISPLAY, XAUTHORITY,
HOME and SDL_AUDIODRIVER. A sentinel secret-like environment variable
must not reach the subprocess.

## Strict non-claims

This test has no actual commercial SoulGold ROM/save, savestate or CPU
game trace. It does NOT execute the Thumb opcode (no c/s), demonstrate
a breakpoint HIT or game input, establish the modified ROM identity,
run the full protected PR26 probe, test original player-owned request,
legal auto move, PP/cancellation, overworld, terminal or manual fallback.
No private staging or transfer is implemented or authorized, no merges
or releases. Formal native Smart Auto Battle acceptance remains 0/20
(0%), production 0%, original two unresolved PP submissions 0/2.
