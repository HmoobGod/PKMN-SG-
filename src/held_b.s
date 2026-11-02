/* Installed in two copies. ENTRY/RESUME substituted by build script.
   Replays original actor extraction, native predicate and cmp.
   A scoped held-B input can only change true to false. */
lsrs r4,r4,#24
ldr r3,=0x0806df4d
bl call_native
push {r1,r2}
cmp r0,#0
beq done
cmp r4,#0
bne done
ldr r1,=0x030001a4
ldrb r1,[r1]
cmp r1,#1
bne done
ldr r1,=0x03002e48
ldr r1,[r1]
ldr r2,=0x080625f9
cmp r1,r2
bne done
ldr r1,=0x02001ab4
ldr r1,[r1]
cmp r1,#4
bne done
ldr r1,=0x02001ab8
ldrb r1,[r1]
cmp r1,#2
bne done
ldr r1,=0x03005600
ldrh r1,[r1]
movs r2,#2
tst r1,r2
beq done
movs r0,#0
done:
pop {r1,r2}
ldr r3,=RESUME
mov lr,r3
adds r3,#2
cmp r0,#0
bx r3
call_native:
bx r3
