/* PUBLIC-ONLY optional one-step follow-up to a completed 44-byte copy.
 * Include only AFTER alternate_mgba_capture_player_copy.c supplies Proof.
 * No original ROM/save is required; test uses a fake CPU. This code does
 * not certify ownership, cancellation, native gameplay or production. */
#ifndef SG_PLAYER0_POSTPC_CONTEXT_PROBE_H
#define SG_PLAYER0_POSTPC_CONTEXT_PROBE_H
#include <stdint.h>
#include <string.h>
typedef struct {
 uint32_t attempted,observed,error;
 uint32_t pc_before,pc_after,opcode_before,frame_before,frame_after;
 uint32_t pointer_before,pointer_after,pending_before,pending_after;
 uint32_t context_changed_unclassified;
 uint32_t engine_one_use_certified,native_pp_cause_certified,production_authorized;
} SgPostPcProbe;
static int sg_probe_postpc_once(void *core,uint32_t *regs,
                                const Proof *copy,SgPostPcProbe *out){
 void (*guest_step)(void *)=0;
 uint32_t (*frame)(void *)=0;
 uint32_t (*read8)(void *,uint32_t,int)=0;
 uint32_t (*read32)(void *,uint32_t,int)=0;
 if(!out||out->attempted)return 0; /* ONE probe attempt per output ticket */
 memset(out,0,sizeof(*out));
 out->attempted=1;
 if(!core||!regs||!copy||copy->state!=2u||copy->error||
    copy->actor!=0u||copy->length!=SRC_N||copy->stores!=SRC_N||
    copy->total_steps!=SRC_N+1u||
    copy->entry_frame!=copy->post_frame||
    copy->entry_sp<8u||copy->post_sp!=copy->entry_sp-8u||
    copy->source<EWRAM_BASE||copy->dest<EWRAM_BASE+16u||
    !ewram(copy->source,SRC_N)||!ewram(copy->dest,SRC_N)){
  out->error=1;return 0;
 }
 memcpy(&guest_step,(char *)core+0x13e8,sizeof guest_step);
 memcpy(&frame,(char *)core+0x1428,sizeof frame);
 memcpy(&read8,(char *)core+0x1488,sizeof read8);
 memcpy(&read32,(char *)core+0x1498,sizeof read32);
 if(!guest_step||!frame||!read8||!read32){out->error=2;return 0;}
 out->pc_before=regs[15];
 out->frame_before=frame(core);
 out->pointer_before=read32(core,0x02001C6Cu,0);
 out->pending_before=read32(core,0x02001D2Cu,0);
 out->opcode_before=sg_thumb_halfword(core,read8,POST_PC);
 if(out->pc_before!=POST_PC||
    out->frame_before!=copy->post_frame||
    out->pointer_before!=copy->dest-16u||
    out->pending_before!=copy->pending_entry||
    out->pending_before!=copy->pending_post||
    out->opcode_before!=copy->post_insn||
    out->opcode_before==0u||
    regs[13]!=copy->post_sp||regs[14]!=copy->post_lr){
  out->error=3;return 0;
 }
 for(uint32_t i=0;i<SRC_N;i++){
  if((read8(core,copy->source+i,0)&255u)!=copy->source_before[i]||
     (read8(core,copy->dest+i,0)&255u)!=copy->dest_after[i]||
     copy->dest_after[i]!=copy->source_before[i]){
    out->error=4;return 0;
  }
 }
 /* Exactly ONE CPU step, never a host input, guest RAM write or retry.
  * The poststep state may be a legitimate transition: record it as
  * UNKNOWN rather than inventing an engine-owned one-use request. */
 guest_step(core);
 out->pc_after=regs[15];
 out->frame_after=frame(core);
 out->pointer_after=read32(core,0x02001C6Cu,0);
 out->pending_after=read32(core,0x02001D2Cu,0);
 out->context_changed_unclassified=
   (out->pointer_after!=out->pointer_before||
    out->pending_after!=out->pending_before)?1u:0u;
 if(out->frame_after<out->frame_before){
  out->error=5;return 0;
 }
 for(uint32_t i=0;i<SRC_N;i++){
  if((read8(core,copy->source+i,0)&255u)!=copy->source_before[i]||
     (read8(core,copy->dest+i,0)&255u)!=copy->dest_after[i]){
    out->error=6;return 0;
  }
 }
 out->observed=1u; /* a single *synthetic* continuation step only */
 return 1;
}
#endif
