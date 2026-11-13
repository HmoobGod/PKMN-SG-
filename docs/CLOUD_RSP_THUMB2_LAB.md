# Public cloud mGBA Thumb-width-2 GDB breakpoint lab — not native gameplay

This is an isolated **new draft** on independently source-approved PR #33
exact head 7e66060ba1f9f37cca54ae3f9f2f7711cdb25708, which is preserved
unchanged along with PR #26 and PR #30–#32. Approval does NOT transfer to
this new head. No merge, private stage, commercial ROM/save or gameplay approval.

## Actual generated test image

The script generates a fresh noncommercial 32-KiB GBA ROM with a zeroed
Nintendo logo. The synthetic ARM startup code branches to 0x080000C0,
where it contains ARM LDR r0,[pc,#0] followed by BX r0, and literal address
0x08000101 (Thumb bit set). At generated ROM address 0x08000100 is
Thumb halfword 0xE7FE (little-endian bytes fee7), an infinite-loop branch.
The script does NOT continue or step the CPU, so it does **not** claim
the guest actually executed these instructions or reached Thumb state.

In a Docker network-none container already verified on host and guest,
it launches actual mGBA -g against ONLY that generated ROM and verifies
?/g/m responses using original PR #26 stop/register parser functions and
PR #30 bounded read framing. It additionally reads exactly
m08000100,2 and checks the returned synthetic Thumb halfword before
sending **Z0,08000100,2** to install and **z0,08000100,2** to remove
one width-2 breakpoint. The fixed allowlists reject c, s, Ctrl-C,
memory/register writes, other addresses/widths, and other breakpoint
classes. An install attempt, even with an ambiguous reply, triggers one
bounded removal attempt; cleanup failures abort. An extra read-only ?
must have PR #26 stop grammar (not stale OK) after removal, but is NOT
a proof of actual breakpoint removal or a breakpoint-hit stop form.

The old PR33 ARM-width-4 session remains in the same real job, separately
executed against the previous generated fixture. Unit tests also pin
the copied original PR26 Git blob SHA:
8c55e8acf9b0da6b7957de4a9c5eb84ecd6b1d78.
Tests cover the no-private-input flag, preflight network gate ordering,
command allowlists and safe cleanup, mocked full-run sequencing, real
RSP framing, and the generated ARM/Thumb bytes.

## Evidence boundary and gating

Passing this lab may certify the **synthetic mGBA 0.10.2 RSP size-2 packet
ACK/NAK path only**, not the original PR #26 breakpoint on an exact
modified ROM. mGBA 0.10.5, a real breakpoint **hit**, exact modified-ROM
loaded identity/save compatibility, the engine-owned player0 request,
legal automatic move, PP/cancellation, terminal and manual fallback remain
unverified. The GDB listener may bind all interfaces (0.0.0.0); the
host verifies Docker network mode none, the guest checks only-lo,
IPv4/IPv6 procfs, outbound failures, and a separate bridge-network
negative test blocks an unisolated container before emulator creation.

No private game files, savestates, binary traces, emulator secrets or raw
private memory are read, mounted, printed, staged or uploaded. Actual user
ROM/save private transfer requires a new owner-authorized reviewed design.
No merges/releases. Formal native acceptance 0/20 (0%), production 0%,
two historical unmatched PP cases still 0/2 classified.
