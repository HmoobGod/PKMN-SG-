/* Public FAKE core C->Python observer bridge: no commercial game input.
 * The exact original joint C observer is executed against deterministic
 * memory-only fixtures. Output is a PUBLIC SYNTHETIC JSON envelope, NOT
 * attested native CPU evidence, saved traces, or an actual original ROM.
 */
#ifdef NDEBUG
#error "Public C observer bridge requires enabled assertions"
#endif
#define SG_CONTEXT_MAIN sg_existing_fake_context_fixture_main
#include "test_exact_joint_player_terminal_context_c.c"
#undef SG_CONTEXT_MAIN
#include <inttypes.h>
#include <stdlib.h>

static const char *const field_names[]={
    "frame","step","pc","opcode","stage","kind","address","before",
    "after","slot","r0","r1","r2","r3","r4","flags","battlers",
    "pending","inbattle","callback1","callback2"
};
_Static_assert(sizeof(SG_JointEvent)==21u*sizeof(uint32_t),
               "observer event layout unexpected");

static void emit_event_json(const SG_JointEvent *ev)
{
    uint32_t fields[21];
    memcpy(fields,ev,sizeof fields); /* no pointer aliasing or fake fields */
    putchar('{');
    for(unsigned j=0;j<21u;j++)
        printf("%s\"%s\":%" PRIu32,j?",":"",field_names[j],fields[j]);
    putchar('}');
}

static void emit_pp(const uint32_t pp[4])
{
    printf("[%" PRIu32 ",%" PRIu32 ",%" PRIu32 ",%" PRIu32 "]",
           pp[0],pp[1],pp[2],pp[3]);
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    const char *mode=argv[1];
    Mock m={0};
    SG_JointRun out={0};
    SG_JointEvent e[64]={0};
    install(&m);
    if(strcmp(mode,"baseline")==0) { /* default */ }
    else if(strcmp(mode,"flags0")==0)m.flags=0;
    else if(strcmp(mode,"battlers0")==0)m.battlers=0;
    else if(strcmp(mode,"main0")==0)m.main_byte=0;
    else if(strcmp(mode,"no_pp")==0)m.pp[0]=19u;
    else if(strcmp(mode,"slot1_delta3")==0) {
        void (*step)(void *)=fake_step_slot1_delta;
        m.pp[0]=19u;
        memcpy(m.abi+0x13e8,&step,sizeof step);
    }else if(strcmp(mode,"main_bit0")==0) {
        void (*step)(void *)=fake_step_main_bit0;
        memcpy(m.abi+0x13e8,&step,sizeof step);
    }else return 2;

    sg_trace_exact_joint_player_terminal(&m,m.regs,2u,1000u,e,64u,&out);
    assert(out.status==1u&&out.steps==11u&&out.count<=64u);
    printf("{\"schema\":\"sg-public-synthetic-joint-c-v1\",\"mode\":\"%s\",",mode);
    printf("\"run\":{\"status\":%" PRIu32 ",\"start_frame\":%" PRIu32
           ",\"end_frame\":%" PRIu32 ",\"window_frames\":2"
           ",\"steps\":%llu,\"initial_main\":%" PRIu32
           ",\"final_main\":%" PRIu32 ",\"initial_cb1\":%" PRIu32
           ",\"final_cb1\":%" PRIu32 ",\"initial_cb2\":%" PRIu32
           ",\"final_cb2\":%" PRIu32 ",\"initial_pp\":",
           out.status,out.start_frame,out.end_frame,
           (unsigned long long)out.steps,out.initial_main,out.final_main,
           out.initial_cb1,out.final_cb1,out.initial_cb2,out.final_cb2);
    emit_pp(out.initial_pp);
    printf(",\"final_pp\":");
    emit_pp(out.final_pp);
    printf("},\"events\":[");
    for(uint32_t i=0;i<out.count;i++){
        if(i)putchar(',');
        emit_event_json(&e[i]);
    }
    puts("]}");
    return 0;
}
