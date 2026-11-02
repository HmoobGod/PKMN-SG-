/* Exact-Current experimental safety guard. Thumb-1 / ARM7TDMI.
 * Hook: player ChooseMove automatic branch, 0x08065b18 (8 original bytes).
 * No Smart AI scorer or new automatic action authorization.
 * Non-player controller classes pass through the original route unchanged.
 * Invalid owned move selections enter the existing manual setup at 0x08065a96.
 * The original player-handler prologue remains on the stack on every exit.
 */
    push {r4, r5, r6, r7, lr}
    cmp r4, #4
    bhs original
    ldr r0, =0x030001a4
    ldrb r0, [r0, r4]
    cmp r0, #1
    bne original
    ldr r0, =0x03002e48
    lsls r1, r4, #2
    ldr r0, [r0, r1]
    ldr r1, =0x080625f9
    cmp r0, r1
    bne original
    ldr r0, =0x02001e90
    ldr r0, [r0]
    adds r0, r0, r4
    ldr r1, =0x106
    ldrb r2, [r0, r1]
    cmp r2, #4
    bhs manual
    ldr r0, =0x02001ecc
    movs r1, #152
    muls r1, r4, r1
    adds r0, r0, r1
    lsls r3, r2, #1
    adds r3, r3, r0
    ldrh r3, [r3, #12]
    cmp r3, #0
    beq manual
    ldr r1, =936
    cmp r3, r1
    bhs manual
    movs r7, r3
    ldr r3, =0x02001c6c
    ldr r3, [r3]
    lsls r1, r4, #9
    adds r3, r3, r1
    lsls r1, r2, #1
    adds r3, r3, r1
    ldrh r3, [r3, #20]
    cmp r3, r7
    bne manual
    adds r0, r0, r2
    /* Exact observed native Disable identity, bits11..20 at actor+0x6C.
     * This negative check is not complete native move permission. */
    movs r1, r0
    subs r1, r1, r2
    ldr r1, [r1, #108]
    lsls r1, r1, #11
    lsrs r1, r1, #22
    cmp r1, r7
    beq manual
    /* Original native Encore: timer bits15..17 at own+0x74;
     * stored move bits21..30 at own+0x6C. Negative restriction only.
     * r0 remains base+slot; r1/r3 are dead scratch on both exits. */
    movs r1, r0
    subs r1, r1, r2
    ldr r3, [r1, #116]
    lsls r3, r3, #14
    lsrs r3, r3, #29
    beq encore_done
    ldr r1, [r1, #108]
    lsls r1, r1, #1
    lsrs r1, r1, #22
    cmp r1, r7
    bne manual
encore_done:
    /* Native repeat-move predicate: own+0x58 bit7 and own last-ID table.
     * No call to the side-effecting restriction helper. */
    movs r1, r0
    subs r1, r1, r2
    adds r1, #88
    ldrb r1, [r1]
    lsrs r1, r1, #7
    beq repeat_done
    ldr r1, =0x02001df8
    lsls r3, r4, #1
    ldrh r1, [r1, r3]
    cmp r1, r7
    beq manual
repeat_done:
    adds r0, #37
    ldrb r0, [r0]
    cmp r0, #0
    beq manual
original:
    pop {r4, r5, r6, r7}
    pop {r0}
    mov lr, r0
    movs r0, r4
    ldr r3, =0x08065eb5
    bl call_original
    ldr r0, =0x08065a91
    bx r0
call_original:
    bx r3
manual:
    pop {r4, r5, r6, r7}
    pop {r0}
    mov lr, r0
    movs r6, #0
    ldr r0, =0x08065a97
    bx r0
