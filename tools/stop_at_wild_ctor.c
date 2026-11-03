#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef struct {uint32_t reason,frame,pc,flags,count,kind0,kind1,install0,install1; uint64_t steps;} SG_ConstructorWitness;
void sg_until_fresh_wild_constructor(void *core, uint32_t *regs, uint32_t frames, uint32_t maxsteps, SG_ConstructorWitness*out){
 if(!out)return;
 memset(out,0,sizeof *out);
 if(!core||!regs)return;
 void(*step)(void*)=*(void(**)(void*))((char*)core+0x13e8);
 uint32_t(*frame)(void*)=*(uint32_t(**)(void*))((char*)core+0x1428);
 uint32_t(*read8)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1488);
 uint32_t(*read32)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1498);
 uint32_t start=frame(core);
 for(uint32_t i=0;i<maxsteps;i++){
   if(frame(core)-start>=frames){out->reason=1;break;}
   if(regs[15]==0x0806ad48u){
    out->frame=frame(core);out->pc=regs[15]-2u;
    out->flags=read32(core,0x02001ab4,0);out->count=read8(core,0x02001ab8,0);
    out->kind0=read8(core,0x030001a4,0);out->kind1=read8(core,0x030001a5,0);
    out->install0=read32(core,0x03002e58,0);out->install1=read32(core,0x03002e5c,0);
    out->reason=(out->flags==4u && out->count==2u && out->kind0==0u && out->kind1==0u)?2u:3u;
    break;
   }
   step(core);out->steps++;
 }
 if(!out->reason)out->reason=4;
}