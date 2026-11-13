# Combined public generated-ROM mGBA debugger inside verified no-network container

**Draft source/security lab, not private staging or gameplay approval.**
Base is independently source-approved PR32 at exact
70261d8286c874eb56dbc2cdd55c1a7d5e76f075. PR31's exact approved
source and tests from 53bdb658a0e647ca2b0a290b53e5314e542f84ae
are copied BYTE-FOR-BYTE to this isolated branch (Git blob SHA parity is
recorded in the PR). PR26's exact original capture tool source from
1be4e4bc976db53b637086cdb3b65eef856ac7ed is copied unchanged to
tools/pr26_exact_probe_parser_reference.py; ONLY its original parse_stop
and parse_registers functions are invoked, never its run_capture/main or
ROM/save verification-locked original-ROM capture. Copying reviewed
code into a new combined branch does not transfer independent approval.

GitHub Actions builds its Docker image solely from checked-out public Python
source and ubuntu:24.04. It creates a capability-dropped, unprivileged,
read-only, resource-bounded container with Docker --network none. The host
first verifies NetworkMode=none. The container requires a loopback-only
network interface and both readable IPv4/IPv6 TCP listener tables; both
outbound probes must not succeed. A timeout is INCONCLUSIVE and fails closed;
an external TCP refusal is suspicious evidence of a route and fails closed
even though a refused loopback port is only negative connectivity evidence.
The public Docker image's digest and mGBA apt version are reported, but
Ubuntu and apt remain floating and are not provenance-pinned.

Only AFTER isolation checks pass, the workflow starts real mGBA -g on an
ORIGINAL GENERATED 32 KiB noncommercial GBA fixture. It queries ?/g/m,
validates PR30 grammar and the generated ROM ARM word, then uses the exact
unchanged PR31 roundtrip to install Z0,080000c0,4 and remove z0 at the same
address. It executes original PR26 parse_stop and parse_registers on the
actual returned bytes; this is **parser compatibility**, NOT running the
full PR26 original-ROM probe. The full probe REQUIRES the privately
held exact modified commercial ROM and save and MUST NOT be run against
a synthetic fixture by bypassing digest gates.

After z0 cleanup an extra read-only ? must be a valid PR26 CPU-stop
reply: a stale OK cannot certify successful cleanup. This check alone
cannot prove breakpoint state or rule out every late re-transmission;
the combined proof remains bounded protocol compatibility. No c, s,
Ctrl-C, debugger guest writes, breakpoint hits, trace logs or user inputs.
GDB still binds 0.0.0.0 *inside* the isolated namespace; outside a verified
sandbox this is unsafe.

Negative test: a SECOND short-lived container intentionally uses Docker
bridge networking with ONLY the public fixture source. It invokes
inspect_network() and must REJECT the presence of eth0 without starting
the emulator. An error unrelated to the specific network guard fails CI.

Remaining stages (NOT IMPLEMENTED or authorized here): mGBA 0.10.5 parity,
PR26's Thumb-width-2 breakpoint behavior, authentic original-game input
and CPU requests, secure private staging and owner consent, player0 one-use
request/copy and legal slot/target, PP and cancellation, game terminal,
overworld, further unattended encounters and manual fallback.
Protected Current ROM/save, main, canonical branch, prior approved PR
exact heads, enemy/NPC AI and all no-item/no-capture/no-uncertified-doubles
limits remain unchanged. Formal native game acceptance is 0/20 (0%),
production Smart Auto Battle 0%, historical unmatched PP classification 0/2.
