/* Read-only, same-run actor0/PP/Main callback observer. SOURCE RESEARCH ONLY.
 * No guest writes, no host input, no ROM/save or NPC-partner access.
 * A move reply, PP change, Main clear or callback alone NEVER certifies result.
 * This observer must run against a separately authenticated exact modified ROM.
 */
#include <stdint.h>
#include <string.h>

#define MAIN_BASE 0x030055D4u
#define MAIN_BATTLE (MAIN_BASE+0x439u)
#define MAIN_PHASE (MAIN_BASE+0x438u)
#define OWN_PP 0x02001EF1u
#define BATTLE_FLAGS 0x02001AB4u
#define BATTLE_COUNT 0x02001AB8u
#define PENDING_WORD 0x02001D2Cu

enum {
    SG_JOIN_EMIT=1, SG_JOIN_REPLY=2, SG_JOIN_COMPLETE=3,
    SG_JOIN_VALIDATE=4, SG_JOIN_SLOT=5, SG_JOIN_MOVE=6,
    SG_JOIN_TARGET=7, SG_JOIN_MANUAL=8, SG_JOIN_PP_BYTE=9,
    SG_JOIN_INBATTLE=10, SG_JOIN_CALLBACK1=11, SG_JOIN_CALLBACK2=12,
    SG_JOIN_PHASE=13
};
typedef struct {
    uint32_t frame, step, pc, opcode, stage, kind, address, before, after;
    uint32_t slot, r0, r1, r2, r3, r4, flags, battlers, pending, inbattle;
    uint32_t callback1, callback2;
} SG_JointEvent;
typedef struct {
    uint32_t status, start_frame, end_frame, count;
    uint32_t initial_main, final_main, initial_cb1, final_cb1,
             initial_cb2, final_cb2, initial_pp[4], final_pp[4];
    uint64_t steps;
} SG_JointRun;

typedef struct {
    void (*step)(void *);
    uint32_t (*frame)(void *);
    uint32_t (*read8)(void *,uint32_t,int);
    uint32_t (*read32)(void *,uint32_t,int);
} SG_JointOps;

static void sg_joint_emit(SG_JointRun *out,SG_JointEvent *events,
                          uint32_t cap,SG_JointOps o,void *core,
                          uint32_t f,uint32_t st,uint32_t pc,uint32_t opcode,
                          uint32_t stage,uint32_t kind,uint32_t addr,
                          uint32_t before,uint32_t after,uint32_t slot,
                          const uint32_t r[5])
{
    SG_JointEvent *e;
    if(out->count>=cap){out->status=3;return;}
    e=&events[out->count++];
    *e=(SG_JointEvent){f,st,pc,opcode,stage,kind,addr,before,after,slot,
                       r[0],r[1],r[2],r[3],r[4],
                       o.read32(core,BATTLE_FLAGS,0),
                       o.read8(core,BATTLE_COUNT,0)&255u,
                       o.read32(core,PENDING_WORD,0),
                       o.read8(core,MAIN_BATTLE,0)&255u,
                       o.read32(core,MAIN_BASE,0),
                       o.read32(core,MAIN_BASE+4u,0)};
}

void sg_trace_exact_joint_player_terminal(void *core,const uint32_t *regs,
                        uint32_t frames,uint64_t maxsteps,SG_JointEvent *events,
                        uint32_t cap,SG_JointRun *out)
{
    SG_JointOps o;
    uint32_t state[8];
    const uint32_t addresses[8]={MAIN_BATTLE,MAIN_BASE,MAIN_BASE+4u,
                                 MAIN_PHASE,OWN_PP,OWN_PP+1u,
                                 OWN_PP+2u,OWN_PP+3u};
    if(!out)return;
    memset(out,0,sizeof *out);
    if(!core||!regs||!events||!cap||cap>1024u||!frames||frames>10000u||
       !maxsteps||maxsteps>UINT32_MAX){out->status=4;return;}
    memcpy(&o.step,(char*)core+0x13e8,sizeof o.step);
    memcpy(&o.frame,(char*)core+0x1428,sizeof o.frame);
    memcpy(&o.read8,(char*)core+0x1488,sizeof o.read8);
    memcpy(&o.read32,(char*)core+0x1498,sizeof o.read32);
    if(!o.step||!o.frame||!o.read8||!o.read32){out->status=4;return;}
    out->start_frame=o.frame(core);
    for(uint32_t j=0;j<8;j++)
        state[j]=j==1||j==2?o.read32(core,addresses[j],0):
                 (o.read8(core,addresses[j],0)&255u);
    out->initial_main=state[0];out->initial_cb1=state[1];
    out->initial_cb2=state[2];
    for(uint32_t j=0;j<4;j++)out->initial_pp[j]=state[4+j];
    for(uint64_t i=0;i<maxsteps;i++){
        uint32_t f=o.frame(core),raw=regs[15],pc=0,opcode=0,kind=0;
        uint32_t r[5];
        if(f<out->start_frame){out->status=5;break;}
        if(f-out->start_frame>=frames){out->status=1;break;}
        for(uint32_t j=0;j<5;j++)r[j]=regs[j];
        if(raw>=0x08000002u&&raw<0x0A000002u&&!(raw&1u)){
            pc=raw-2u;
            opcode=(o.read8(core,pc,0)&255u)|
                   ((o.read8(core,pc+1u,0)&255u)<<8);
        }
        if(raw==0x0806BD82u&&r[0]==0&&r[2]==10u)kind=SG_JOIN_EMIT;
        else if(raw==0x0806B372u&&r[0]==0&&r[1]==1u&&r[3]==6u)
            kind=SG_JOIN_REPLY;
        else if(raw==0x0806261Eu&&r[0]==0)kind=SG_JOIN_COMPLETE;
        else if(raw==0x08094332u)kind=SG_JOIN_VALIDATE;
        else if(raw==0x0809435Eu)kind=SG_JOIN_SLOT;
        else if(raw==0x08094376u)kind=SG_JOIN_MOVE;
        else if(raw==0x08094382u)kind=SG_JOIN_TARGET;
        else if(raw==0x0806449Eu)kind=SG_JOIN_MANUAL;
        if(kind){
            sg_joint_emit(out,events,cap,o,core,f,(uint32_t)i,pc,opcode,0,
                          kind,0,0,0,255u,r);
            if(out->status==3)break;
        }
        o.step(core);out->steps++;
        /* Per-step field updates: attach same step and original pre-step PC. */
        for(uint32_t j=0;j<8;j++){
            uint32_t now=j==1||j==2?o.read32(core,addresses[j],0):
                         (o.read8(core,addresses[j],0)&255u);
            if(state[j]==now)continue;
            /* Bit0 changes in Main are not an active-battle transition. */
            if(j==0&&!((state[j]^now)&2u)){state[j]=now;continue;}
            uint32_t changed_kind=j==0?SG_JOIN_INBATTLE:
                j==1?SG_JOIN_CALLBACK1:j==2?SG_JOIN_CALLBACK2:
                j==3?SG_JOIN_PHASE:SG_JOIN_PP_BYTE;
            sg_joint_emit(out,events,cap,o,core,f,(uint32_t)i,pc,opcode,1,
                          changed_kind,addresses[j],state[j],now,
                          j>=4?j-4u:255u,r);
            state[j]=now;
            if(out->status==3)break;
        }
        if(out->status==3)break;
    }
    out->end_frame=o.frame(core);
    out->final_main=o.read8(core,MAIN_BATTLE,0)&255u;
    out->final_cb1=o.read32(core,MAIN_BASE,0);
    out->final_cb2=o.read32(core,MAIN_BASE+4u,0);
    for(uint32_t j=0;j<4;j++)out->final_pp[j]=o.read8(core,OWN_PP+j,0)&255u;
    if(!out->status)out->status=2; /* Instruction budget is NOT success. */
}
