#include <stdint.h>
#include <stddef.h>
#include <string.h>

typedef struct {uint32_t pc,frame,r0,r1,r2,r3,r4,sp,lr;} Event;
typedef struct {uint32_t start_frame,end_frame,event_count,stop_reason; uint64_t steps;} Stats;
uint32_t sg_until_pc(void *core,uint32_t* regs,uint32_t target,uint32_t maxsteps) {
 if(!core||!regs) return 0;
 void(*step)(void*)=*(void(**)(void*))((char*)core+0x13e8);
 for(uint32_t i=0;i<maxsteps;i++){
  if(regs[15]==target)return i+1;
  step(core);
 }
 return 0;
}
void sg_trace_frames(void* core,uint32_t* regs,uint32_t frames,uint32_t maxsteps,Event* events,uint32_t capacity,Stats* result) {
 if(!core||!regs||!result)return;
 memset(result,0,sizeof *result);
 void(*step)(void*)=*(void(**)(void*))((char*)core+0x13e8);
 uint32_t(*frame)(void*)=*(uint32_t(**)(void*))((char*)core+0x1428);
 result->start_frame=frame(core);
 for(uint32_t i=0;i<maxsteps;i++){
  uint32_t fr=frame(core);
  if(fr-result->start_frame>=frames){result->stop_reason=1;break;}
  uint32_t pc=regs[15];
  if(pc==0x0806b372u||pc==0x0806b3c0u||pc==0x0806b3c8u||pc==0x0806bd82u||pc==0x0806261eu){
   if(result->event_count<capacity){Event*e=events+result->event_count;*e=(Event){.pc=pc-2,.frame=fr,.r0=regs[0],.r1=regs[1],.r2=regs[2],.r3=regs[3],.r4=regs[4],.sp=regs[13],.lr=regs[14]};}
   result->event_count++;
  }
  step(core);result->steps++;
 }
 result->end_frame=frame(core);
 if(result->stop_reason==0)result->stop_reason=2;
}