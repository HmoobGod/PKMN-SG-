/* Public FAKE original-outcome original Thumb opcode capture:
 * uses actual C observer inherited from read-only PR56.
 * No commercial ROM, save, emulator, guest writes or native promotion. */
#ifdef NDEBUG
#error "Original CPU opcode fake-core assertions must not be disabled"
#endif
#define main sg_existing_public_outcome_safety_main
#include "test_exact_outcome_pp_capture_safety.c"
#undef main

static uint32_t fake_opcode_read8(void *v,uint32_t addr,int unused)
{
    if(addr==0x0806BD80u)return 0x34u;
    if(addr==0x0806BD81u)return 0x12u;
    if(addr==0x0809E6BAu)return 0x0Eu;
    if(addr==0x0809E6BBu)return 0x70u;
    return fake_read8(v,addr,unused);
}
int main(void)
{
    Mock m={0};
    SG_OutcomeEdgeRun run={0};
    SG_OutcomeEdge events[64]={0};
    uint32_t (*read8)(void *,uint32_t,int)=fake_opcode_read8;
    assert(sizeof(SG_OutcomeEdge)==23u*sizeof(uint32_t));
    assert(sg_existing_public_outcome_safety_main()==0);
    install(&m,0u);
    /* Real read-only C recorder must capture higher source-register values
     * from the PRE-step CPU snapshot, never infer them from after RAM. */
    m.regs[5]=0x87654321u;
    m.regs[6]=19u;
    m.regs[7]=0xBAD5CAFEu;
    memcpy(m.abi+0x1488,&read8,sizeof read8);
    trace(&m,&run,events,64u,2u);
    assert(run.status==1u&&run.guest_steps==3u);
    assert(run.event_count>=3u);
    assert(events[0].kind==SG_PLAYER_EMIT);
    assert(events[0].pc==0x0806BD80u);
    assert(events[0].opcode==0x1234u);
    int saw_writer=0,saw_post=0;
    for(uint32_t i=0;i<run.event_count;i++){
        assert(events[i].opcode<=0xFFFFu);
        assert(events[i].r5==0x87654321u&&events[i].r6==19u&&
               events[i].r7==0xBAD5CAFEu);
        if(events[i].kind==SG_PP_CHANGE){
            saw_writer++;
            assert(events[i].pc==0x0806BD80u);
            assert(events[i].opcode==0x1234u);
            assert(events[i].before==20u&&events[i].after==19u);
        }
        if(events[i].kind==SG_INBATTLE){
            saw_post++;
            assert(events[i].pc==0x0809E6BAu);
            assert(events[i].opcode==0x700Eu);
            assert(events[i].before==2u&&events[i].after==0u);
        }
    }
    assert(saw_writer==1&&saw_post==1);
    puts("PUBLIC_OUTCOME_OPCODE_V2: PASS real C original event CPU opcode capture on FAKE core");
    return 0;
}
