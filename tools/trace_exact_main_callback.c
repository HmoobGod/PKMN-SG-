/* Read-only original exact-ROM gMain callback observer. No ROM, RAM,
 * controller, enemy/partner, save, or input writes. 0x030055D4 was found
 * using the original Main key fields (+0x28,+0x2a,+0x2c,+0x2e) from
 * actual field directional key transitions. Never trust stale flags4. */
#include <stdint.h>
#include <string.h>
#define MAIN_BASE 0x030055D4u
typedef struct {
 uint32_t frame,pc,kind,before,after,r0,r1,r2,r3,r4,r5,r6,r7,
          flags,battlers,pending,main_state,inbattle;
} SG_MainEvent;
typedef struct {uint32_t status,start_frame,end_frame,count;uint64_t steps;} SG_MainStats;
void sg_observe_main_callback(void *core,uint32_t *regs,uint32_t frames,
                              uint64_t maxsteps,SG_MainEvent *rows,
                              uint32_t cap,SG_MainStats *out){
 if(!core||!regs||!rows||!out||cap==0)return;
 memset(out,0,sizeof *out);
 void(*step)(void*)=*(void(**)(void*))((char*)core+0x13e8);
 uint32_t(*frame)(void*)=*(uint32_t(**)(void*))((char*)core+0x1428);
 uint32_t(*read8)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1488);
 uint32_t(*read32)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1498);
 uint32_t old[3]={read32(core,MAIN_BASE,0),read32(core,MAIN_BASE+4,0),
                  read32(core,MAIN_BASE+8,0)};
 uint32_t state=read8(core,MAIN_BASE+0x438,0);
 out->start_frame=frame(core);
 for(uint64_t n=0;n<maxsteps;n++){
  uint32_t f=frame(core),pc=regs[15];
  if(f-out->start_frame>=frames){out->status=1;break;}
  uint32_t r[8];for(uint32_t j=0;j<8;j++)r[j]=regs[j];
  step(core);out->steps++;
  for(uint32_t k=0;k<3;k++){
   uint32_t now=read32(core,MAIN_BASE+4*k,0);
   if(old[k]==now)continue;
   if(out->count>=cap){out->status=3;break;}
   SG_MainEvent *e=&rows[out->count++];
   *e=(SG_MainEvent){f,pc-2,k+1,old[k],now,r[0],r[1],r[2],r[3],
     r[4],r[5],r[6],r[7],read32(core,0x02001AB4,0),
     read8(core,0x02001AB8,0),read32(core,0x02001D2C,0),
     read8(core,MAIN_BASE+0x438,0),read8(core,MAIN_BASE+0x439,0)};
   old[k]=now;
  }
  if(out->status==3)break;
  uint32_t now=read8(core,MAIN_BASE+0x438,0);
  if(now!=state){
   if(out->count>=cap){out->status=3;break;}
   SG_MainEvent *e=&rows[out->count++];
   *e=(SG_MainEvent){f,pc-2,4,state,now,r[0],r[1],r[2],r[3],
     r[4],r[5],r[6],r[7],read32(core,0x02001AB4,0),
     read8(core,0x02001AB8,0),read32(core,0x02001D2C,0),
     now,read8(core,MAIN_BASE+0x439,0)};
   state=now;
  }
  if(out->status==3)break;
 }
 if(!out->status)out->status=2;
 out->end_frame=frame(core);
}
