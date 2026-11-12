/* Exact modified-ROM native battle flag edge witness, READ ONLY.
 * Tests original return-to-field then NEW wild constructor by observing
 * gBattleTypeFlags guest writes and real PC. No ROM/save, partner or
 * opponent modification and NO automatic battle UI/button input.
 */
#include <stdint.h>
#include <string.h>
typedef struct {
    uint32_t frame,pc,before,after,r0,r1,r2,r3,pending,kind0,kind1;
} SG_FlagEdge;
typedef struct {
    uint32_t status,start_frame,end_frame,edges;
    uint64_t steps;
} SG_FlagStats;
void sg_trace_next_wild_flags(void *core,uint32_t *regs,uint32_t frames,
                              uint64_t limit,SG_FlagEdge *events,uint32_t cap,
                              SG_FlagStats *out){
    if(!core||!regs||!events||!out||!cap)return;
    memset(out,0,sizeof *out);
    void(*step)(void*)=*(void(**)(void*))((char*)core+0x13E8);
    uint32_t(*frame)(void*)=*(uint32_t(**)(void*))((char*)core+0x1428);
    uint32_t(*read8)(void*,uint32_t,int)=
        *(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1488);
    uint32_t(*read32)(void*,uint32_t,int)=
        *(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1498);
    out->start_frame=frame(core);
    uint32_t prior=read32(core,0x02001AB4u,0);
    for(uint64_t i=0;i<limit;i++){
        uint32_t f=frame(core),pc=regs[15];
        if(f-out->start_frame>=frames){out->status=1;break;}
        if(pc==0x0806AD48u &&
           read32(core,0x02001AB4u,0)==4u &&
           read8(core,0x02001AB8u,0)==2u){
            out->status=2;break;/* the original NEW wild constructor */
        }
        uint32_t r0=regs[0],r1=regs[1],r2=regs[2],r3=regs[3];
        step(core);out->steps++;
        uint32_t after=read32(core,0x02001AB4u,0);
        if(after!=prior){
            if(out->edges>=cap){out->status=3;break;}
            SG_FlagEdge *e=&events[out->edges++];
            *e=(SG_FlagEdge){f,pc-2u,prior,after,r0,r1,r2,r3,
                read32(core,0x02001D2Cu,0),
                read8(core,0x030001A4u,0),
                read8(core,0x030001A5u,0)};
            prior=after;
        }
    }
    out->end_frame=frame(core);
    if(!out->status)out->status=4;
}
