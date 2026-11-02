#include "snapshot.h"
#define R8(a) (*(volatile const uint8_t *)(uintptr_t)(a))
#define R16(a) (*(volatile const uint16_t *)(uintptr_t)(a))
#define R32(a) (*(volatile const uint32_t *)(uintptr_t)(a))
uint32_t sg_capture_diagnostic(uint32_t actor,struct sg_diagnostic_snapshot *out) {
 if (!out)return 4;
 *out=(struct sg_diagnostic_snapshot){0};
 if (actor!=0 && actor!=2)return 1;
 uint32_t count=R8(0x02001ab8);
 if (actor>=count || count>4)return 2;
 uint32_t kind=R8(0x030001a4+actor),completion=R32(0x03002e48+actor*4);
 /* Exclude known non-player controller classes BEFORE move/pointer reads.
    This observed class check is not positive owner authorization. */
 if(kind!=1 || completion!=0x080625f9)return 5;
 /* Exact observed lab contexts only. This is an exclusion guard, not
    positive owner, mode, target or action authorization. Unknown flags fail. */
 uint32_t flags=R32(0x02001ab4);
 if (!((flags==4 && count==2) || (flags==13 && count==4)))return 6;
 for (uint32_t i=0;i<count;i++) {
  if (R8(0x02001b58+i)!=i)return 6;
  uint32_t expected_kind=(i&1)?3:1;
  uint32_t expected_completion=(i&1)?0x080616d9:0x080625f9;
  if(R8(0x030001a4+i)!=expected_kind ||
     R32(0x03002e48+i*4)!=expected_completion)return 6;
 }
 uint32_t present=((1u<<count)-1u)&~R8(0x02001d42);
 if (!(present&(1u<<actor)))return 6;
 uint32_t sel=R32(0x02001e90),res=R32(0x02001c6c);
 /* Conservative half-open EWRAM bounds; validate before derived reads. */
 if (sel<0x02000000 || sel>0x02040000-0x10a || res<0x02000000 || res>0x02040000-(actor*512+28) || (res&1))return 3;
 uint32_t live=0x02001ecc+actor*152;
 out->actor=actor;out->count=count;out->kind=kind;
 out->completion=completion;out->run=R32(0x03002e58+actor*4);
 out->slot=R8(sel+0x106+actor);out->position=R8(0x02001b58+actor);
 for (uint32_t i=0;i<4;i++) {
  out->moves[i]=R16(live+12+2*i);out->buffer_moves[i]=R16(res+actor*512+20+2*i);out->pp[i]=R8(live+37+i);
 }
 out->battle_type_flags=flags;
 out->present_mask=present;
 uint32_t packed_moves=R32(live+0x6c);
 out->disabled_move=(packed_moves>>11)&0x3ff;
 out->encored_move=(packed_moves>>21)&0x3ff;
 out->encore_timer=(R32(live+0x74)>>15)&7;
 out->last_move=R16(0x02001df8+2*actor);
 out->repeat_blocked=R8(live+0x58)>>7;
 uint32_t native=R32(0x02001d24);
 if(native<0x02000000 || native>0x02040000-(0x39d+actor) || (native&3))return 3;
 uint32_t mask=R8(native+0x39c+actor);
 if(mask&~15u)return 6;
 out->native_restricted_mask=mask;
 /* permission_state remains zero/unknown regardless of kind/pointer values. */
 return 0;
}
