/* Public FAKE core only — exercise the actual source-only original-outcome
 * guest CPU observer with rolled-back frames and invalid PC values.
 * No owner ROM/save/attest/emulator, no guest memory writes or host input.
 */
#ifdef NDEBUG
#error "Original outcome observer tests require live assert checks"
#endif
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "trace_exact_outcome_pp_edges.c"

typedef struct {
    unsigned char abi[0x1500];
    uint32_t regs[16];
    uint32_t frame, index, mode, main_byte, flags, pending, battlers, pp[4];
    uint32_t callback1,callback2,phase;
} Mock;

static uint32_t fake_frame(void *v){return ((Mock *)v)->frame;}
static uint32_t fake_read8(void *v,uint32_t address,int unused)
{
    Mock *m=v;(void)unused;
    if(address==SG_MAIN+0x439u)return m->main_byte;
    if(address==SG_MAIN+0x438u)return m->phase;
    if(address==0x02001AB8u)return m->battlers;
    if(address>=SG_PP&&address<SG_PP+4u)return m->pp[address-SG_PP];
    return 0u;
}
static uint32_t fake_read32(void *v,uint32_t address,int unused)
{
    Mock *m=v;(void)unused;
    if(address==SG_MAIN)return m->callback1;
    if(address==SG_MAIN+4u)return m->callback2;
    if(address==SG_FLAGS)return m->flags;
    if(address==SG_PENDING)return m->pending;
    return 0u;
}
static void fake_step(void *v)
{
    Mock *m=v;
    if(m->index==0u){
        m->pp[0]=19u;
        if(m->mode==1u)m->frame=3199u;    /* underflow on old unsigned diff */
        if(m->mode==2u)m->frame=3201u;    /* still inside frame window */
        if(m->mode==3u)m->regs[15]=0u;   /* invalid CPU PC on next step */
        else m->regs[15]=0x0809E6BCu;
    }else if(m->index==1u){
        m->main_byte=0u;
        if(m->mode==2u)m->frame=3200u;   /* rollback after a frame advance */
        m->regs[15]=0x081C1236u;
    }else if(m->index==2u){
        m->frame=3202u;                 /* real, monotonic window end */
    }
    m->index++;
}
static void install(Mock *m,uint32_t mode)
{
    void (*step)(void *)=fake_step;
    uint32_t (*frame)(void *)=fake_frame;
    uint32_t (*read8)(void *,uint32_t,int)=fake_read8;
    uint32_t (*read32)(void *,uint32_t,int)=fake_read32;
    memset(m,0,sizeof *m);
    memcpy(m->abi+0x13e8,&step,sizeof step);
    memcpy(m->abi+0x1428,&frame,sizeof frame);
    memcpy(m->abi+0x1488,&read8,sizeof read8);
    memcpy(m->abi+0x1498,&read32,sizeof read32);
    m->mode=mode;m->frame=3200u;m->main_byte=2u;
    m->flags=4u;m->battlers=2u;m->pp[0]=20u;
    m->callback1=0x0808CBDDu;m->callback2=0x0808F225u;
    m->regs[15]=0x0806BD82u;m->regs[2]=10u;
    if(mode==4u)m->regs[15]=0u;
    if(mode==5u)m->regs[15]=0x0806BD83u;
}
static void trace(Mock *m,SG_OutcomeEdgeRun *run,SG_OutcomeEdge *events,
                  uint32_t cap,uint32_t frames)
{
    sg_trace_exact_outcome_pp_edges(m,m->regs,frames,100u,0u,
                                    events,cap,run);
}
static uint32_t count_kind(const SG_OutcomeEdge *events,
                           uint32_t count,uint32_t kind)
{
    uint32_t n=0;
    for(uint32_t i=0;i<count;i++)if(events[i].kind==kind)n++;
    return n;
}
int main(void)
{
    Mock m={0};
    SG_OutcomeEdgeRun run={0};
    SG_OutcomeEdge events[64]={0};
    install(&m,0u);trace(&m,&run,events,64u,2u);
    assert(run.status==1u&&run.guest_steps==3u);
    assert(run.start_frame==3200u&&run.end_frame==3202u);
    assert(count_kind(events,run.event_count,SG_PLAYER_EMIT)==1u);
    assert(count_kind(events,run.event_count,SG_PP_CHANGE)==1u);
    assert(count_kind(events,run.event_count,SG_INBATTLE)==1u);
    assert(events[0].pc==0x0806BD80u);

    install(&m,1u);trace(&m,&run,events,64u,2u);
    assert(run.status==5u&&run.end_frame==3199u);
    assert(run.guest_steps==1u);

    install(&m,2u);trace(&m,&run,events,64u,2u);
    assert(run.status==5u&&run.end_frame==3200u);
    assert(run.guest_steps==2u);

    install(&m,3u);trace(&m,&run,events,64u,2u);
    assert(run.status==6u&&run.guest_steps==1u);

    install(&m,4u);trace(&m,&run,events,64u,2u);
    assert(run.status==6u&&run.guest_steps==0u&&run.event_count==0u);

    install(&m,5u);trace(&m,&run,events,64u,2u);
    assert(run.status==6u&&run.guest_steps==0u);

    install(&m,0u);trace(&m,&run,events,1u,2u);
    assert(run.status==3u&&run.event_count==1u);
    install(&m,0u);trace(&m,&run,events,2049u,2u);
    assert(run.status==4u&&run.guest_steps==0u);
    install(&m,0u);trace(&m,&run,events,64u,10001u);
    assert(run.status==4u&&run.guest_steps==0u);

    install(&m,0u);
    memset(m.abi+0x13e8,0,sizeof(void (*)(void *)));
    trace(&m,&run,events,64u,2u);
    assert(run.status==4u&&run.guest_steps==0u);

    install(&m,0u);
    sg_trace_exact_outcome_pp_edges(&m,m.regs,2u,100u,SG_PP,
                                    events,64u,&run);
    assert(run.status==4u&&run.guest_steps==0u);

    assert(sg_original_thumb_pc(0x08000002u));
    assert(sg_original_thumb_pc(0x02000002u));
    assert(sg_original_thumb_pc(0x03008000u));
    assert(!sg_original_thumb_pc(0u));
    assert(!sg_original_thumb_pc(0x08000001u));
    assert(!sg_original_thumb_pc(0x06000002u));
    puts("PUBLIC_ORIGINAL_OUTCOME_OBSERVER: PASS frame and PC fail-closed fake-core tests");
    return 0;
}
