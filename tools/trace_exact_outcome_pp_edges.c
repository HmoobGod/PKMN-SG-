/* Source-only, read-only exact-ROM outcome/PP discovery observer.
 * The candidate outcome BYTE address MUST come from separate authentic
 * evidence; its value/write PC are candidates, NOT a victory certificate.
 * No guest RAM/ROM/save writes, input injection, or controller modification.
 * All writes observed are made by the ORIGINAL guest CPU while stepping.
 * Extended marker family records the original controller reply/complete/
 * validation/slot/move/target sequence; marker alone is never execution.
 */
#include <stdint.h>
#include <string.h>
#define SG_MAIN 0x030055D4u
#define SG_FLAGS 0x02001AB4u
#define SG_PENDING 0x02001D2Cu
#define SG_PP 0x02001EF1u
#define SG_MAX_WATCH 11u

enum {
    SG_OUTCOME_CANDIDATE=1, SG_INBATTLE, SG_CALLBACK1, SG_CALLBACK2,
    SG_PP_CHANGE, SG_PLAYER_EMIT, SG_PLAYER_REPLY, SG_MANUAL_MENU,
    SG_FLAGS_CHANGE, SG_PENDING_CHANGE, SG_MAIN_PHASE,
    SG_PLAYER_COMPLETE, SG_NATIVE_VALIDATOR, SG_NATIVE_SLOT,
    SG_NATIVE_MOVE, SG_NATIVE_TARGET
};
typedef struct {
    uint32_t frame, step, pc, kind, address, before, after, slot;
    uint32_t r0, r1, r2, r3, r4, flags, battlers, pending, inbattle,
             callback1, callback2;
} SG_OutcomeEdge;
typedef struct {
    uint32_t status, start_frame, end_frame, event_count;
    uint64_t guest_steps;
} SG_OutcomeEdgeRun;
typedef struct {
    uint32_t address, width, kind, slot, previous;
} SG_Watch;

/* Raw Thumb r15 is execution PC+2. Deny invalid or ambiguous CPU origin
 * BEFORE recording a putative original outcome, callback or PP writer. */
static int sg_original_thumb_pc(uint32_t raw)
{
    return !(raw&1u) &&
           ((raw>=0x08000002u && raw<=0x0A000000u) ||
            (raw>=0x02000002u && raw<=0x02040000u) ||
            (raw>=0x03000002u && raw<=0x03008000u));
}

/* Event kind never claims the candidate address is gBattleOutcome. */
static void sg_edge_append(void *core, uint32_t (*read8)(void *,uint32_t,int),
                           uint32_t (*read32)(void *,uint32_t,int),
                           SG_OutcomeEdge *events, uint32_t capacity,
                           SG_OutcomeEdgeRun *out, uint32_t frame,
                           uint32_t step, uint32_t pc, uint32_t kind,
                           uint32_t addr, uint32_t old, uint32_t now,
                           uint32_t slot, const uint32_t r[5])
{
    SG_OutcomeEdge *e;
    if (!sg_original_thumb_pc(pc)) {out->status=6;return;}
    if (out->event_count >= capacity) {out->status=3;return;}
    e=&events[out->event_count++];
    *e=(SG_OutcomeEdge){
        frame,step,pc-2u,kind,addr,old,now,slot,
        r[0],r[1],r[2],r[3],r[4],
        read32(core,SG_FLAGS,0),read8(core,0x02001AB8u,0),
        read32(core,SG_PENDING,0),read8(core,SG_MAIN+0x439u,0),
        read32(core,SG_MAIN,0),read32(core,SG_MAIN+4u,0)
    };
}

void sg_trace_exact_outcome_pp_edges(void *core, uint32_t *regs,
                                     uint32_t frames, uint64_t maxsteps,
                                     uint32_t candidate_outcome_byte_addr,
                                     SG_OutcomeEdge *events, uint32_t cap,
                                     SG_OutcomeEdgeRun *out)
{
    SG_Watch watch[SG_MAX_WATCH];
    uint32_t n=0;
    void (*step)(void *);
    uint32_t (*frame)(void *);
    uint32_t (*read8)(void *,uint32_t,int);
    uint32_t (*read32)(void *,uint32_t,int);
    if (!out)return;
    memset(out,0,sizeof *out);
    if (!core || !regs || !events || !cap || cap>2048u ||
        !frames || frames>10000u || !maxsteps || maxsteps>0xFFFFFFFFu) {
        out->status=4;return;
    }
    if (candidate_outcome_byte_addr &&
        (candidate_outcome_byte_addr<0x02000000u ||
         candidate_outcome_byte_addr>0x0203FFFFu ||
         (candidate_outcome_byte_addr>=SG_PP && candidate_outcome_byte_addr<SG_PP+4u) ||
         (candidate_outcome_byte_addr>=SG_FLAGS && candidate_outcome_byte_addr<SG_FLAGS+4u) ||
         (candidate_outcome_byte_addr>=SG_PENDING && candidate_outcome_byte_addr<SG_PENDING+4u))) {
        out->status=4;return;
    }
    /* ABI slots may not satisfy host function-pointer alignment.
     * memcpy is well-defined, and a missing method fails closed. */
    memcpy(&step,(char *)core+0x13e8,sizeof step);
    memcpy(&frame,(char *)core+0x1428,sizeof frame);
    memcpy(&read8,(char *)core+0x1488,sizeof read8);
    memcpy(&read32,(char *)core+0x1498,sizeof read32);
    if (!step || !frame || !read8 || !read32) {out->status=4;return;}
    if (candidate_outcome_byte_addr)
        watch[n++]=(SG_Watch){candidate_outcome_byte_addr,1,SG_OUTCOME_CANDIDATE,255,0};
    watch[n++]=(SG_Watch){SG_MAIN+0x439u,1,SG_INBATTLE,255,0};
    watch[n++]=(SG_Watch){SG_MAIN,4,SG_CALLBACK1,255,0};
    watch[n++]=(SG_Watch){SG_MAIN+4u,4,SG_CALLBACK2,255,0};
    watch[n++]=(SG_Watch){SG_FLAGS,4,SG_FLAGS_CHANGE,255,0};
    watch[n++]=(SG_Watch){SG_PENDING,4,SG_PENDING_CHANGE,255,0};
    watch[n++]=(SG_Watch){SG_MAIN+0x438u,1,SG_MAIN_PHASE,255,0};
    for (uint32_t k=0;k<4;k++)
        watch[n++]=(SG_Watch){SG_PP+k,1,SG_PP_CHANGE,k,0};
    for (uint32_t j=0;j<n;j++)
        watch[j].previous=(watch[j].width==1 ?
                           read8(core,watch[j].address,0) :
                           read32(core,watch[j].address,0));
    out->start_frame=frame(core);
    uint32_t last_frame=out->start_frame;
    for (uint64_t step_index=0;step_index<maxsteps;step_index++) {
        uint32_t f=frame(core), pc=regs[15],r[5],kind=0;
        /* Unsigned subtraction alone turns a clock rollback into a fake
         * completed frame window. Reject even an in-window time rollback. */
        if (f<out->start_frame || f<last_frame) {out->status=5;break;}
        if (f-out->start_frame>=frames) {out->status=1;break;}
        if (!sg_original_thumb_pc(pc)) {out->status=6;break;}
        last_frame=f;
        for (uint32_t j=0;j<5;j++)r[j]=regs[j];
        if (pc==0x0806BD82u && r[0]==0 && r[2]==10)kind=SG_PLAYER_EMIT;
        else if (pc==0x0806B372u && r[0]==0 && r[1]==1 && r[3]==6)
            kind=SG_PLAYER_REPLY;
        else if (pc==0x0806449Eu)kind=SG_MANUAL_MENU;
        else if (pc==0x0806261Eu && r[0]==0)kind=SG_PLAYER_COMPLETE;
        else if (pc==0x08094332u)kind=SG_NATIVE_VALIDATOR;
        else if (pc==0x0809435Eu)kind=SG_NATIVE_SLOT;
        else if (pc==0x08094376u)kind=SG_NATIVE_MOVE;
        else if (pc==0x08094382u)kind=SG_NATIVE_TARGET;
        if (kind)
            sg_edge_append(core,read8,read32,events,cap,out,f,
                           (uint32_t)step_index,pc,kind,0,0,0,255,r);
        if (out->status==3)break;
        step(core);out->guest_steps++;
        for (uint32_t j=0;j<n;j++) {
            SG_Watch *w=&watch[j];
            uint32_t now=(w->width==1 ? read8(core,w->address,0) :
                          read32(core,w->address,0));
            if (w->previous!=now) {
                sg_edge_append(core,read8,read32,events,cap,out,f,
                               (uint32_t)step_index,pc,w->kind,w->address,
                               w->previous,now,w->slot,r);
                w->previous=now;
                if(out->status==3)break;
            }
        }
        if(out->status==3)break;
    }
    out->end_frame=frame(core);
    if (out->end_frame<out->start_frame || out->end_frame<last_frame)
        out->status=5;
    if(!out->status)out->status=2; /* Instruction budget, NOT a terminal. */
}
