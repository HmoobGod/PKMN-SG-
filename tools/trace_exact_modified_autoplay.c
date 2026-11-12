/* Exact modified SoulGold original-controller replay observer; READ ONLY.
 * No ROM/save/guest memory mutation. Private inputs stay outside public git.
 */
#include <stdint.h>
#include <string.h>
typedef struct {
 uint32_t pc,frame,r0,r1,r2,r3,r4,r5,r6,pending,cursor,auto_slot;
 uint32_t reply_header,reply_payload,reply_valid;
} Event;
typedef struct {uint32_t start_frame,end_frame,count,status;uint64_t steps;} Stats;
static const uint32_t marker[]={
 0x08065b1a,0x09f1f002,0x09f1f9fe,0x08065eb6,0x0806bd82,
 0x0806b372,0x0806261e,0x080e5e5e,0x08094332,
 0x0809435e,0x08094376,0x08094382,0x0806449e,0x09f1d002
};
void sg_exact_trace(void *core,uint32_t *regs,uint32_t frames,
                    uint64_t maxsteps,Event *events,uint32_t cap,Stats *out){
 if(!core||!regs||!events||!out)return;
 memset(out,0,sizeof *out);
 void(*step)(void*)=*(void(**)(void*))((char*)core+0x13e8);
 uint32_t(*frame)(void*)=*(uint32_t(**)(void*))((char*)core+0x1428);
 uint32_t(*read8)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1488);
 uint32_t(*read32)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1498);
 out->start_frame=frame(core);
 for(uint64_t i=0;i<maxsteps;i++){
  uint32_t f=frame(core);
  if(f-out->start_frame>=frames){out->status=1;break;}
  uint32_t pc=regs[15];
  for(uint32_t k=0;k<sizeof(marker)/sizeof(marker[0]);k++)if(pc==marker[k]){
   if(out->count<cap){
    Event *e=&events[out->count];
    *e=(Event){pc-2u,f,regs[0],regs[1],regs[2],regs[3],regs[4],
       regs[5],regs[6],read32(core,0x02001d2c,0),read8(core,0x02001e54,0),0,0,0,0};
    uint32_t sel=read32(core,0x02001e90,0);
    if(sel>=0x02000000&&sel<0x0203fef0)
      e->auto_slot=read8(core,sel+0x106,0);
    if(pc==0x0806b372&&regs[0]==0&&regs[1]==1&&regs[3]==6){
     uint32_t src=regs[2];
     if(src>=0x02000000&&src<=0x02040000-6){
      e->reply_header=read8(core,src,0)|(read8(core,src+1,0)<<8);
      for(uint32_t t=0;t<4;t++)
        e->reply_payload|=read8(core,src+2+t,0)<<(8*t);
      e->reply_valid=1;
     }
    }
   }
   out->count++;break;
  }
  step(core);out->steps++;
 }
 out->end_frame=frame(core);
 if(!out->status)out->status=2;
}
