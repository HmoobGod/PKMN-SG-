# PR26 source-only strict post-resume adapter — generated test boundary

This independent draft branches from approved PR41 exact head
`e9e5b9f837de47a7555ea1c74860fa998bdd0515`. It DOES NOT
modify that approved parent, PR26 R4, PR42 or PR43, any protected
game ROM/save, or main/source-first.

The original private `run_capture()`, command address whitelist, ROM/save
SHA gate, output handling, single-use PP, generic `resume()`, and
`parse_stop()` are BYTE UNCHANGED. No new CLI or default behavior exists.

An imported **test-only** `PublicStrictStopAdapter` explicitly invokes
PR41's literal `qSupported:swbreak+;hwbreak+` method on an initially stopped
RSP session. It permits exactly one timeout-bounded `c`, after negotiation,
and uses **PR26's actual ACK/framing `RSP.receive()`**. It accepts ONLY the
literal `T05hwbreak:;` stop, then reads `g` via PR26 RSP and requires
the *generated Thumb target* r15 (0x08000100, +2, or +4). All other stop
replies and PCs are rejected; no poststop `g` on malformed T05, no Z0/z0
cleanup or further RSP commands on any uncertain failure. The adapter
poisons the session on Exception **and BaseException** (including
KeyboardInterrupt). Caller must terminate disposable test emulator on
failure; the adapter itself does not launch an emulator or accept any ROM path.

Test coverage includes FakeGDB synthetic packet cases and one genuine
**OS socketpair** ACK-mode exercise using a deterministic fake server which
sends generated-target bytes. This last test is a *real OS socket but
NOT a real mGBA emulator*. The separately approved public PR42 hosted
generated-ROM experiment has real mGBA T05 evidence, but used its own
receiver. The current draft does not claim PR26's receiver was proven
against real mGBA. A separately reviewed generated-ROM mGBA test needs
isolated networking and must not copy the original private game files.

No private staging, commercial game execution, player0 move, PP/outcome,
battle terminal, manual fallback or production acceptance.
Formal native game acceptance 0/20 (0%), production 0%, historic PP 0/2.
