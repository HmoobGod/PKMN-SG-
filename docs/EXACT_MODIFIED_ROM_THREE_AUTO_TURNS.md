# Exact modified ROM: three consecutive native automatic wild moves

Research-only discovery, 2026-11-11 CST / 2026-11-12 UTC. This is observation
of the EXISTING private modified ROM, NOT a newly installed source-first hook.
Protected Current, save, and main were not modified.

The protected Current ROM SHA-256 is 7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32.
The exact recovered modified ROM SHA-256 is 4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44.
The original save SHA-256 is 8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4.
Modified vs Current: 13,168 changed bytes in 64KiB blocks 1, 6, 9, 15,
497, 498, 499. Original native Thumb dispatcher 0x080619D4, completion
0x080625F8 and copy entry 0x0806B370 windows match byte-for-byte.

On the pinned unchanged original save and exact modified ROM, mGBA naturally
entered an ordinary wild single: battle flags 4, count 2, actor0 PLAYER
installer once, opponent installer once, native 44/44 original request byte
stores, pending bit after 23 original guest instructions. The original
request bytes remain PRIVATE; only their SHA256 appears in the verifier.

From the fresh player-pending state, the replay sent NO player move-menu keys,
no guest writes and no modified game hook. Original player automatic
callback and native preflight occurred three times. Native player0
emitter subcommand10 and original 6-byte buffer-B reply matched on
three consecutive turns:
  Frame 4179: packed payload259, slot3, move269, opponent1
  Frame 4318: packed payload257, slot1, move157, opponent1
  Frame 4462: packed payload257, slot1, move157, opponent1
Each produced original actor0 completion, restriction result zero, and
original native slot/move/target commit. Player-owned PP changed from
[20,10,10,20] to [20,8,10,19], exactly three PP decrements.
Frames 4179 to 4529: no original manual move-menu marker observed.
Opponent's original controller continued independently.

The private original emulator host had SHA-256
4304688a0b44007cca23c9e887af17c44530fd602ee3d1e57a232da397bec769.
The fresh preconstructor private state SHA256
a4b8849ef8037c199d8ce04230a92f6e0c87903fbc348e735481ada5c3bf8e0d
and player-pending private state SHA256
91503b1db0aae28a4c004d1af4f7e618d7aed4d291aa236950362a730763fab6.
Neither state nor ROM/save/host/request bytes may be uploaded to public GitHub.

tools/trace_exact_modified_autoplay.c: source-only, read-only exact-PC marker.
tools/verify_exact_modified_autoplay.py: offline strict chronological,
actor-owned reply/commit and own PP verifier, bounded metadata-only result.
tools/test_exact_modified_autoplay.py: synthetic mutation denials.
Private reproducible runner available in isolated local lab; never publish
private trace or any ROM binary.

NOT certified: complete battle, arbitrary engine-owned one-use authorization,
effective Disable/Choice/Encore/Imprison legality, cancellation, forced switch,
Struggle, trainer/doubles/partner, capture/item prohibition across all
contexts, Android, save compatibility or Current promotion. Formal production
acceptance remains 0/20; playable production hybrid integration 0%.
Next: verify multiple fresh wild fixtures, rejection/fallback and entire
battle with zero buttons, then only develop a bounded exact-ROM hybrid hook
for a demonstrated gap. Do not replace Current with incompatible source ROM.
