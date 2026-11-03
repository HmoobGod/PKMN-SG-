/* ROM-free, read-only tracer. No command emission, no game memory writes. */
#include <stdint.h>
#include <string.h>
typedef struct {
 uint32_t result,start_frame,end_frame,player_installer,foe_installer,copy_frame;
 uint32_t actor,source,length,flags,count,kind0,kind1,completion0,completion1,pending,request_opcode;
 uint64_t steps;
} SG_RequestRun;
void sg_wait_player_copy(void *core,uint32_t *regs,uint32_t frames,uint32_t maxsteps,SG_RequestRun *out){
 if(!core || !regs || !out)return;
 memset(out,0,sizeof *out);
 void(*step)(void*)=*(void(**)(void*))((char*)core+0x13e8);
 uint32_t(*frame)(void*)=*(uint32_t(**)(void*))((char*)core+0x1428);
 uint32_t(*read8)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1488);
 uint32_t(*read32)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1498);
 out->start_frame=frame(core);
 for(uint32_t i=0;i<maxsteps;i++){
  uint32_t fr=frame(core);if(fr-out->start_frame>=frames){out->result=1;break;}
  uint32_t pc=regs[15];
  if(pc==0x08063d26u && regs[0]==0)out->player_installer++;
  if(pc==0x080619a2u && regs[0]==1)out->foe_installer++;
  if(pc==0x0806b372u && regs[0]==0 && regs[1]==0 && regs[3]==44){
   out->copy_frame=fr;out->actor=regs[0];out->source=regs[2];out->length=regs[3];
   out->flags=read32(core,0x02001ab4,0);out->count=read8(core,0x02001ab8,0);
   out->kind0=read8(core,0x030001a4,0);out->kind1=read8(core,0x030001a5,0);
   out->completion0=read32(core,0x03002e48,0);out->completion1=read32(core,0x03002e4c,0);
   out->pending=read32(core,0x02001d2c,0);
   out->request_opcode=(regs[2]>=0x02000000 && regs[2]<=0x02040000-44)?read8(core,regs[2],0):0;
   out->result=out->flags==4 && out->count==2 && out->kind0==1 && out->kind1==3 &&
      out->completion0==0x080625f9 && out->completion1==0x080616d9 && out->request_opcode==19 ?2:3;
   break;
  }
  step(core);out->steps++;
 }
 if(!out->result)out->result=4;
 out->end_frame=frame(core);
}