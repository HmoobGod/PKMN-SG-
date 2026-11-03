/* Read-only original-engine follow-up from a fixture first accepted in-ROM move.
 * Stops before the next actor0 request copy/guard or manual move chooser.
 * Never touches emulator memory or injects commands.
 */
#include <stdint.h>
#include <string.h>
struct SG_SecondWatch {
 uint32_t kind, start_frame, end_frame, pc, pending, pp0, pp1, player_emit, guard, manual, next_copy;
 uint64_t guest_steps;
};
void sg_watch_second(void *core,uint32_t *regs,uint32_t frames,uint64_t cap,struct SG_SecondWatch *out){
 if(!core||!regs||!out)return;
 memset(out,0,sizeof(*out));
 void(*step)(void*)=*(void(**)(void*))((char*)core+0x13e8);
 uint32_t(*fr)(void*)=*(uint32_t(**)(void*))((char*)core+0x1428);
 uint32_t(*r8)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1488);
 uint32_t(*r32)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1498);
 out->start_frame=fr(core);
 for(uint64_t i=0;i<cap;i++){
  uint32_t f=fr(core),pc=regs[15];
  if(f-out->start_frame>=frames){out->kind=1;break;}
  if(pc==0x0806b372u && regs[0]==0 && regs[1]==0 && regs[3]==44){out->kind=2;out->next_copy++;break;}
  if(pc==0x09f2d002u){out->kind=3;out->guard++;break;}
  if(pc==0x0806bd82u && regs[0]==0 && regs[2]==10){out->kind=4;out->player_emit++;break;}
  if(pc==0x0806449eu){out->kind=5;out->manual++;break;}
  step(core);out->guest_steps++;
 }
 out->end_frame=fr(core);out->pc=regs[15];out->pending=r32(core,0x02001d2c,0);
 out->pp0=r8(core,0x02001ecc+37,0);out->pp1=r8(core,0x02001ecc+38,0);
}