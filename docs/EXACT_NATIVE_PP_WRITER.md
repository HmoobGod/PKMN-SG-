# Exact native PP write PC — player-only wild-single research

Source-only validation checkpoint. Protected Current ROM, original save,
production main and opponent/NPC AI untouched. This is NOT a new hybrid
hook and NOT a playable production acceptance.

An instruction-by-instruction, read-only mGBA core replay on exact modified
ROM SHA256 4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44,
using the verified original save 8c6cb520...a5579a4, naturally reached
a separate normal wild-single encounter after original overworld movement.
Two original actor0 automatic native move emitter actions (subcommand10,
payload256=slot0, opponent1), original reply/completion and original
slot/move/target commits occurred without any host move-menu buttons.

The exact native instruction at 0x0809E6BA wrote the own-battler
PP byte at 0x02001EF1:
- Frame 5023, player slot0 20 -> 19.
- Frame 5195, player slot0 19 -> 18.

These changes followed separate original player0 native move requests.
The 64-byte code neighborhood [0x0809E6AA,0x0809E6EA) was byte-identical
on protected Current and exact modified ROM, SHA256
84ffa68c024412568ce64fdac3719cd460c40a55caf07a5549bd150a7fe50923.
The writer instruction is Thumb STRB R6,[R1] at +0x10 in this window;
no ROM code mutation was made. Total 99 private CPU events, trace SHA256
3b8c9d582f09244435643017f0821dc6f84178216ae98e6636f30dfc63ec4aed.

CRITICAL: other instructions also write the SAME four watched bytes:
the original bulk-copy PC around 0x08002112/0x08002116 accounts
for seven recorded changes, and 0x081FB8DA accounts for 28
additional changes often 5/10/15. A beginning/end memory difference
by itself is NOT a valid count of PP-consuming moves. Those other
writes may involve initialization, re-use of memory, or different
battle/animation processes; exact lifetime and cause remain unproven.
The 2 unaccounted-for submissions from the earlier independent
8-command fixture remain unresolved. No acceptance count is increased.

tools/trace_exact_pp_writer.c implements the same bounded read-only
original guest CPU observer with private input supplied separately.
tools/verify_exact_pp_writer.py pins exact private provenance,
64-byte Thumb identity, native move emitter/response/commit order and
actual single-point PP write PC. tools/test_exact_pp_writer.py
denies fake/duplicate/early/wrong-actor PP claims in synthetic CI.
Private ROM, save, state, host and trace are never published.

Terminal state still blocked: quiet original battle flags4/battlers2/
pending0 do not prove a battle outcome or overworld callback. Precise
original instruction/guest callback evidence needed. Effective move
Disable/Choice/Encore/Imprison and one-use request epoch also not
fully established, so formal gameplay acceptance 0/20 (0%),
production native hybrid injection 0%. Preserve manual safety fallback,
no automatic battle items/capture/Master Ball, no trainer/doubles/
partner AI or uncertified force-switch/Struggle automation.
