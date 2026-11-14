# Public player0 44-byte request-copy: Thumb STRB instruction semantics v4

## Concrete source-evidence gap

The original read-only 44-byte request-copy observer accepted all 44
changed POST-step destination bytes while only requiring a nonzero
`STORE_PC` Thumb instruction halfword and matching pre-step registers.
The PUBLIC fake CPU fixture claimed the synthetic halfword `0x7003`
(Thumb `STRB r3,[r0,#0]`) for all 44 stores, although it wrote
`dest + index` and held `r0 == dest` throughout. That instruction
cannot explain later `dest+1..dest+43` writes. The earlier proof
could therefore label incoherent CPU/memory behavior as a copy candidate.

## Distinct isolated source-only v4 repair

This **new draft**, stacked on review-pending PR68 exact
`bbf96ec1c8477d75c7004bed128b01904d7fc74a`, makes every claimed
store fail closed unless the actual PRE-step recorded Thumb-1 opcode
is `STRB Rt,[Rb,#imm5]` or `STRB Rt,[Rb,Rm]`, with the effective address
computed from actual pre-step CPU r0..r7 and exactly equal to the
watched `destination + index`; the PRE-step register Rt low byte
must exactly equal the byte that the observer sees change after the
original CPU step. Invalid opcodes, loads, wrong register/value,
incorrect destination, or 32-bit address overflow fail before
counting a store. The existing all-prefix and whole-source continuous
read-only integrity checks remain intact.

The public fake machine now advertises a **coherent synthetic** Thumb
opcode `0x5443` (`STRB r3,[r0,r1]`), matching its fake registers and
44 destination-byte writes. Three additional FAKE modes deliberately
supply `STRB r3,[r0,#0]` at later indices, a wrong Rt, and an LDRB
rather than a store; all must fail with a new error code 14 at store
index 7. These are fabricated instructions, **not** alleged original
Pokémon CPU opcode bytes.

The read-only C `Proof` now emits exactly 44 decoded effective
addresses and 44 encoded Rt source bytes alongside the already
captured bytes, store indices, pre-store destination bytes and
entry/store/post instruction halfwords. Strict Python proof schema
is explicitly bumped to `sg-public-synthetic-request-copy-v4` and
requires complete typed arrays, the 44 correct destination offsets,
exact decoded byte value parity, and a Thumb STRB instruction class.
New fixture mutations deny missing/incorrect arrays and untrusted
privilege claims. Source and public original request-copy CI run
the actual C fake-core fixture and strict Python C-to-JSON checks;
no original game binary is generated or executed.

## Limits: source-only, not native certification

The observer's fixed public reference PCs, source/dest pointer fields
and fake C opcode do **not** attest the commercial original/modified
game's instruction bytes or identify a genuine engine-issued actor0
request epoch. The stronger instruction semantic check would fail
closed if an authentic instruction uses different registers than the
current source-only recorder allows: never invent an original opcode
to make it pass. Real native one-use ownership, dynamic move/target
legality, PP debit/cancellation, result callback PC, overworld return
and manual fallback remain unverified. No private Current ROM/save,
savestate, owner emulator, original modified-ROM CPU trace or
private original game bytes are staged, read, hashed or executed.

No protected main/source-first branch or approved exact heads changed;
no auto items/capture, enemy/NPC AI, uncertified doubles, gameplay
release or merge. Formal original-game native acceptance 0/20=0%,
production 0%, historical unmatched PP cause classifications 0/2.
