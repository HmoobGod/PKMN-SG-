# Authenticated exact-ROM callback handoff; stale battle flags protection

PRIVATE READ-ONLY REAL EMULATOR EVIDENCE, 2026-11-12.
Existing protected Current ROM, original save and public main not modified.

A third independent normally triggered exact modified ROM 4b2585e1...d3ee44
wild single began at frame3207 from original user's save, with original actor0
and enemy controller installers each run once. 44/44 original request bytes
copied, pending actor0; private preconstructor SHA cdda0d1c...4892a0f,
private player-pending state SHA 32fd9ec6...803c9ee.
No player move-menu input after pending. Actor0 native original auto emitted
two targeted slot0/move325 submissions frames3621 and3782, and original
PP writer 0x0809E6BA debited own slot0 at frames3669 (20->19) and3830
(19->18). The 66-event private native PP trace SHA256
8d721766e92b3567fd89f2d1b70eb97d7367c09b14449a4d2b59c8ae064168bf.
Do not credit 16 additional source-copy/other byte changes as move PP.

NEW AUTHENTIC ORIGINAL gMain evidence: RAM base 0x030055D4, independently
identified through actual held/new key fields at offsets +0x28/+0x2A/
+0x2C/+0x2E responding to right/down/left/up directional inputs.
callback1 at +0x0, callback2 at +0x4, phase state +0x438,
inBattle bit in byte +0x439. During no-input battle replay,
frame3984 ORIGINAL Thumb PC0x0808E33C writes callback1
0x0808CBDD -> 0x081C7589. ORIGINAL PC0x081AED58 writes callback2
at frames3987/3988/3989/3998 through:
0x0808F225 -> 0x080C4265 -> 0x081CA4B1 -> 0x081C7F65 ->
0x081C9FC5. Main phase 0->1->2->3->0 from original native writes.
At callback handoff original gMain.inBattle byte is 0 despite stale
gBattleTypeFlags=4 and original battlers2/pending0. This demonstrates why
old flags4/quietness must NOT authorize another player automatic action.
The two original code windows at PC0x0808E33C and0x081AED58 match
the protected Current exact 64-byte Thumb windows, SHA256 respectively
e92a2c689b0dc81c18664509bd52dfb00737b76d6c5b268ba952261301c21281 and
87a078714223450057d306b127deea90d6d8ef37173973216c103f72f95dc333.
The private exact callback nine-event CPU trace SHA256
58c560303a2013c0fbfd250539bcf174d8275b56c71dad9019b8bfa08f15660a.

New source-LAB protection: SOURCE-FIRST wild-only chooser checks
gMain.inBattle before auto reply, in addition to gBattleOutcome==0,
original active player controller ownership and same foe/PP snapshots.
It is applied only in disposable upstream source LAB, NOT the user's
protected Current or actual modified game ROM. In battle gMain.inBattle
may toggle in its low bit but bit1 persists; at actual callback handoff
the bit is cleared. The engine's original manual path remains fallback.

Native original callback transfer is PROVED on this third fixture.
Previous battle's exact outcome DECISION PC, specific victory/loss,
full unattended terminal/Android compatibility and 20 formal acceptance
scenarios remain UNPROVEN. The existing movement-to-second-wild witnesses
are separate diagnostic evidence, not a proof of every outcome. No enemy
or NPC partner AI, trainer/doubles/Struggle/forced switch or automatic
bag/capture/Master Ball touched. Production integration remains 0%.
Private ROM, save, mGBA host, core states and full CPU traces are
never committed to the public GitHub repo. Next: original outcome PC
and new native rejection/legality evidence, old fixture PP-less
submissions, multiple full end-to-end battle results and save safety.
