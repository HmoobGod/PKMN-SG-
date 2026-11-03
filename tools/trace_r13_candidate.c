/* R13 lab read-only timeline: original controller + original byte protocol,
 * new temporary ROM fixture guard and original native accept/commit events.
 * The observer NEVER writes emulated game memory or buttons.
 */
#include <stdint.h>
#include <string.h>
typedef struct {
 uint32_t pc,frame,r0,r1,r2,r3,r4,r5,r6,pending,cursor,auto_slot;
 uint32_t reply_header,reply_payload,reply_valid;
} E;
typedef struct {uint32_t start_frame,end_frame,count,status;uint64_t steps;} S;
static const uint32_t marker[]={
 0x09f20014,/* r0 from original sg_run_diagnostic */
 0x09f2001e,/* new candidate block */
 0x09f2d002,/* fixture guard entry */
 0x09f20024,/* fixture guard result */
 0x09f20034,/* lab auto route */
 0x09f20048,/* manual route */
 0x08065b1a,/* native auto preflight entry */
 0x08065eb6,/* original auto selection entry */
 0x0806bd82,/* original emitter */
 0x0806b372,/* native reply copy entry */
 0x0806261e,/* reply completion */
 0x080e5e5e,/* consumer restriction check */
 0x08094332,/* validator result */
 0x0809435e,/* slot commit */
 0x08094376,/* move commit */
 0x08094382,/* target commit */
 0x0806449e /* original manual move menu */
};
void sg_r13_trace(void *core,uint32_t *regs,uint32_t frames,uint64_t limit,E *events,uint32_t cap,S *out){
 if(!core||!regs||!events||!out)return;
 memset(out,0,sizeof *out);
 void(*step)(void*)=*(void(**)(void*))((char*)core+0x13e8);
 uint32_t(*frame)(void*)=*(uint32_t(**)(void*))((char*)core+0x1428);
 uint32_t(*read8)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1488);
 uint32_t(*read32)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1498);
 out->start_frame=frame(core);
 for(uint64_t i=0;i<limit;i++){
  uint32_t f=frame(core);
  if(f-out->start_frame>=frames){out->status=1;break;}
  uint32_t pc=regs[15];
  for(uint32_t k=0;k<sizeof(marker)/sizeof(marker[0]);k++)if(pc==marker[k]){
   if(out->count<cap){E *e=&events[out->count];*e=(E){
     pc-2u,f,regs[0],regs[1],regs[2],regs[3],regs[4],regs[5],regs[6],
     read32(core,0x02001d2c,0),read8(core,0x02001e54,0),0,0,0,0};
    uint32_t sel=read32(core,0x02001e90,0);
    if(sel>=0x02000000 && sel<0x0203fef0)e->auto_slot=read8(core,sel+0x106,0);
    if(pc==0x0806b372u && regs[0]==0u && regs[1]==1u && regs[3]==6u){
      uint32_t src=regs[2];
      if(src>=0x02000000u && src<=0x02040000u-6u){
        uint32_t b0=read8(core,src,0),b1=read8(core,src+1u,0);
        e->reply_header=b0|(b1<<8);
        for(unsigned t=0;t<4;t++)e->reply_payload|=read8(core,src+2u+t,0)<<(8u*t);
        e->reply_valid=1u;
      }
    }
   }out->count++;break;
  }
  step(core);out->steps++;
 }
 out->end_frame=frame(core);if(!out->status)out->status=2;
}