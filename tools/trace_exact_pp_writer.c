/* Read-only exact modified-ROM actor0 PP-writer observer.
 * Emulates original guest instruction stepping; it writes NOTHING to guest
 * ROM/RAM, opponent state, save, controller or battle inputs.
 * Original protected Current and exact modified ROM were byte compared at the
 * 0x0809E6BA native PP debit instruction. This is RESEARCH, not a hook.
 */
#include <stdint.h>
#include <string.h>
#define OWN_PP_BASE 0x02001EF1u
typedef struct {
    uint32_t frame, pc, kind, slot, before, after;
    uint32_t r0, r1, r2, r3, pending, flags;
} SG_PpEvent;
typedef struct {
    uint32_t status, start_frame, end_frame, events;
    uint64_t steps;
} SG_PpRun;
void sg_trace_exact_pp_writer(void *core, uint32_t *regs, uint32_t frames,
                              uint64_t maxsteps, SG_PpEvent *events, uint32_t cap,
                              SG_PpRun *out)
{
    if (!core || !regs || !events || !out || cap == 0 || maxsteps == 0)
        return;
    memset(out, 0, sizeof(*out));
    void (*step)(void *) = *(void (**)(void *))((char *)core + 0x13E8);
    uint32_t (*frame)(void *) = *(uint32_t (**)(void *))((char *)core + 0x1428);
    uint32_t (*read8)(void *, uint32_t, int) =
        *(uint32_t (**)(void *, uint32_t, int))((char *)core + 0x1488);
    uint32_t (*read32)(void *, uint32_t, int) =
        *(uint32_t (**)(void *, uint32_t, int))((char *)core + 0x1498);
    uint32_t prior[4];
    out->start_frame = frame(core);
    for (uint32_t k=0; k<4; k++) prior[k]=read8(core, OWN_PP_BASE+k, 0);
    for (uint64_t i=0; i<maxsteps; i++) {
        uint32_t f=frame(core), pc=regs[15], kind=0;
        if (f-out->start_frame>=frames) {out->status=1; break;}
        if (pc==0x0806BD82u && regs[0]==0u && regs[2]==10u) kind=1; /* move emit */
        if (pc==0x0806B372u && regs[0]==0u && regs[1]==1u && regs[3]==6u) kind=2; /* reply */
        if (pc==0x08094332u) kind=3; /* native validator */
        if (pc==0x0809435Eu) kind=4; /* native slot commit */
        if (pc==0x08094376u) kind=5; /* native move commit */
        if (pc==0x08094382u) kind=6; /* native target commit */
        if (pc==0x0806449Eu) kind=7; /* manual move UI */
        if (pc==0x0806261Eu && regs[0]==0u) kind=8; /* controller complete */
        if (kind) {
            if (out->events>=cap) {out->status=3; break;}
            SG_PpEvent *e=&events[out->events++];
            *e=(SG_PpEvent){f,pc-2u,kind,0,0,0,regs[0],regs[1],regs[2],regs[3],
                read32(core,0x02001D2Cu,0),read32(core,0x02001AB4u,0)};
        }
        step(core);
        out->steps++;
        /* Inspect ONLY original player's four PP bytes, after each instruction.
         * Do NOT call every change a move: copy/overlay routines also write
         * these addresses. The verifier separates exact PP debit PC from them. */
        for (uint32_t k=0;k<4;k++) {
            uint32_t now=read8(core,OWN_PP_BASE+k,0);
            if (now==prior[k]) continue;
            if (out->events>=cap) {out->status=3; break;}
            SG_PpEvent *e=&events[out->events++];
            *e=(SG_PpEvent){f,pc-2u,9,k,prior[k],now,regs[0],regs[1],
                regs[2],regs[3],read32(core,0x02001D2Cu,0),
                read32(core,0x02001AB4u,0)};
            prior[k]=now;
        }
        if(out->status==3)break;
    }
    out->end_frame=frame(core);
    if(!out->status) out->status=2; /* guest instruction budget */
}
