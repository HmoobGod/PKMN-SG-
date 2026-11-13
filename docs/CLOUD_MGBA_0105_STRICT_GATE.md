# Public mGBA 0.10.5 exact package/version and environment hardening

This isolated NEW draft branches from independently Claude-approved PR #35,
exact head 7db58590cd3f93511334a833a26f52bbe3fc917c. It never changes
that reviewed source, previous PR exact heads, main, canonical source-first,
or protected Current ROM/save.

The old Ubuntu 26.04 Docker CMD used grep -F '0.10.5' against a whole
dpkg-query output row, allowing suffixes or unrelated substrings.
This new version gate reads ONLY dpkg-query -W -f='${Version}' mgba-sdl
into Python, enforces a FULL EQUAL comparison to the prior actually
observed Ubuntu package identity 0.10.5+dfsg-3build1, prints that
identity, and refuses a changed package before any mGBA executable
or test ROM is launched. If Ubuntu packages change, public CI fails
closed; this is NOT the same as pinning Ubuntu base/apt contents by
immutable image digest. A missing or broken dpkg-query also fails.

Additional tests mutate/test the FULL combined fixture runner's
subprocess environment: only PATH, DISPLAY, XAUTHORITY, HOME and
SDL_AUDIODRIVER may reach mGBA; an injected SG_PRIVATE_SENTINEL
must be dropped. Another full-run test confirms that after
the public read-only ?/g/m/Z0/z0 fixture roundtrip there is a
post-cleanup '?' grammar verification. No new debugger commands,
ROM inputs, upload mechanisms or private collection are added.

The existing network=none Docker harness remains nonroot, only-lo,
capability-dropped, memory/PID bounded and with two-family negative
egress checks and deliberate networked-container denial.
The prior genuine hosted mGBA0.10.5 synthetic ARM-width-4 and
Thumb-width-2 protocol tests must run as before.

Strict scope: public GENERATED 32KiB noncommercial ROM only; no game
ROM/save, no breakpoint HIT, no c/s/Ctrl-C, no native player0 auto
move, PP, terminal, overworld, manual fallback, private staging or
gameplay. Formal native acceptance 0/20 (0%), production 0%,
historical PP events 0/2 classified. This new exact head needs its
own independent source/test/security review.
