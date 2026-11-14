/* PUBLIC synthetic fake-CPU continuation after PR80's PRE-POST_PC stop.
 * No commercial ROM, save, emulator, private trace or game input. */
#ifdef NDEBUG
#error "Post-PC continuation fixture must retain assertions"
#endif
#define main sg_original_copy_fixture_main
#include "test_original_player0_request_44byte_poststore.c"
#undef main
#include "alternate_mgba_postpc_context_probe.h"
static uint32_t post_mode,post_steps;
static void sg_fake_post_step(void *v){
 FakeCore *m=v;
 assert(m->regs[15]==POST_PC);
 post_steps++;
 m->regs[15]=POST_PC+2u; /* hypothetical FAKE successor; NOT original ROM */
 if(post_mode==1u)m->pending=1u;
 if(post_mode==2u)m->buffer+=32u;
 if(post_mode==3u)m->ram[m->dest-EWRAM_BASE+9u]^=1u;
 if(post_mode==4u)m->frame=49u;
 if(post_mode==5u)m->regs[15]=POST_PC;
}
static void sg_fresh_post(FakeCore *m,Proof *p){
 void (*guest_step)(void *)=sg_fake_post_step;
 install(m,0u);run(m,p,2u,1000u);
 assert(p->state==2u&&p->error==0u&&p->stores==44u);
 assert(m->regs[15]==POST_PC);
 memcpy(m->abi+0x13e8,&guest_step,sizeof guest_step);
 post_steps=0u;post_mode=0u;
}
int main(void){
 static FakeCore m;Proof p={0};SgPostPcProbe out={0};
 sg_fresh_post(&m,&p);
 assert(sg_probe_postpc_once(&m,m.regs,&p,&out)==1);
 assert(out.attempted==1u&&out.observed==1u&&out.error==0u);
 assert(out.pc_before==POST_PC&&out.pc_after==POST_PC+2u);
 assert(out.frame_before==50u&&out.frame_after==50u);
 assert(out.pointer_before==m.buffer&&out.pointer_after==m.buffer);
 assert(out.pending_before==0u&&out.pending_after==0u);
 assert(out.opcode_before==0x4718u&&post_steps==1u);
 assert(out.engine_one_use_certified==0u&&
        out.native_pp_cause_certified==0u&&out.production_authorized==0u);
 assert(!sg_probe_postpc_once(&m,m.regs,&p,&out)&&post_steps==1u);
 for(uint32_t mode=1u;mode<=5u;mode++){
  memset(&out,0,sizeof out);sg_fresh_post(&m,&p);post_mode=mode;
  int ok=sg_probe_postpc_once(&m,m.regs,&p,&out);
  assert(post_steps==1u);
  if(mode<=2u){
   assert(ok&&out.observed==1u&&out.context_changed_unclassified==1u);
   assert(out.engine_one_use_certified==0u);
  }else if(mode==3u)assert(!ok&&out.error==6u&&!out.observed);
  else if(mode==4u)assert(!ok&&out.error==5u&&!out.observed);
  else assert(ok&&out.pc_after==POST_PC&&out.engine_one_use_certified==0u);
 }
 /* ALL preflight corruptions must return without advancing fake guest. */
 for(uint32_t bad=1u;bad<=7u;bad++){
  memset(&out,0,sizeof out);sg_fresh_post(&m,&p);
  if(bad==1u)p.stores=43u;
  if(bad==2u)m.regs[15]=POST_PC+2u;
  if(bad==3u)m.pending=1u;
  if(bad==4u)m.buffer+=32u;
  if(bad==5u)m.ram[m.dest-EWRAM_BASE+9u]^=1u;
  if(bad==6u)p.post_insn=0x1234u;
  if(bad==7u)memset(m.abi+0x13e8,0,sizeof(void (*)(void *)));
  assert(!sg_probe_postpc_once(&m,m.regs,&p,&out));
  assert(out.attempted==1u&&out.observed==0u&&out.error!=0u);
  assert(post_steps==0u);
 }
 puts("PUBLIC_PLAYER0_POSTPC_ONE_STEP: PASS synthetic only, no native certification");
 return 0;
}
