# SoulGold: cloud mGBA GDB/RSP staging boundary (source-only research)

Status: initial GitHub Actions run [43461371439](https://github.com/HmoobGod/PKMN-SG-/actions/runs/43461371439) **passed** on PR30 head `1575cfa4` using Ubuntu's mGBA 0.10.2. Independent Claude review returned **REQUEST CHANGES** for B1/B2 on that head. The repaired source passed real hosted CI [43463706087](https://github.com/HmoobGod/PKMN-SG-/actions/runs/43463706087) with **17/17** tests and actual `?`/`g`/`m` replies. Exact revised head still requires independent Claude re-review; the old green run/Claude verdict cannot certify the repaired head.
This isolated draft does not merge any previous SoulGold branch or touch any real game.
Its first job is answering one question: can a real **GitHub-hosted Ubuntu runner**
start packaged mGBA with a GDB remote stub and answer read-only RSP packets?

## Stage A — public, non-private compatibility check

- Isolated `pull_request` and `workflow_dispatch` workflow at `.github/workflows/cloud-mgba-rsp-fixture.yml`; never `pull_request_target`.
- Installs Ubuntu 24.04 `mgba-sdl` + `xvfb` + `xauth` at runner execution time. Ubuntu provided mGBA **0.10.2** in first real run, not the target research setup's **0.10.5**. Package versions float with Ubuntu updates; CI prints package version, frontend version, and binary SHA-256 so subsequent runner changes are visible.
- Generates **original** 32 KiB test image in a temporary runner directory;
  the GBA header licensed-logo region is left empty. No proprietary ROM data.
- Starts **actual** mGBA SDL with -g on a temporary Xvfb display.
- Connects via 127.0.0.1:2345 and allows ONLY ?, g and m080000c0,4.
- Validates RSP checksum and ACK/NAK, stop-reply **grammar**, a 128-hex-character minimum register payload compatible with PR26, an upper bound, and the exact generated fixture ROM-mapped instruction. A stop packet **does not prove that game execution is paused**, source authenticity, debugger state stability or user-input exclusion. Records public synthetic stop form, register length, extra-byte flag, ROM read and kernel-observed listening IPv4 address, but never raw registers.
- The synthetic fixture has no real Pokémon logic: passing it validates the
  hosted emulator+RSP transport, **not** actual game startup, ROM identity,
  loaded battery save, any player-owned move or native acceptance.
- No **private** ROM/save, savestate, private trace, source code, or debugger memory in workflow logs, uploaded artifacts or repository history. The public generated fixture's tiny ROM read and synthetic stop-reply metadata are logged. No secrets, GitHub token write permissions, artifact uploads or cache. Pull requests from forks receive only read-only checkout access; no private file fetch.
- The dedicated fixture workflow (not `source-check.yml`) executes bounded socket tests for allowlist, no-wire mutation denials, ACK/NAK, framing, EOF, size and prefix limits, and exact PR26-compatible register grammar. Unit-test PASS alone must never substitute for the real hosted emulator job.
- If the packaged SDL build has no GDB stub, exits, or fails to return
  correct RSP values, FAIL CI and read logs; do not claim compatibility.

## Stage B — PROPOSAL ONLY, NOT IMPLEMENTED: private exact-game staging

Do not upload the original 32 MiB ROM, 128 KiB .sav, savestate, developer
traces or any memory dump to this **public** GitHub repository, its PRs,
logs, issues, Actions artifacts, cache, comments or source ZIPs.

After Stage A genuinely passes at a reviewed head, evaluate an owner-approved
access-controlled private staging workspace (not implemented here). Commercial
ROM/save transfers, even to private repositories, can raise copyright and
platform-terms questions; do **not** upload any game files to GitHub, private
or public, absent a separate owner decision and appropriate review. Keep its
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
   **Security blocker:** hosted fixture CI 43463706087 reported
   `GDB_LISTENER_IPV4: 0.0.0.0`, meaning the mGBA stub listens on ALL IPv4
   interfaces although this probe connected to 127.0.0.1. For any future
   *private* game data, use enforceable process/network isolation (for example
   a reviewed firewall/namespace with no externally reachable GDB port),
   verify it before loading data, and fail closed if unavailable. A private
   GitHub repository alone does NOT isolate the emulator's network listener.
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

Previous game evidence is described in the [SoulGold Master Development Status](https://docs.google.com/document/d/1I6Njtr6jZlvvWTZZxgF900jr7nWsid0btHKl5Gy3amw/edit): 9/9 limited authentic Current boot checks and 32/32 save sectors audited in separate prior work. This public fixture workflow does not rerun or authenticate those claims; none constitute native move acceptance. Formal native 0/20, production 0%.
Historical modified ROM 4b2585e1... and Current 7b9ac66d... MUST NOT be
conflated. Unmatched historical PP submissions classified: 0/2.

This workflow has no private-data access and makes no automated gameplay patch.
