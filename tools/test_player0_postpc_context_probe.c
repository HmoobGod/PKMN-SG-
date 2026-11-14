/* PUBLIC synthetic fake-CPU continuation after PR80's PRE-POST_PC stop.
 * No commercial ROM, save, emulator, private trace or game input. */
#ifdef NDEBUG
#error "Post-PC continuation fixture must retain assertions"
#endif
#define main sg_original_copy_fixture_main
#include "test_original_player0_request_44byte_poststore.c"
#undef main
#include "alternate_mgba_postpc_context_probe.h"
#define SG_PUBLIC_THUMB_TARGET 0x0806B4C8u
static uint32_t post_mode,post_steps;
static void sg_fake_post_step(void *v){
 FakeCore *m=v;
 assert(m->regs[15]==POST_PC);
 post_steps++;
 /* The fake 0x4718 encodes BX r3: advance to r3 with Thumb bit
  * removed, not an invented constant unrelated to source operands. */
 m->regs[15]=m->regs[3]&~1u;
 if(post_mode==1u)m->pending=1u;
 if(post_mode==2u)m->buffer+=32u;
 if(post_mode==3u)m->ram[m->dest-EWRAM_BASE+9u]^=1u;
 if(post_mode==4u)m->frame=49u;
 if(post_mode==5u)m->regs[15]=POST_PC; /* mismatched BX target */
 if(post_mode==6u)m->regs[15]+=2u; /* another wrong successor */
}
static void sg_fresh_post(FakeCore *m,Proof *p){
 void (*guest_step)(void *)=sg_fake_post_step;
 install(m,0u);run(m,p,2u,1000u);
 assert(p->state==2u&&p->error==0u&&p->stores==44u);
 assert(m->regs[15]==POST_PC);
 m->regs[3]=SG_PUBLIC_THUMB_TARGET|1u; /* generated fake Thumb BX r3 */
 memcpy(m->abi+0x13e8,&guest_step,sizeof guest_step);
 post_steps=0u;post_mode=0u;
}
int main(void){
 static FakeCore m;Proof p={0};SgPostPcProbe out={0};
 sg_fresh_post(&m,&p);
 assert(sg_probe_postpc_once(&m,m.regs,&p,&out)==1);
 assert(out.attempted==1u&&out.observed==1u&&out.error==0u);
 assert(out.pc_before==POST_PC&&out.pc_after==SG_PUBLIC_THUMB_TARGET);
 assert(out.bx_operand_register==3u&&
        out.bx_expected_successor_pc==SG_PUBLIC_THUMB_TARGET);
 assert(out.frame_before==50u&&out.frame_after==50u);
 assert(out.pointer_before==m.buffer&&out.pointer_after==m.buffer);
 assert(out.pending_before==0u&&out.pending_after==0u);
 assert(out.opcode_before==0x4718u&&post_steps==1u);
 assert(out.engine_one_use_certified==0u&&
        out.native_pp_cause_certified==0u&&out.production_authorized==0u);
 assert(!sg_probe_postpc_once(&m,m.regs,&p,&out)&&post_steps==1u);
 for(uint32_t mode=1u;mode<=6u;mode++){
  memset(&out,0,sizeof out);sg_fresh_post(&m,&p);post_mode=mode;
  int ok=sg_probe_postpc_once(&m,m.regs,&p,&out);
  assert(post_steps==1u);
  if(mode<=2u){
   assert(ok&&out.observed==1u&&out.context_changed_unclassified==1u);
   assert(out.engine_one_use_certified==0u);
  }else if(mode==3u)assert(!ok&&out.error==6u&&!out.observed);
  else if(mode==4u)assert(!ok&&out.error==5u&&!out.observed);
  else assert(!ok&&out.error==8u&&!out.observed&&
              out.engine_one_use_certified==0u);
 }
 /* ALL preflight corruptions must return without advancing fake guest. */
 for(uint32_t bad=1u;bad<=10u;bad++){
  memset(&out,0,sizeof out);sg_fresh_post(&m,&p);
  if(bad==1u)p.stores=43u;
  if(bad==2u)m.regs[15]=POST_PC+2u;
  if(bad==3u)m.pending=1u;
  if(bad==4u)m.buffer+=32u;
  if(bad==5u)m.ram[m.dest-EWRAM_BASE+9u]^=1u;
  if(bad==6u)p.post_insn=0x1234u;
  if(bad==7u)memset(m.abi+0x13e8,0,sizeof(void (*)(void *)));
  if(bad==8u)m.regs[3]&=~1u; /* BX would switch to ARM state */
  if(bad==9u)m.regs[3]=0x02001235u; /* RAM-origin unsupported */
  if(bad==10u)m.regs[3]=0xFFFFFFFFu; /* out-of-ROM target */
  assert(!sg_probe_postpc_once(&m,m.regs,&p,&out));
  assert(out.attempted==1u&&out.observed==0u&&out.error!=0u);
  assert(post_steps==0u);
 }
 /* Thumb instruction decode negatives are separate from guest execution. */
 uint32_t reg=99u,pc=0u;
 assert(sg_public_thumb_bx_successor(0x4718u,m.regs,&reg,&pc)==0);
 m.regs[3]=SG_PUBLIC_THUMB_TARGET|1u;
 assert(sg_public_thumb_bx_successor(0x4718u,m.regs,&reg,&pc));
 assert(reg==3u&&pc==SG_PUBLIC_THUMB_TARGET);
 assert(!sg_public_thumb_bx_successor(0x4798u,m.regs,&reg,&pc)); /* BLX */
 assert(!sg_public_thumb_bx_successor(0x4778u,m.regs,&reg,&pc)); /* PC source */
 assert(!sg_public_thumb_bx_successor(0x471Au,m.regs,&reg,&pc)); /* malformed bits */
 assert(!sg_public_thumb_bx_successor(0x6818u,m.regs,&reg,&pc)); /* LDR */
 puts("PUBLIC_PLAYER0_POSTPC_THUMB_BX: PASS generated fake instruction/PC parity only");
 return 0;
}
