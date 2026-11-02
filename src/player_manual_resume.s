/* Native controller callback ABI: r0=actor, called on a later frame.
 * Recreate the exact PlayerHandleChooseMove prologue required by its
 * original manual setup tail. No save-option edits or duplicate completion.
 */
    push {r4, r5, r6, r7, lr}
    movs r4, r0
    movs r6, #0
    ldr r0, =0x08065a97
    bx r0
