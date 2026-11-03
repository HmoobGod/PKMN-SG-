#include <stdint.h>
/* R13 PRIVATE EXPERIMENT ONLY. This pin is one historically accepted
 * non-roamer wild request, not general action ownership or legality.
 * Not a shipped gameplay feature: outside the pinned fixture, fail closed.
 * Never reads any opponent hidden stats, moves, item, or ability.
 */
#define R8(a)  (*(volatile const uint8_t *)(uintptr_t)(a))
#define R16(a) (*(volatile const uint16_t *)(uintptr_t)(a))
#define R32(a) (*(volatile const uint32_t *)(uintptr_t)(a))
#define W8(a,v) (*(volatile uint8_t *)(uintptr_t)(a)=(uint8_t)(v))
/* Defined exclusively in a private, compiler-generated local header.
 * No raw player request bytes are stored in the public repository. */
#include "private_r13_request.h"
/* 1 means only 'attempt original PLAYER auto entry' in this disposable
 * binary. We do not claim engine authorization for untested actions. */
__attribute__((used)) uint32_t sg_r13_fixture_gate(void){
 if (R32(0x02001ab4)!=4u || R8(0x02001ab8)!=2u)return 0;
 if (R8(0x030001a4)!=1u || R8(0x030001a5)!=3u)return 0;
 if (R32(0x03002e48)!=0x080625f9u || R32(0x03002e4c)!=0x080616d9u)return 0;
 if (R8(0x02001b58)!=0u || R8(0x02001b59)!=1u || (R8(0x02001d42)&3u)!=0u)return 0;
 if ((R32(0x02001d2c)&1u)==0u)return 0;
 if (R8(0x02001e54)!=1u)return 0; /* actual in-ROM scorer's status4 proposal */
 uintptr_t req=R32(0x02001c6c);
 uintptr_t sel=R32(0x02001e90);
 uintptr_t locks=R32(0x02001d24);
 if (req<0x02000000u || req>0x02040000u-0x210u || (req&1u))return 0;
 if (sel<0x02000000u || sel>0x02040000u-0x110u || (sel&1u))return 0;
 if (locks<0x02000000u || locks>0x02040000u-0x39eu || (locks&3u))return 0;
 if (R8(locks+0x39cu)!=0u)return 0;
 for(uint32_t i=0;i<44u;i++)if(R8(req+0x10u+i)!=k_request[i])return 0;
 const uint16_t expected[4]={325u,157u,92u,269u};
 const uint8_t pp[4]={20u,10u,10u,20u};
 for(uint32_t i=0;i<4u;i++) {
  if (R16(0x02001eccu+12u+2u*i)!=expected[i] || R8(0x02001eccu+37u+i)!=pp[i])return 0;
 }
 uint32_t packed=R32(0x02001eccu+0x6cu);
 uint32_t enctimer=(R32(0x02001eccu+0x74u)>>15)&7u;
 if (((packed>>11)&0x3ffu) || ((packed>>21)&0x3ffu) || enctimer ||
     (R8(0x02001eccu+0x58u)&0x80u) || R16(0x02001df8)!=0u)return 0;
 /* Exactly one mutation AFTER all checks: the original per-player
  * automatic slot byte read by the pre-existing strict preflight guard.
  * If the original engine rejects it, existing guard should defer manual. */
 W8(sel+0x106u,1u);
 return 1;
}