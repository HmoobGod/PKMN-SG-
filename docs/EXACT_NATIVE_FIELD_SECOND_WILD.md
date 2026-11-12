# Original modified ROM: field-to-second-wild CPU evidence

No Current/save/main changes. Two independent read-only emulator diagnostics
of exact modified ROM 4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44
with original save 8c6cb520...a5579a4 demonstrate a new wild battle
from ordinary directional movement after the prior automatic encounter
had stopped submitting moves (and without any move-menu selection).

Replay #1: original first wild was constructed frame4471.
After two player-owned automatic move submissions and three consecutive
350-frame no-button windows with zero native action markers, quiet state
at frame6221 still carried gBattleTypeFlags=4. It was NOT a freeze
certificate. Ordinary directional movement (no A) was then accepted.
The flags were observed zero during field movement, and a NEW exact
original wild constructor ran at frame8609, flags4 and battler count2.
This is functional field-to-wild reentry, NOT direct proof of the prior
battle's outcome writer PC or exact gMain.callback2 native instruction.

Replay #2 (additional instruction-level CPU witness): first normal
wild was constructed at frame4475. After original automatic action
and a quiet stage at frame6575 with stale flags4, directional movement
alone reached a NEW original wild constructor at frame9994. The native
flag store 0x080C501E wrote gBattleTypeFlags from4 to0 at frame9957;
0x0808D71A wrote0 to4 at frame9993, and original constructor
0x0806AD46 (emulator prefetch PC0x0806AD48) executed at frame9994,
original controller kinds both uninstalled. The second pair of writes
belongs to new-encounter setup, not necessarily to old-battle teardown.
No menu A presses after quiet (trial0 only). Private route metadata
SHA256 6776c99fb4509873da12e12af0a114d2409deb6edce7f015431cf465ab2cdd33.

All three original exact-ROM Thumb 64-byte windows were byte-identical
against protected Current:
0x080C501E: b10cb1738322db3aff54fa02c2e47c626628441fb23d63b5c4012f15d79ca392
0x0808D71A: 2ccced6028b620b8ca2685a911c06fe6c41079e92d6c624f2e03efdd8fdcbb92
0x0806AD46: 5bbd5d0fcdb2c0b458258cee28f93709e70ac73746a20f651f24d26ef847df34

tools/trace_exact_next_wild_flags.c: bounded read-only engine-CPU flag
edge observer for private emulator guest, stops at authenticated
next original wild constructor. tools/verify_exact_next_wild.py:
exact private ROM/save/trace hash + original windows, strict monotonic
original PC/write/second constructor evidence. Its synthetic unit tests
reject fake terminal/constructor/flag mutations. Private ROM/save/host,
guest state, full CPU trace never published.

This is a real field-control continuity finding, not a 20/20
gameplay safety promotion. No exact old-battle outcome writer PC or
gMain.callback2 return PC authenticated; no full-battle result UI and
persistent saved-game compatibility proved. Unclassified original
PP-less move submissions, engine-owned one-use epochs, dynamic
Disable/Choice/Encore/Imprison legality, target/cancellation
fail-closedness, trainer/doubles/NPC partner and auto items/capture
are still blocked. Preserve Current and save; formal 0/20 (0%),
production hybrid injection 0%.
