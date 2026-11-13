# Public generated GBA: first bounded authentic Thumb breakpoint-HIT lab

NEW isolated DRAFT stacked on the exact independently Claude source-approved
PR #35 head 7db58590cd3f93511334a833a26f52bbe3fc917c. This patch is
NOT approved by earlier reviews and does NOT authorize a private game run.
Protected Current ROM/save, main, source-first and approved prior PR SHA
heads remain untouched. NO commercial-game content or save is read,
mounted, copied, printed, uploaded or used as an emulator input.

## What changes relative to the prior Z0/z0 ACK tests?

The generated public 32-KiB original synthetic GBA ROM contains:
- ARM LDR r0,[pc,#0] at 0x080000c0 and BX r0 at 0x080000c4.
- Thumb state literal 0x08000101 at 0x080000c8.
- Original Thumb B . opcode 0xe7fe (memory bytes fee7) at 0x08000100.

Only after verifying Docker --network none on the host and a guest
only-lo interface with both IPv4/IPv6 no-egress guards, the fixture
launches actual mGBA 0.10.5 Ubuntu package on the ORIGINAL generated
ROM. It checks ? and g stop/register grammar using byte-identical
PR26 parser functions and reads expected generated ARM and Thumb
memory bytes. It then sends exactly Z0,08000100,2, one **single "c"**
without an arbitrary address, and expects a bounded reply reporting
SIGTRAP/05 (S05 or T05). It requires a register r15/PC at generated
0x08000100, 0x08000102 or 0x08000104. If it cannot attest that
generated target stop + PC, the lab reports FAILURE, not evidence.

After a trustworthy stop, it performs one bounded z0 cleanup. After
an ambiguous stop or timeout, it sends NO further run-control or
breakpoint manipulation to the running guest; the entire disposable
mGBA process must be terminated and awaited. Socket timeouts are 3s
on the stop; an outer process timeout is 50s with a 3s kill grace.
Never retry c; no s, Ctrl-C, arbitrary addresses, game-engine writes,
input injection or emulator-save mutation.

This is the FIRST isolated synthetic fixture where a c packet can run.
PR26/30/31/32/33/34/35 reviewed heads explicitly did NOT authorize c:
their code and evidence remain unchanged. The new head MUST get fresh
independent SOURCE/TEST/SECURITY scrutiny. A real synthetic breakpoint
hit is meaningful as debugger protocol evidence, but does NOT prove
the modified commercial SoulGold ROM behavior or owner player0.

## If it fails

The generated header deliberately omits Nintendo's proprietary logo.
Therefore an authentic mGBA boot may fail before the synthetic target
is reached. This is an acceptable documented FAIL, not permission to
insert a copyrighted game header or claim fake stop evidence. Any such
diagnostic requires a separate reviewed technical follow-up. No new
private file inputs or ROM options will be added.

## Native gating

No original modified commercial ROM/save, no native player-owned
engine request, no legal automatic slot/target, PP/cancellation, game
terminal, overworld, next unattended wild encounter or manual fallback.
Formal native acceptance 0/20 (0%), production Smart Auto-Battle 0%,
historic unmatched PP submissions 0/2 classified. Main, player-only
safety, no auto in-battle items/capture, enemy/NPC partner AI and
uncertified doubles restrictions remain protected.
