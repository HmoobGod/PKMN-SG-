# SoulGold: cloud mGBA GDB/RSP staging boundary (source-only research)

Status: **UNVERIFIED UNTIL EXACT-HEAD GITHUB ACTIONS COMPLETES**.
This isolated draft does not merge any previous SoulGold branch or touch any real game.
Its first job is answering one question: can a real **GitHub-hosted Ubuntu runner**
start packaged mGBA with a GDB remote stub and answer read-only RSP packets?

## Stage A — public, non-private compatibility check

- Pull-request-only isolated workflow at .github/workflows/cloud-mgba-rsp-fixture.yml.
- Installs Ubuntu 24.04 mgba-sdl + xvfb + xauth at runner execution time.
- Generates **original** 32 KiB test image in a temporary runner directory;
  the GBA header licensed-logo region is left empty. No proprietary ROM data.
- Starts **actual** mGBA SDL with -g on a temporary Xvfb display.
- Connects via 127.0.0.1:2345 and allows ONLY ?, g and m080000c0,4.
- Validates response checksum, paused stop, bounded register grammar, exact
  generated fixture's mapped ARM infinite-loop instruction.
- The synthetic fixture has no real Pokémon logic: passing it validates the
  hosted emulator+RSP transport, **not** actual game startup, ROM identity,
  loaded battery save, any player-owned move or native acceptance.
- No ROM/save, savestate, private trace or debugger bytes in workflow logs,
  uploaded artifacts or repository history. No secrets, GITHUB_TOKEN write
  permissions, checkout of a PR from an untrusted fork with private access.
- Source unit tests cover allowlist, framing/checksums and denial conditions;
  unit-test PASS alone must never substitute for the real hosted emulator job.
- If the packaged SDL build has no GDB stub, exits, or fails to return
  correct RSP values, FAIL CI and read logs; do not claim compatibility.

## Stage B — PROPOSAL ONLY, NOT IMPLEMENTED: private exact-game staging

Do not upload the original 32 MiB ROM, 128 KiB .sav, savestate, developer
traces or any memory dump to this **public** GitHub repository, its PRs,
logs, issues, Actions artifacts, cache, comments or source ZIPs.

After Stage A genuinely passes, create a separately access-controlled
**private** staging workspace/repository, requiring owner opt-in. Keep its
workflows and data private, with no fork/PR triggers and no third-party
Actions whose supply chain is not reviewed; the owner may stage an authorized
disposable file copy from the phone. Do not blindly treat ordinary GitHub
encryption-at-rest as end-to-end secrecy or place ROM bytes in git history.
Prefer a bounded private encrypted transfer mechanism and ephemeral runner
files, with audit/retention/deletion controls explained before enabling it.
Do not copy protected files automatically merely because they are available
in this chat or Google Drive.

Security gate before ANY private run:
1. Independent Claude reviews of exact heads for PR #26 (approved source
   only), #28 stacked extension, #29 adapter and optionally #27. Reconfirm
   SHAs; approval for one head does not transfer to any other head.
2. Owner verifies consent and separately authorizes the chosen private
   staging mechanism; secret and data scope strictly limited to that runner.
3. Runner disables shell tracing, excludes private raw output from public
   CI, uses exact SHA256 and lengths of disposable ROM/save, rejects
   symlinks/aliasing, and rehashes originals after testing. Avoid raw memory
   in any logs or artifact; private report must require explicit review.
4. First REAL game GDB step limited to ?, g and approved m read,
   no c/s, breakpoint/watchpoint, guest memory write, host battle inputs,
   items/capture or doubles.
5. Document actual loaded-image parity and true RSP stop/register grammar
   without claiming full emulator identity from a few sampled addresses.
6. Only after separately reviewed breakpoint/capture controls may the team
   attempt a single native player0 engine-issued request to six-byte reply,
   legal move/target, player PP and cancellation, game-owned terminal,
   overworld/next wild and manual fallback in ONE authentic session.
7. Preserve main, canonical source-first, all exact-head drafts, protected
   Current ROM/save, enemy and NPC-partner AI. Never silently promote draft
   tools or treat historic modified ROM evidence as Current-ROM evidence.

Current evidence baseline (pre-Stage A): 9/9 authentic limited Current boot
checks, 32/32 verified save sectors. Formal native 0/20, production 0%.
Historical modified ROM 4b2585e1... and Current 7b9ac66d... MUST NOT be
conflated. Unmatched historical PP submissions classified: 0/2.

This workflow has no private-data access and makes no automated gameplay patch.
