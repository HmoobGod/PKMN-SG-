/* Native gMain.inBattle-bit edge observer: source-only, read-only.
 * Watches the original Main field at 0x03005A0D (base 0x030055D4 + 0x439).
 * Records guest CPU PC immediately BEFORE an original core step which changes
 * bit1 (the actual inBattle field), irrespective of its machine opcode.
 * Neither an edge, callback swap nor old gBattleTypeFlags=4 proves outcome.
 * NO guest ROM/RAM writes, input, controller hooks, or save operations. */
#include <stdint.h>
#include <string.h>
#define EDGE_MAIN 0x030055D4u
#define EDGE_INBATTLE (EDGE_MAIN+0x439u)
#define EDGE_FLAGS 0x02001AB4u
#define EDGE_PENDING 0x02001D2Cu
#define EDGE_BATTLERS 0x02001AB8u
#define EDGE_STEP_OFFSET 0x13E8u
#define EDGE_FRAME_OFFSET 0x1428u
#define EDGE_R8_OFFSET 0x1488u
#define EDGE_R32_OFFSET 0x1498u

typedef struct {
    uint32_t frame, step_index, pc, opcode_halfword;
    uint32_t before_byte, after_byte, before_callback1, after_callback1;
    uint32_t before_callback2, after_callback2;
    uint32_t before_flags, after_flags, before_pending, after_pending;
    uint32_t before_battlers, after_battlers, registers[8];
} SG_MainBattleEdge;
typedef struct {
    uint32_t status, start_frame, end_frame, total_edges, start_byte,
             end_byte, start_callback1, start_callback2, end_callback1,
             end_callback2, start_flags, end_flags;
    uint64_t guest_steps;
} SG_MainBattleEdgeRun;

void sg_trace_main_battle_edge(void *core, const uint32_t *regs,
                               uint32_t frames, uint64_t maxsteps,
                               SG_MainBattleEdge *events, uint32_t cap,
                               SG_MainBattleEdgeRun *out)
{
    void(*step)(void*);
    uint32_t(*frame)(void*);
    uint32_t(*read8)(void*,uint32_t,int);
    uint32_t(*read32)(void*,uint32_t,int);
    if(!out)return;
    memset(out,0,sizeof *out);
    if(!core||!regs||!events||!cap||cap>256u||!frames||frames>10000u||
       !maxsteps||maxsteps>UINT32_MAX){out->status=4;return;}
    memcpy(&step,(char*)core+EDGE_STEP_OFFSET,sizeof step);
    memcpy(&frame,(char*)core+EDGE_FRAME_OFFSET,sizeof frame);
    memcpy(&read8,(char*)core+EDGE_R8_OFFSET,sizeof read8);
    memcpy(&read32,(char*)core+EDGE_R32_OFFSET,sizeof read32);
    if(!step||!frame||!read8||!read32){out->status=4;return;}
    out->start_frame=frame(core);
    out->start_byte=read8(core,EDGE_INBATTLE,0)&255u;
    out->start_callback1=read32(core,EDGE_MAIN,0);
    out->start_callback2=read32(core,EDGE_MAIN+4u,0);
    out->start_flags=read32(core,EDGE_FLAGS,0);
    uint32_t previous=out->start_byte;
    for(uint64_t i=0;i<maxsteps;i++){
        uint32_t f=frame(core), rawpc=regs[15];
        if(f<out->start_frame){out->status=5;break;}
        if(f-out->start_frame>=frames){out->status=1;break;}
        uint32_t r[8];
        for(unsigned k=0;k<8;k++)r[k]=regs[k];
        uint32_t c1=read32(core,EDGE_MAIN,0),c2=read32(core,EDGE_MAIN+4u,0);
        uint32_t fl=read32(core,EDGE_FLAGS,0),p=read32(core,EDGE_PENDING,0);
        uint32_t b=read8(core,EDGE_BATTLERS,0)&255u;
        uint32_t opcode=0,pc=0;
        /* Observed ROM-address PC encoding in pinned mGBA guest: opcode PC+2.
         * If another mode/address is seen, preserve it as ZERO/UNKNOWN. */
        if(rawpc>=0x08000002u && rawpc<0x0A000002u && !(rawpc&1u)){
            pc=rawpc-2u;
            opcode=(read8(core,pc,0)&255u)|((read8(core,pc+1u,0)&255u)<<8);
        }
        step(core);out->guest_steps++;
        uint32_t current=read8(core,EDGE_INBATTLE,0)&255u;
        if((previous^current)&2u){
            if(out->total_edges>=cap){out->status=3;break;}
            SG_MainBattleEdge *e=&events[out->total_edges++];
            memset(e,0,sizeof *e);
            e->frame=f;e->step_index=(uint32_t)i;
            e->pc=pc;e->opcode_halfword=opcode;
            e->before_byte=previous;e->after_byte=current;
            e->before_callback1=c1;e->after_callback1=read32(core,EDGE_MAIN,0);
            e->before_callback2=c2;e->after_callback2=read32(core,EDGE_MAIN+4u,0);
            e->before_flags=fl;e->after_flags=read32(core,EDGE_FLAGS,0);
            e->before_pending=p;e->after_pending=read32(core,EDGE_PENDING,0);
            e->before_battlers=b;
            e->after_battlers=read8(core,EDGE_BATTLERS,0)&255u;
            for(unsigned k=0;k<8;k++)e->registers[k]=r[k];
        }
        previous=current;
    }
    out->end_frame=frame(core);
    out->end_byte=read8(core,EDGE_INBATTLE,0)&255u;
    out->end_callback1=read32(core,EDGE_MAIN,0);
    out->end_callback2=read32(core,EDGE_MAIN+4u,0);
    out->end_flags=read32(core,EDGE_FLAGS,0);
    if(!out->status)out->status=2; /* Incomplete: guest CPU budget hit. */
}
