# PR26 real-socket generated-ROM pre-c and post-z0 sentinels

A new independent **DRAFT** source follow-up on PR45 exact
`f19db0d2c652a316a5ef4962fd1b0d6b87e6ef55`, preserving
that pending-review head, approved PR42 and all prior approved heads.

## Concrete evidence being hardened

GitHub Actions on PR45's exact Ubuntu `mgba-sdl` package
`0.10.5+dfsg-3build1` observed a disposable **noncommercial 32KiB**
generated Thumb ROM with initial debugger stop `S02`, initial
register `r15=0x00000000`, a generated ARM entry word `00009fe5`
at `0x080000C0`, Thumb loop word `fee7` at `0x08000100`,
and after a canonical single `T05hwbreak:;` PC `0x08000100`,
a removed `z0` and final read-only stop `S02`.

The initial `r15=0` is **a source-backed observed mGBA startup
sentinel**, NOT evidence that the commercial SoulGold entry CPU has
executed or that the initial PC must be zero in any other emulator.

## New fail-closed gates

- `read_verified_generated_preflight` performs only the exact
  original PR26 RSP `?` and `g` and two fixed generated-ROM
  read commands, then requires `S02`, `r15=0`, and exact ARM/Thumb
  instruction bytes **before** the generated-only `Z0` installation.
- Unit tests submit `S05`, unexpected `T05`, PC at 0x080000C0,
  bool-PC, altered ARM/Thumb bytes and wrong types; all fail without
  any generated `Z0`, `c` or `s`.
- After the one accepted generated T05, the existing z0 cleanup is
  followed by a read-only `?`; `validate_generated_post_cleanup`
  requires the exact observed `S02`. Other statuses fail closed.
- This PR does not change the PR26 original parser, private
  `run_capture()`, owner file identity checks or the PR44 exact
  one-use post-resume adapter. Real hosted network-none mGBA CI is
  mandatory to confirm the new checks on the same generated ROM.

These are conservative source/test requirements tied to this exact
Ubuntu package and fixture; a changed emulator version must undergo
new independent review. The real game's pre-resume PC/battle state is
**unknown and must be separately learned** from an authorized
owner-local private copy. Do not port the sentinel `r15=0` into the
real game controller.

## Limits

No game ROM/save/savestate staged, installed, run, copied into the public
container, modified or released; no production Smart AI changes, no
enemy/NPC partner AI, no auto items/capture, no uncertified doubles.
Actual-game native 0/20 (0%), production 0%, PP unmatched 0/2.
