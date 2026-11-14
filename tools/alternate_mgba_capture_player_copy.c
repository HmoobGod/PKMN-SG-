#include <stdint.h>
#include <stddef.h>
#include <string.h>
#define SRC_N 44u
#define EWRAM_BASE 0x02000000u
#define EWRAM_END  0x02040000u
#define ENTRY_PC 0x0806B372u
#define STORE_PC 0x0806B3C0u
#define POST_PC  0x0806B3C8u
typedef struct {
 uint32_t state,error,begin_frame,end_frame,entry_frame,post_frame;
 uint32_t source,dest,actor,direction,length,entry_sp,entry_lr,post_sp,post_lr;
 uint32_t stores,pending_entry,pending_post,opcode_post;
 uint32_t total_steps,tag;
 uint8_t source_before[44],source_after[44],dest_after[44],store_values[44];
 uint32_t store_indices[44];
 /* v2 evidence: observed destination byte before EACH stepped store. */
 uint8_t dest_before[44];
 /* v3 public observer: PRE-step Thumb halfwords, NOT private attestation. */
 uint32_t entry_insn, store_insn, post_insn;
} Proof;
static int ewram(uint32_t p, uint32_t n){return p>=EWRAM_BASE&&p<=EWRAM_END-n;}
static uint32_t sg_thumb_halfword(void *core,
    uint32_t (*read8)(void *,uint32_t,int), uint32_t pc){
 return (read8(core,pc,0)&255u)|((read8(core,pc+1u,0)&255u)<<8);
}
void sg_capture_player_request(void* core,uint32_t* regs,uint32_t frames,uint32_t maxsteps,Proof*proof){
 if(!core||!regs||!proof)return;
 memset(proof,0,sizeof(*proof));
 void(*step)(void*)=0;
 uint32_t(*frame)(void*)=0;
 uint32_t(*read8)(void*,uint32_t,int)=0;
 uint32_t(*read32)(void*,uint32_t,int)=0;
 /* Host ABI offsets are not necessarily pointer-aligned. Never dereference
  * an unaligned function-pointer slot or call a missing core callback. */
 memcpy(&step,(char*)core+0x13e8,sizeof step);
 memcpy(&frame,(char*)core+0x1428,sizeof frame);
 memcpy(&read8,(char*)core+0x1488,sizeof read8);
 memcpy(&read32,(char*)core+0x1498,sizeof read32);
 proof->tag=0x16266007;
 if(!step||!frame||!read8||!read32||!frames||frames>10000u||
    !maxsteps||maxsteps>10000000u){proof->error=8;return;}
 proof->begin_frame=frame(core);
 uint32_t last_frame=proof->begin_frame;
 for(uint32_t i=0;i<maxsteps;i++) {
  uint32_t fr=frame(core);
  if(fr<proof->begin_frame||fr<last_frame){proof->error=9;break;}
  if(fr-proof->begin_frame>=frames)break;
  last_frame=fr;
  uint32_t pc=regs[15];
  uint32_t verify_store=0,verify_index=0,verify_value=0,verify_before=0;
  if(pc==ENTRY_PC && regs[0]==0 && regs[1]==0 && regs[3]==SRC_N){
   if(proof->state){proof->error=1;break;}
   uint32_t s=regs[2],buffer=read32(core,0x02001C6C,0),d;
   /* Reject pointer arithmetic wraparound *before* computing buffer+16.
    * A forged buffer 0x01FFFFF0 must never alias valid EWRAM. */
   if(buffer<EWRAM_BASE||buffer>EWRAM_END-(0x10u+SRC_N)){
       proof->error=2;break;
   }
   d=buffer+0x10u;
   if(!ewram(s,SRC_N)||!ewram(d,SRC_N)||!((s+SRC_N<=d)||(d+SRC_N<=s))){proof->error=2;break;}
   if(read8(core,s,0)!=19u){proof->error=3;break;}
   proof->state=1;proof->actor=0;proof->direction=0;proof->length=44;
   proof->source=s;proof->dest=d;proof->entry_sp=regs[13];proof->entry_lr=regs[14];proof->entry_frame=fr;
   proof->pending_entry=read32(core,0x02001D2C,0);
   proof->entry_insn=sg_thumb_halfword(core,read8,ENTRY_PC);
   if(!proof->entry_insn){proof->error=11;break;}
   for(uint32_t k=0;k<SRC_N;k++)proof->source_before[k]=(uint8_t)read8(core,s+k,0);
  }
  if(proof->state==1 && pc==STORE_PC){
    uint32_t k=regs[1];
    if(k!=proof->stores||k>=SRC_N||regs[0]!=proof->dest||regs[4]!=proof->source ||
       (regs[3]&255u)!=proof->source_before[k]||regs[13]!=proof->entry_sp-8||
       regs[14]!=proof->entry_lr) {proof->error=4;break;}
    uint32_t insn=sg_thumb_halfword(core,read8,STORE_PC);
    if(!insn || (proof->stores && insn!=proof->store_insn)){
      proof->error=11;break;
    }
    proof->store_insn=insn;
    /* The STORE_PC marker is pre-instruction. Only count the store
     * AFTER the real CPU step and after checking the actual destination
     * byte, not merely the pre-step register values. This still does not
     * authenticate a private ROM opcode and cannot prove a store when the
     * old byte already equaled the new one. */
    verify_store=1;verify_index=k;verify_value=regs[3]&255u;
    verify_before=read8(core,proof->dest+k,0)&255u;
    /* A same-value poststep read cannot demonstrate that this CPU step
     * changed memory: fail closed rather than assert a witnessed store. */
    if(verify_before==verify_value){proof->error=10;break;}
  }
  if(proof->state==1 && pc==POST_PC){
   proof->post_frame=fr;proof->post_sp=regs[13];proof->post_lr=regs[14];
   proof->pending_post=read32(core,0x02001D2C,0);
   proof->opcode_post=read8(core,proof->dest,0);
   proof->post_insn=sg_thumb_halfword(core,read8,POST_PC);
   if(!proof->post_insn||!proof->entry_insn||!proof->store_insn){
      proof->error=11;break;
   }
   if(proof->stores!=SRC_N||regs[1]!=SRC_N||regs[2]!=SRC_N||
      regs[0]!=proof->dest||regs[4]!=proof->source||
      fr!=proof->entry_frame||regs[13]!=proof->entry_sp-8||regs[14]!=proof->entry_lr){proof->error=5;break;}
   for(uint32_t k=0;k<SRC_N;k++){
     proof->source_after[k]=(uint8_t)read8(core,proof->source+k,0);
     proof->dest_after[k]=(uint8_t)read8(core,proof->dest+k,0);
     if(proof->source_before[k]!=proof->source_after[k]||proof->dest_after[k]!=proof->source_after[k]){proof->error=6;break;}
   }
   if(proof->error)break;
   /* POST_PC was observed before a CPU step: report the exact number
    * of instructions actually stepped, not an extra imaginary step. */
   proof->state=2;proof->total_steps=i;break;
  }
  step(core);proof->total_steps=i+1;
  if(verify_store){
    uint32_t observed_after=read8(core,proof->dest+verify_index,0)&255u;
    if(observed_after!=verify_value||observed_after==verify_before){
      proof->error=7;break;
    }
    /* Do not accept a final 44-byte match if an earlier copied byte
     * was corrupted and later restored between store observations.
     * All reads are passive; only the fake guest in tests mutates RAM. */
    for(uint32_t j=0;j<verify_index;j++){
      if((read8(core,proof->dest+j,0)&255u)!=proof->source_before[j]){
        proof->error=12;break;
      }
    }
    if(proof->error)break;
    /* A transient source-buffer mutation could similarly disappear by
     * POST_PC, evading only entry/post source comparisons. */
    for(uint32_t j=0;j<SRC_N;j++){
      if((read8(core,proof->source+j,0)&255u)!=proof->source_before[j]){
        proof->error=13;break;
      }
    }
    if(proof->error)break;
    proof->dest_before[verify_index]=(uint8_t)verify_before;
    proof->store_indices[verify_index]=verify_index;
    proof->store_values[verify_index]=(uint8_t)verify_value;
    proof->stores++;
  }
 }
 proof->end_frame=frame(core);
 if(proof->end_frame<proof->begin_frame||proof->end_frame<last_frame){
    proof->error=9;proof->state=0;
 }
}