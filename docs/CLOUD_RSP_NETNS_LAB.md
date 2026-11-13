# Cloud network-isolation feasibility — ONLY synthetic noncommercial ROM

This PR is isolated from (but based on) unchanged approved PR30 exact
6a6252c263d1998ba41a3430d68cc9adfb8b25f5. It does not change approved
PR30 or PR31, and needs independent exact-head source/security review.

Cloud runner builds a disposable Ubuntu 24.04 container from ONLY four
public Python files. GitHub Action creates it with Docker --network none,
drops all capabilities, disallows privilege escalation, makes root filesystem
read-only, supplies a temporary writable /tmp, and uses no private secrets.
The container now runs as unprivileged UID/GID 65534, has explicit
512 MiB memory and 128-PID limits, and prints its built image ID for
repeatable identity checks. Ubuntu base and apt package versions are still
floating: an image ID is NOT a pinned upstream build. Inside the container
the egress check accepts refused/unroutable connections as **negative
connectivity evidence**, not a standalone proof of isolation; a timeout
is **inconclusive and fails closed**. Tests now cover reachable local
listeners, closed ports, IPv6 success, timeout, malformed procfs rows,
and direct `inspect_network` rejection of extra interfaces.

Before starting the container, the host checks Docker NetworkMode equals none.
Inside the container, BEFORE starting mGBA, a fail-closed checker requires
/sys/class/net to contain only lo, both /proc/net/tcp and tcp6 to be readable
and parsable, and direct IPv4 and IPv6 outbound connects to fail. After mGBA
starts, it repeats checks, requires a GDB listener on port 2345, and tries
actual ?/g/m against a new **generated, original public** ROM fixture.

An IPv4 0.0.0.0 or IPv6 :: listener INSIDE a correctly isolated namespace
need not mean external exposure, but a wildcard on the ordinary host is
dangerous. This workflow does not prove a firewall on Windows, a phone,
an arbitrary private runner, or any other unrelated runtime. It does not
authorize private staging, data transfers, commercial-ROM hosting or reuse
with a real game. Never upload ROM/save files publicly or privately until
owner-specific legal/security approval and an independently reviewed
private staging design. An outside-namespace connection to the container
has no routable container address under Docker network=none; runtime verifies
only lo. Reviewers must assess this evidence separately before any private
game plan. Listener parsing includes BOTH TCP4/TCP6. Reject unreadable or
unresolved tables and unexpected network interfaces.

This proves network sandbox feasibility and a real synthetic emulator
handshake only. Does NOT show stopped breakpoint, player0 engine request,
legal automatic move, PP, terminal, manual fallback, or modified/Current
game ROM identity; formal native acceptance remains 0/20 (0%).
