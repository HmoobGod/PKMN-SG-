/* Reject obviously invalid targets at the dedicated PLAYER auto emit path.
 * This is a negative safety filter, NOT complete move/target authorization.
 * Valid selections continue through the original serializer and completion.
 * Bad targets defer original manual setup to the next controller frame.
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
    cmp r6, #4
    bhs manual
    ldr r0, =0x02001ecc
    movs r1, #152
    muls r1, r4, r1
    adds r0, r0, r1
    adds r0, r0, r6
    adds r0, #37
    ldrb r0, [r0]
    cmp r0, #0
    beq manual
    ldrb r0, [r5]
    ldr r1, =0x02001ab8
    ldrb r1, [r1]
    cmp r1, #4
    bhi manual
    cmp r0, r1
    bhs manual
    movs r2, #1
    lsls r2, r0
    ldr r1, =0x02001d42
    ldrb r1, [r1]
    tst r1, r2
    bne manual
    movs r1, #152
    muls r1, r0, r1
    ldr r0, =0x02001ecc
    adds r0, r0, r1
    adds r0, #42
    ldrh r0, [r0]
    cmp r0, #0
    beq manual
original:
    pop {r4, r5, r6, r7}
    pop {r0}
    mov lr, r0
    ldrb r3, [r5]
    lsls r3, r3, #8
    movs r2, #10
    movs r1, #1
    ldr r0, =0x08065f25
    bx r0
manual:
    ldr r0, =0x03002e58
    lsls r1, r4, #2
    ldr r2, =0x09f1f201
    str r2, [r0, r1]
    pop {r4, r5, r6, r7}
    pop {r0}
    mov lr, r0
    ldr r0, =0x08065f33
    bx r0
