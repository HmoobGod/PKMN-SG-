/* Public original joint actor0/PP/Main observer chronology and PC contract.
 * Run real C observer only against existing in-memory FAKE core; never run
 * original SoulGold ROM, savestate, or guest emulator from public CI. */
#ifdef NDEBUG
#error "Joint chronology tests require enabled assertions"
#endif
#define main sg_original_joint_fake_baseline_main
#include "test_exact_joint_player_terminal.c"
#undef main

static void fake_step_in_window_rollback(void *v)
{
    Mock *m=v;
    uint32_t prev=m->index;
    fake_step(v);
    if(prev==0u)m->frame=3201u;
    if(prev==1u)m->frame=3200u; /* frame stays >= start, but goes BACK */
}
static void fake_step_invalid_pc_after_one(void *v)
{
    Mock *m=v;
    uint32_t prev=m->index;
    fake_step(v);
    if(prev==0u)m->regs[15]=0u;
}
static void set_step(Mock *m,void (*step)(void *))
{
    memcpy(m->abi+0x13e8,&step,sizeof step);
}
static void call_observer(Mock *m,SG_JointRun *out,SG_JointEvent ev[64],
                          uint32_t frames,uint32_t cap)
{
    sg_trace_exact_joint_player_terminal(m,m->regs,frames,1000,ev,cap,out);
}
int main(void)
{
    Mock m={0};SG_JointRun out={0};SG_JointEvent e[64]={0};
    assert(sg_original_joint_fake_baseline_main()==0);

    install(&m);
    set_step(&m,fake_step_in_window_rollback);
    call_observer(&m,&out,e,2u,64u);
    assert(out.status==5u&&out.steps==2u&&out.end_frame==3200u);
    assert(out.count>=2u); /* Marker observations do NOT certify completion. */

    install(&m);
    m.regs[15]=0u;
    call_observer(&m,&out,e,2u,64u);
    assert(out.status==6u&&out.steps==0u&&out.count==0u);

    install(&m);
    m.regs[15]=0x0806BD83u; /* odd Thumb program counter */
    call_observer(&m,&out,e,2u,64u);
    assert(out.status==6u&&out.steps==0u&&out.count==0u);

    install(&m);
    m.regs[15]=0x03000002u; /* unapproved RAM PC, no ROM opcode parity */
    call_observer(&m,&out,e,2u,64u);
    assert(out.status==6u&&out.steps==0u&&out.count==0u);

    install(&m);
    set_step(&m,fake_step_invalid_pc_after_one);
    call_observer(&m,&out,e,2u,64u);
    assert(out.status==6u&&out.steps==1u);
    assert(out.count==1u); /* first emitter not a completed replay */

    install(&m);
    call_observer(&m,&out,e,10001u,64u);
    assert(out.status==4u&&out.steps==0u);

    install(&m);
    call_observer(&m,&out,e,2u,1025u);
    assert(out.status==4u&&out.steps==0u);

    puts("PUBLIC_JOINT_CHRONOLOGY: PASS original C actor0/PP frame and CPU PC guards");
    return 0;
}
