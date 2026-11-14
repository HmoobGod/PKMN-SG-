/* PUBLIC FAKE CPU ONLY: serialize the ACTUAL read-only original PP observer
 * events for strict offline v3 Python evidence verification. No owner ROM,
 * savestate, private trace, emulator path or real game is accessed here.
 */
#ifdef NDEBUG
#error "C-to-Python original PP proof must preserve runtime assertions"
#endif
#define main sg_unused_capture_safety_fixture_main
#include "test_exact_outcome_pp_capture_safety.c"
#undef main
#include <inttypes.h>

static uint32_t public_fake_instr_read8(void *v,uint32_t address,int unused)
{
    Mock *m=v;
    /* Deliberately mutate a fake instruction image at each CPU step:
     * only PRE-step instructions may be used for memory watcher rows. */
    if(address==0x0806BD80u)return m->index==0u?0x34u:0xA5u;
    if(address==0x0806BD81u)return m->index==0u?0x12u:0x5Au;
    if(address==0x0809E6BAu)return m->index==1u?0x0Eu:0xC3u;
    if(address==0x0809E6BBu)return m->index==1u?0x70u:0xD2u;
    return fake_read8(v,address,unused);
}
static void public_fake_step_mutate(void *v)
{
    Mock *m=v;
    fake_step(v);
    m->regs[5]+=1u;
    m->regs[6]+=2u;
    m->regs[7]^=0xFFu;
}
static void output_edge(const SG_OutcomeEdge *e)
{
    unsigned count=0;
#define FIELD(n) do { \
    if(count++)putchar(','); \
    printf("\"" #n "\":%" PRIu32,e->n); \
} while(0)
    putchar('{');
    FIELD(frame);FIELD(step);FIELD(pc);FIELD(opcode);
    FIELD(kind);FIELD(address);FIELD(before);FIELD(after);FIELD(slot);
    FIELD(r0);FIELD(r1);FIELD(r2);FIELD(r3);
    FIELD(r4);FIELD(r5);FIELD(r6);FIELD(r7);
    FIELD(flags);FIELD(battlers);FIELD(pending);
    FIELD(inbattle);FIELD(callback1);FIELD(callback2);
    putchar('}');
#undef FIELD
    assert(count==23u);
}
int main(void)
{
    Mock m={0};
    SG_OutcomeEdgeRun run={0};
    SG_OutcomeEdge edges[64]={0};
    uint32_t (*read8)(void *,uint32_t,int)=public_fake_instr_read8;
    void (*step)(void *)=public_fake_step_mutate;
    assert(sizeof(SG_OutcomeEdge)==23u*sizeof(uint32_t));
    install(&m,0u);
    m.regs[5]=0x87654321u;
    m.regs[6]=19u;
    m.regs[7]=0xBAD5CAFEu;
    memcpy(m.abi+0x1488,&read8,sizeof read8);
    memcpy(m.abi+0x13e8,&step,sizeof step);
    trace(&m,&run,edges,64u,2u);
    assert(run.status==1u&&run.guest_steps==3u&&run.event_count==3u);
    assert(edges[0].kind==SG_PLAYER_EMIT && edges[0].opcode==0x1234u);
    assert(edges[1].kind==SG_PP_CHANGE && edges[1].opcode==0x1234u);
    assert(edges[2].kind==SG_INBATTLE && edges[2].opcode==0x700Eu);
    printf("{\"status\":%" PRIu32 ",\"steps\":%" PRIu64 ",\"events\":[",
           run.status,run.guest_steps);
    for(uint32_t i=0;i<run.event_count;i++){
        if(i)putchar(',');
        output_edge(&edges[i]);
    }
    puts("]}");
    return 0;
}
