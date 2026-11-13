/* Bounded C-level FAKE core observer regressions; NO owner ROM is run.
 * Include existing public fake fixture to exercise the exact C observer with
 * the same original CPU marker, PP byte and Main/callback instrumentation.
 */
#define main original_joint_baseline_fixture_main
#include "test_exact_joint_player_terminal.c"
#undef main

static void observe(Mock *m,SG_JointRun *out,SG_JointEvent *events)
{
    sg_trace_exact_joint_player_terminal(m,m->regs,2,1000u,events,64u,out);
    assert(out->status==1u && out->steps==11u);
    assert(out->start_frame==3200u && out->end_frame==3202u);
}
static unsigned count_kind(const SG_JointEvent *e,uint32_t count,uint32_t kind)
{
    unsigned n=0;
    for(uint32_t i=0;i<count;i++)
        if(e[i].kind==kind)n++;
    return n;
}
static const SG_JointEvent *find_writer(const SG_JointEvent *e,uint32_t count)
{
    for(uint32_t i=0;i<count;i++)
        if(e[i].kind==SG_JOIN_PP_BYTE && e[i].pc==WRITER)return &e[i];
    return NULL;
}
static void assert_stable_core_observation(unsigned mode)
{
    Mock m={0};
    SG_JointRun run={0};
    SG_JointEvent event[64]={0};
    const SG_JointEvent *writer;
    install(&m);
    if(mode==1)m.flags=0u;       /* stale flags despite real writer PC */
    if(mode==2)m.battlers=0u;    /* no wild-single battler count */
    if(mode==3)m.main_byte=0u;  /* original Main already out of battle */
    if(mode==4)m.pp[0]=19u;     /* no actual PP mutation at writer PC */
    observe(&m,&run,event);
    assert(run.count<=64u);
    assert(count_kind(event,run.count,SG_JOIN_EMIT)==1u);
    assert(count_kind(event,run.count,SG_JOIN_CALLBACK1)==1u);
    assert(count_kind(event,run.count,SG_JOIN_CALLBACK2)==1u);
    assert(run.final_cb1==0x081C7589u && run.final_cb2==0x081C9FC5u);
    writer=find_writer(event,run.count);
    if(mode==4){
        assert(writer==NULL);
        assert(count_kind(event,run.count,SG_JOIN_PP_BYTE)==0u);
        assert(run.initial_pp[0]==19u && run.final_pp[0]==19u);
    }else{
        assert(writer!=NULL && writer->pc==WRITER);
        assert(writer->slot==0u && writer->before==20u && writer->after==19u);
        assert(count_kind(event,run.count,SG_JOIN_PP_BYTE)==1u);
        assert(writer->flags==(mode==1?0u:4u));
        assert(writer->battlers==(mode==2?0u:2u));
        assert(writer->inbattle==(mode==3?0u:2u));
    }
    /* A C trace records chronology and source context. The separate strict
     * Python audit decides whether these events may be attributed to
     * player0. No C fixture itself authorizes a move or production. */
    if(mode==3){
        assert(run.initial_main==0u && run.final_main==0u);
        assert(count_kind(event,run.count,SG_JOIN_INBATTLE)==0u);
    }else{
        assert(run.initial_main==2u && run.final_main==0u);
        assert(count_kind(event,run.count,SG_JOIN_INBATTLE)==1u);
    }
}
int main(void)
{
    assert(original_joint_baseline_fixture_main()==0);
    for(unsigned mode=0;mode<=4;mode++)
        assert_stable_core_observation(mode);
    puts("original joint C observer negative-context FAKE core PASS");
    return 0;
}
