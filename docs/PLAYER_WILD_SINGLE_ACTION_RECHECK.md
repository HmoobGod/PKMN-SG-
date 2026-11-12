# Player-owned first-stage action reply freshness (disposable SOURCE-LAB)

2026-11-12. Parent commit `18e7275be66842df8c861c9a0166cf85b0adb5b0`.

## The demonstrated source gap

Prior to this batch, the player-only ChooseMove stage consumed a frozen lease and rechecked the original engine's live request after restrictions/target helpers. The earlier ChooseAction stage did **not** do equivalent revalidation after the target helper; it could send Fight even if that helper changed the active player request, selected move/PP or foe. This is a source-safety issue, not a claim it occurred on the user's custom ROM.

The source-LAB controller now (1) rejects changed ChooseAction opcode/owner/foe/move/PP after targeting and (2) checks the newly staged read-only lease snapshot and live ChooseAction opcode again immediately before emitting Fight. Denial invalidates staging and leaves the original manual ChooseAction path intact. It does not request or emit item, capture, switch, Struggle, trainer, doubles, enemy, NPC partner or forced-switch actions.

## Evidence and limits

- New source contract/mutation + synthetic model suite: `tools/test_wild_single_action_recheck.py`.
- Existing post-check/live-buffer contracts updated for the fourth explicit snapshot call.
- ARM lab compile is required before considering this a successful source-only change; an original 32MiB modified-ROM CPU test is required before any production promotion.
- The 32MiB original ROM (SHA256 `7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32`) and exact customized ROM (SHA256 `4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44`) are distinct, protected. No ROM/save bytes are committed here.

## Native priority

The exact modified ROM is available from a private user Library copy and the mGBA 0.10.5 AppImage is recovered from Drive. A disposable original-ROM CLI smoke run observed GBA BIOS/CPU boot logging, and the Qt mGBA GDB server accepted initial read commands; the Qt display remained black in the attempted Xvfb run and authentic in-battle states/guest CPU traces were **not** reproduced. This is host-environment recovery evidence only, not a legal automatically executed move or outcome/PP PC witness. Continue with a matching wild-battle savestate and authenticated guest CPU playback before claiming request epoch, native outcome PC, PP cause, unattended terminal, manual fallback certification or formal acceptance. Production integration remains 0%, acceptance 0/20.
