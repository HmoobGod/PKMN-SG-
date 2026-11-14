/* Public FAKE original-outcome original Thumb opcode capture:
 * uses actual C observer inherited from read-only PR56.
 * No commercial ROM, save, emulator, guest writes or native promotion. */
#ifdef NDEBUG
#error "Original CPU opcode fake-core assertions must not be disabled"
#endif
#define main sg_existing_public_outcome_safety_main
#include "test_exact_outcome_pp_capture_safety.c"
#undef main

/* Public FAKE source changes its halfwords AFTER the CPU step.
 * It deliberately exaggerates self-modification to distinguish a true
 * captured PRE-step instruction from a post-step memory bus read. */
static uint32_t fake_opcode_read8(void *v,uint32_t addr,int unused)
{
    Mock *m=v;
    if(addr==0x0806BD80u)return m->index==0u ? 0x34u : 0xA5u;
    if(addr==0x0806BD81u)return m->index==0u ? 0x12u : 0x5Au;
    if(addr==0x0809E6BAu)return m->index==1u ? 0x0Eu : 0xC3u;
    if(addr==0x0809E6BBu)return m->index==1u ? 0x70u : 0xD2u;
    return fake_read8(v,addr,unused);
}
static void fake_opcode_step_and_mutate_regs(void *v)
{
    Mock *m=v;
    fake_step(v);
    m->regs[5]+=1u;
    m->regs[6]+=2u;
    m->regs[7]^=0xFFu;
}
int main(void)
{
    Mock m={0};
    SG_OutcomeEdgeRun run={0};
    SG_OutcomeEdge events[64]={0};
    uint32_t (*read8)(void *,uint32_t,int)=fake_opcode_read8;
    void (*step)(void *)=fake_opcode_step_and_mutate_regs;
    assert(sizeof(SG_OutcomeEdge)==23u*sizeof(uint32_t));
    assert(sg_existing_public_outcome_safety_main()==0);
    install(&m,0u);
    /* Real read-only C recorder must capture higher source-register values
     * from the PRE-step CPU snapshot, never infer them from after RAM. */
    m.regs[5]=0x87654321u;
    m.regs[6]=19u;
    m.regs[7]=0xBAD5CAFEu;
    memcpy(m.abi+0x1488,&read8,sizeof read8);
    memcpy(m.abi+0x13e8,&step,sizeof step);
    trace(&m,&run,events,64u,2u);
    assert(run.status==1u&&run.guest_steps==3u);
    assert(run.event_count>=3u);
    assert(events[0].kind==SG_PLAYER_EMIT);
    assert(events[0].pc==0x0806BD80u);
    assert(events[0].opcode==0x1234u);
    int saw_writer=0,saw_post=0;
    for(uint32_t i=0;i<run.event_count;i++){
        assert(events[i].opcode<=0xFFFFu);
        /* Each event must preserve the snapshot from BEFORE its OWN
         * step, not the register values changed by fake step. */
        uint32_t k=events[i].step;
        assert(events[i].r5==0x87654321u+k &&
               events[i].r6==19u+2u*k &&
               events[i].r7==(0xBAD5CAFEu^(k&1u ? 0xFFu : 0u)));
        if(events[i].kind==SG_PP_CHANGE){
            saw_writer++;
            assert(events[i].pc==0x0806BD80u);
            /* The fake opcode has already changed to 0x5AA5
             * by now. This checks that the ORIGINAL halfword was
             * sampled BEFORE the memory write step. */
            assert(events[i].opcode==0x1234u);
            assert(events[i].before==20u&&events[i].after==19u);
        }
        if(events[i].kind==SG_INBATTLE){
            saw_post++;
            assert(events[i].pc==0x0809E6BAu);
            /* The second opcode mutates to 0xD2C3 after step.
             * A post-step recapture would be rejected here. */
            assert(events[i].opcode==0x700Eu);
            assert(events[i].before==2u&&events[i].after==0u);
        }
    }
    assert(saw_writer==1&&saw_post==1);
    assert(m.index==3u);
    puts("PUBLIC_OUTCOME_OPCODE_V3_PRESTEP: PASS fake mutable CPU instructions and registers; source observer freezes both before every step");
    return 0;
}
