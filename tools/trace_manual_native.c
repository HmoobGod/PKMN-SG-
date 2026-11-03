/* 16266R9: passive tracing of original manual actor-0 battle reply/consumer.
   Not compiled into the game. No automatic action, hidden-foe reads or writes. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>

typedef struct {
 uint32_t pc,frame,r0,r1,r2,r3,r4,r6,pending;
 uint32_t own_reply_header,own_reply_payload,own_reply_valid;
} SG_ManualEvent;
typedef struct {uint32_t first_frame,last_frame,count,status;uint64_t steps;} SG_ManualStats;
#define EWRAM_BASE 0x02000000u
#define EWRAM_END 0x02040000u
static const uint32_t markers[]={
 0x0806bd82u, /* native EmitTwoReturnValues+2 */
 0x0806b372u, /* native CopyBufferData entry+2 */
 0x0806261eu, /* native reply completion+2 */
 0x080e5e5eu, /* original consumer restriction call+2 */
 0x08094332u, /* original validator result+2 */
 0x0809435eu, /* original slot commit+2 */
 0x08094376u, /* original move commit+2 */
 0x08094382u  /* original target commit+2 */
};
void sg_trace_original_manual(void *core,uint32_t *regs,uint32_t frames,uint32_t limit,
                              SG_ManualEvent *events,uint32_t cap,SG_ManualStats *stats){
 if(!core||!regs||!events||!stats)return;
 memset(stats,0,sizeof *stats);
 void(*step)(void*)=*(void(**)(void*))((char*)core+0x13e8);
 uint32_t(*frame)(void*)=*(uint32_t(**)(void*))((char*)core+0x1428);
 uint32_t(*read8)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1488);
 uint32_t(*read32)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1498);
 stats->first_frame=frame(core);
 for(uint32_t i=0;i<limit;i++){
  uint32_t f=frame(core);
  if(f-stats->first_frame>=frames){stats->status=1;break;}
  uint32_t pc=regs[15];
  unsigned matched=0;
  for(unsigned k=0;k<sizeof markers/sizeof markers[0];k++)
   if(pc==markers[k]){matched=1;break;}
  if(matched){
   /* Capture actor-0 events ONLY. Original opponents still run untouched. */
   unsigned actor0=(pc==0x0806bd82u && regs[0]==0 && regs[2]==10) ||
     (pc==0x0806b372u && regs[0]==0 && regs[1]==1 && regs[3]==6) ||
     (pc==0x0806261eu && regs[4]==0) ||
     (pc==0x080e5e5eu && regs[0]==0 && regs[6]==0) ||
     ((pc==0x08094332u || pc==0x0809435eu ||pc==0x08094376u ||
       pc==0x08094382u) && regs[6]==0);
   if(actor0){
    if(stats->count<cap){
     SG_ManualEvent *e=events+stats->count;
     *e=(SG_ManualEvent){.pc=pc-2u,.frame=f,.r0=regs[0],
       .r1=regs[1],.r2=regs[2],.r3=regs[3],.r4=regs[4],
       .r6=regs[6],.pending=read32(core,0x02001d2c,0)};
     if(pc==0x0806b372u){
      uint32_t src=regs[2];
      if(src>=EWRAM_BASE && src<=EWRAM_END-6){
       unsigned char b[6];
       for(unsigned j=0;j<6;j++)b[j]=(unsigned char)read8(core,src+j,0);
       e->own_reply_header=(uint32_t)b[0] | ((uint32_t)b[1]<<8);
       e->own_reply_payload=(uint32_t)b[2] | ((uint32_t)b[3]<<8) |
         ((uint32_t)b[4]<<16) | ((uint32_t)b[5]<<24);
       e->own_reply_valid=1;
      }
     }
    }
    stats->count++;
   }
  }
  step(core);
  stats->steps++;
 }
 stats->last_frame=frame(core);
 if(!stats->status)stats->status=2;
}