/* Actual GBA memory reader for the historical 7b9ac66d ROM only.
 * No action authority: caller must separately authenticate ROM, lifecycle,
 * automatic Fight and approved output/stack allocation before invocation. */
#include <stdint.h>
#define R8(a) (*(volatile const uint8_t *)(uintptr_t)(a))
#define R16(a) (*(volatile const uint16_t *)(uintptr_t)(a))
#define R32(a) (*(volatile const uint32_t *)(uintptr_t)(a))
#define REQUEST 0x0201bf14u
#define LIVE 0x02001eccu
#define LENGTH 44u

/* Narrow historical actor0 wild-single context; exclusion only. */
static int scope(uint32_t pending)
{
    return (pending==1u || pending==3u) &&
        R32(0x02001d2c)==pending && R32(0x02001ab4)==4u &&
        R8(0x02001ab8)==2u && R8(0x02001b58)==0u &&
        R8(0x02001b59)==1u && (R8(0x02001d42)&3u)==0u &&
        R8(0x030001a4)==1u && R8(0x030001a5)==3u &&
        R32(0x03002e48)==0x080625f9u &&
        R32(0x03002e58)==0x080619d5u &&
        R32(0x03002e5c)==0x08060ac5u &&
        R32(0x02001c6c)==0x0201bf04u;
}
static int matches_live(const uint8_t *b)
{
    for (unsigned i=0;i<4u;i++) {
        unsigned move=(unsigned)b[4u+2u*i] | ((unsigned)b[5u+2u*i]<<8);
        unsigned pp=b[12u+i], max=b[16u+i];
        if (move>=936u || move!=R16(LIVE+12u+2u*i) ||
            pp!=R8(LIVE+37u+i) || pp>max ||
            (move!=0u && max==0u) || (move==0u && (pp!=0u || max!=0u)))
            return 0;
    }
    return 1;
}
/* Writes ONLY to independently approved caller output; on failure no output
 * mutation. Returns a stable observed payload, NOT a native request grant.
 * Double sampling cannot exclude ABA, interruption, or a stale lifetime. */
int r7_native_capture_current44(uint32_t actor,uint8_t *out,uint32_t capacity)
{
    uint8_t b[LENGTH];
    if (actor!=0u || !out || capacity!=LENGTH) return 0;
    uint32_t pending=R32(0x02001d2c);
    if (!scope(pending)) return 0;
    for (unsigned i=0;i<LENGTH;i++) b[i]=R8(REQUEST+i);
    if (b[0]!=19u || b[1] || b[2] || b[3] || !matches_live(b)) return 0;
    for (unsigned i=0;i<LENGTH;i++) if (b[i]!=R8(REQUEST+i)) return 0;
    if (!matches_live(b) || !scope(pending)) return 0;
    for (unsigned i=0;i<LENGTH;i++) out[i]=b[i];
    return 1;
}
