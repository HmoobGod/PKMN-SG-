.syntax unified
.thumb
.section .text,"ax",%progbits
.global sg_r13_wrapper
.thumb_func
sg_r13_wrapper:
    push {r0,r1,r2,r3,r4,r5,r6,r7,lr}
    mov r0,r12
    push {r0}
    sub sp,#48
    movs r0,r4
    mov r1,sp
    ldr r3,=0x09f20101
    bl call_ptr
    cmp r0,#4
    beq candidate
    cmp r0,#5
    beq manual
    b original
candidate:
    ldr r3,=0x09f2d001
    bl call_ptr
    cmp r0,#1
    bne manual
    add sp,#48
    pop {r0}
    mov r12,r0
    pop {r0,r1,r2,r3,r4,r5,r6,r7}
    pop {r3}
    mov lr,r3
    ldr r3,=0x09f1f001
    bx r3
manual:
    add sp,#48
    pop {r0}
    mov r12,r0
    pop {r0,r1,r2,r3,r4,r5,r6,r7}
    pop {r3}
    mov lr,r3
    movs r6,#0
    ldr r3,=0x08065a97
    bx r3
original:
    add sp,#48
    pop {r0}
    mov r12,r0
    pop {r0,r1,r2,r3,r4,r5,r6,r7}
    pop {r3}
    mov lr,r3
    ldr r3,=0x09f1f001
    bx r3
call_ptr:
    bx r3
    .ltorg