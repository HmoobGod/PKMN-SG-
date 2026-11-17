/*
 * SoulGold PLAYABLE-FIRST R4: independent reconstruction of the native
 * observed-Oblivious candidate with conservative player-owned restrictions.
 *
 * The exact R3 assembly (SHA256 007d102a...) could not be recovered as bytes.
 * This is NOT a line-preserving revision of that file.  DO NOT release or
 * replace the installed controller without independent native validation.
 *
 * Thumb entry: 0x09F34001, reached from the 8-byte 0x08065ED8 veneer.
 * Expected input: r4=actor, r6=original selected move slot.  All other
 * entry registers except r7 and flags must be preserved. r7 liveness
 * caveat audited in accompanying source-only report.
 *
 * Absolute RAM addresses and layout derived from the owner's actual
 * original 32 MiB ROM disassembly and bundled soulgold-master source.
 */
.syntax unified
.cpu arm7tdmi
.thumb
.section .text.r4guard,"ax",%progbits
.global soul_gold_r4_hook
.thumb_func
soul_gold_r4_hook:
    push    {r0-r5}
    cmp     r4, #0                  @ actor0 ONLY
    bne     .Lkeep
    cmp     r6, #3                  @ original chose slot3 Taunt
    bne     .Lkeep

    ldr     r0, .Lbattle_type_flags
    ldr     r0, [r0]
    cmp     r0, #4                  @ exactly original wild single flags
    bne     .Lkeep
    ldr     r0, .Lbattlers_count
    ldrb    r0, [r0]
    cmp     r0, #2
    bne     .Lkeep

    ldr     r0, .Lbattle_mons       @ player BattlePokemon (battler 0)
    ldrh    r1, [r0, #14]           @ owned move slot1 = Rock Slide 157
    movs    r2, #157
    cmp     r1, r2
    bne     .Lkeep
    ldrh    r1, [r0, #18]           @ owned move slot3 = Taunt 269
    ldr     r2, .Ltaunt
    cmp     r1, r2
    bne     .Lkeep
    movs    r2, #38                 @ Thumb-1 byte offset limit 31
    ldrb    r1, [r0, r2]            @ owned slot1 PP positive
    cmp     r1, #0
    beq     .Lkeep

    movs    r2, #152               @ enemy battler1 struct stride 0x98
    adds    r2, r0, r2
    ldrh    r2, [r2]
    cmp     r2, #108                @ observed Lickitung species
    bne     .Lkeep
    movs    r3, #250               @ opponent1 volatile.imprison byte
    adds    r3, r0, r3             @ foe base (0x98) + volatile (+98)
    ldrb    r3, [r3]
    movs    r2, #1
    tst     r3, r2                 @ fail closed if Imprison is active
    bne     .Lkeep

    ldr     r1, .Lhistory_pointer  @ publicly revealed opponent ability
    ldr     r1, [r1]
    cmp     r1, #0
    beq     .Lkeep
    ldrh    r1, [r1, #2]            @ gBattleHistory->abilities[1]
    cmp     r1, #12                 @ Oblivious, displayed by script
    bne     .Lkeep

    ldr     r1, [r0, #108]          @ owned volatile field word
    lsrs    r2, r1, #11             @ disabledMove bits 11..20
    ldr     r3, .Lmove_mask
    ands    r2, r3
    cmp     r2, #157                @ Rock Slide currently Disabled
    beq     .Lkeep
    lsrs    r2, r1, #21             @ encoredMove bits 21..30
    ands    r2, r3
    cmp     r2, #0                  @ ANY active Encore: no override
    bne     .Lkeep
    ldr     r1, [r0, #88]           @ owned Torment bit7: fail closed
    movs    r2, #128
    tst     r1, r2
    bne     .Lkeep

    ldr     r1, .Lbattle_struct_ptr
    ldr     r1, [r1]
    cmp     r1, #0
    beq     .Lkeep
    ldr     r2, .Lchoiced_offset
    adds    r1, r1, r2
    ldrh    r1, [r1]
    cmp     r1, #0                  @ no engine Choice/Gorilla lock
    beq     .Lcheck_items
    ldr     r2, .Lmove_unavailable
    cmp     r1, r2
    beq     .Lcheck_items
    movs    r2, #157
    cmp     r1, r2                  @ only matching Rock Slide lock
    bne     .Lkeep

.Lcheck_items:
    @ Also fail closed for either held Choice item; source permits 2 items.
    ldrh    r1, [r0, #48]           @ actual aligned items[0] offset
    ldr     r2, .Lchoice_band
    subs    r3, r1, r2              @ if unsigned (item-442)<=2, choice
    cmp     r3, #2
    bls     .Lkeep
    ldrh    r1, [r0, #50]           @ items[1]
    subs    r3, r1, r2
    cmp     r3, #2
    bls     .Lkeep

    @ Gorilla Tactics may be the active ability OR a registered innate.
    ldrh    r1, [r0, #32]           @ active ability
    cmp     r1, #255
    beq     .Lkeep
    movs    r2, #142
    adds    r2, r0, r2              @ innates[0..2] by compiled layout
    ldrh    r1, [r2]
    cmp     r1, #255
    beq     .Lkeep
    ldrh    r1, [r2, #2]
    cmp     r1, #255
    beq     .Lkeep
    ldrh    r1, [r2, #4]
    cmp     r1, #255
    beq     .Lkeep

    movs    r6, #1                  @ ONLY selected candidate slot
.Lkeep:
    pop     {r0-r5}
    @ Exact original overwritten bytes at 0x08065ED8..0x08065EDF:
    push    {lr}                    @ 00 b5
    adds    r3, r3, r0              @ 1b 18
    strb    r2, [r5]                @ 2a 70
    lsls    r2, r6, #1              @ 72 00 (restores original flags)
    ldr     r7, .Lresume
    bx      r7

.align 2
.Lbattle_type_flags: .word 0x02001AB4
.Lbattlers_count:   .word 0x02001AB8
.Lbattle_mons:     .word 0x02001ECC
.Lhistory_pointer: .word 0x02001E94
.Lbattle_struct_ptr:.word 0x02001ABC
.Ltaunt:           .word 269
.Lmove_mask:       .word 1023
.Lchoiced_offset:  .word 364
.Lmove_unavailable:.word 65535
.Lchoice_band:     .word 442
.Lresume:         .word 0x08065EE1
