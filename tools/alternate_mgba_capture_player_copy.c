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
} Proof;
static int ewram(uint32_t p, uint32_t n){return p>=EWRAM_BASE&&p<=EWRAM_END-n;}
void sg_capture_player_request(void* core,uint32_t* regs,uint32_t frames,uint32_t maxsteps,Proof*proof){
 if(!core||!regs||!proof)return;
 memset(proof,0,sizeof(*proof));
 void(*step)(void*)=*(void(**)(void*))((char*)core+0x13e8);
 uint32_t(*frame)(void*)=*(uint32_t(**)(void*))((char*)core+0x1428);
 uint32_t(*read8)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1488);
 uint32_t(*read32)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1498);
 proof->tag=0x16266007;
 proof->begin_frame=frame(core);
 for(uint32_t i=0;i<maxsteps;i++) {
  uint32_t fr=frame(core);
  if(fr-proof->begin_frame>=frames)break;
  uint32_t pc=regs[15];
  if(pc==ENTRY_PC && regs[0]==0 && regs[1]==0 && regs[3]==SRC_N){
   if(proof->state){proof->error=1;break;}
   uint32_t s=regs[2],buffer=read32(core,0x02001C6C,0),d=buffer+0x10;
   if(!ewram(s,SRC_N)||!ewram(d,SRC_N)||!((s+SRC_N<=d)||(d+SRC_N<=s))){proof->error=2;break;}
   if(read8(core,s,0)!=19u){proof->error=3;break;}
   proof->state=1;proof->actor=0;proof->direction=0;proof->length=44;
   proof->source=s;proof->dest=d;proof->entry_sp=regs[13];proof->entry_lr=regs[14];proof->entry_frame=fr;
   proof->pending_entry=read32(core,0x02001D2C,0);
   for(uint32_t k=0;k<SRC_N;k++)proof->source_before[k]=(uint8_t)read8(core,s+k,0);
  }
  if(proof->state==1 && pc==STORE_PC){
    uint32_t k=regs[1];
    if(k!=proof->stores||k>=SRC_N||regs[0]!=proof->dest||regs[4]!=proof->source ||
       (regs[3]&255u)!=proof->source_before[k]||regs[13]!=proof->entry_sp-8||
       regs[14]!=proof->entry_lr) {proof->error=4;break;}
    proof->store_indices[k]=k;proof->store_values[k]=(uint8_t)(regs[3]&255u);proof->stores++;
  }
  if(proof->state==1 && pc==POST_PC){
   proof->post_frame=fr;proof->post_sp=regs[13];proof->post_lr=regs[14];
   proof->pending_post=read32(core,0x02001D2C,0);
   proof->opcode_post=read8(core,proof->dest,0);
   if(proof->stores!=SRC_N||regs[1]!=SRC_N||regs[2]!=SRC_N||
      regs[0]!=proof->dest||regs[4]!=proof->source||
      fr!=proof->entry_frame||regs[13]!=proof->entry_sp-8||regs[14]!=proof->entry_lr){proof->error=5;break;}
   for(uint32_t k=0;k<SRC_N;k++){
     proof->source_after[k]=(uint8_t)read8(core,proof->source+k,0);
     proof->dest_after[k]=(uint8_t)read8(core,proof->dest+k,0);
     if(proof->source_before[k]!=proof->source_after[k]||proof->dest_after[k]!=proof->source_after[k]){proof->error=6;break;}
   }
   if(proof->error)break;
   proof->state=2;proof->total_steps=i+1;break;
  }
  step(core);proof->total_steps=i+1;
 }
 proof->end_frame=frame(core);
}