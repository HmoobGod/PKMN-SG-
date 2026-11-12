/* Read-only original exact-ROM Thumb-1 STRB candidate scout.
 * Scope: source diagnostic, not an injected hook, winner detector, or PP judge.
 * The original guest CPU owns every write. This observer calls only its
 * existing step/read/frame functions; it does not patch or write guest memory.
 *
 * Captures CHANGING, small-valued byte stores to a caller-bounded EWRAM/IWRAM
 * region, to discover candidate native outcome store PCs without first
 * inventing the gBattleOutcome RAM address. This does NOT cover ARM-mode,
 * non-STRB instructions, DMA or indirect writes; no negative inference allowed.
 */
#include <stdint.h>
#include <string.h>

#define SG_MAIN_BASE 0x030055D4u
#define SG_FLAGS_ADDR 0x02001AB4u
#define SG_PENDING_ADDR 0x02001D2Cu
#define SG_STEP_PTR_OFFSET 0x13E8u
#define SG_FRAME_PTR_OFFSET 0x1428u
#define SG_READ8_PTR_OFFSET 0x1488u
#define SG_READ32_PTR_OFFSET 0x1498u

enum { SG_STRB_IMM = 1, SG_STRB_REG = 2 };
typedef struct {
    uint32_t frame, step_index, pc, halfword, form, address;
    uint32_t base_register, offset_register, source_register;
    uint32_t old_byte, new_byte, expected_byte;
    uint32_t registers[8];
    uint32_t battle_flags, battlers, pending, inbattle;
    uint32_t callback1, callback2;
} SG_ThumbByteStore;
typedef struct {
    uint32_t status, start_frame, end_frame, event_count;
    uint32_t start_inbattle, end_inbattle;
    uint32_t start_callback1, start_callback2, end_callback1, end_callback2;
    uint64_t guest_steps;
} SG_ThumbByteStoreRun;

/* Decode ONLY the two 16-bit Thumb-1 STRB encodings. Every field is sourced
 * from the original register file BEFORE the guest instruction executes.
 * Return 0 for any other opcode. 'rm'=255 represents the immediate form. */
int sg_decode_thumb_strb(uint16_t h, const uint32_t r[8],
                         uint32_t *addr, uint32_t *byte,
                         uint32_t *form, uint32_t *rn,
                         uint32_t *rm, uint32_t *rt)
{
    uint32_t offset;
    if (!r || !addr || !byte || !form || !rn || !rm || !rt)
        return 0;
    if ((h & 0xF800u) == 0x7000u) {
        *form=SG_STRB_IMM;
        *rn=(h >> 3) & 7u;
        *rt=h & 7u;
        *rm=255u;
        offset=(h >> 6) & 31u;
    } else if ((h & 0xFE00u) == 0x5400u) {
        *form=SG_STRB_REG;
        *rn=(h >> 3) & 7u;
        *rt=h & 7u;
        *rm=(h >> 6) & 7u;
        offset=r[*rm];
    } else {
        return 0;
    }
    if (r[*rn] > UINT32_MAX-offset)
        return 0;
    *addr=r[*rn]+offset;
    *byte=r[*rt]&255u;
    return 1;
}

/* Only one verified GBA RAM region at a time, never MMIO/video/save addresses. */
static int sg_valid_ram_range(uint32_t lo, uint32_t hi)
{
    return (lo<=hi &&
            ((lo>=0x02000000u && hi<=0x0203FFFFu) ||
             (lo>=0x03000000u && hi<=0x03007FFFu)));
}

void sg_trace_exact_thumb_byte_stores(void *core, uint32_t *regs,
                                      uint32_t frames, uint64_t maxsteps,
                                      uint32_t range_lo, uint32_t range_hi,
                                      SG_ThumbByteStore *events, uint32_t cap,
                                      SG_ThumbByteStoreRun *out)
{
    void (*step)(void *);
    uint32_t (*frame)(void *);
    uint32_t (*read8)(void *,uint32_t,int);
    uint32_t (*read32)(void *,uint32_t,int);
    if (!out) return;
    memset(out,0,sizeof *out);
    if (!core || !regs || !events || !frames || !maxsteps ||
        maxsteps>UINT32_MAX || !cap || cap>8192u ||
        !sg_valid_ram_range(range_lo,range_hi)) {
        out->status=4; return;
    }
    /* Existing pinned mGBA host ABI. Read these function pointers only;
     * this code never stores to core/ROM/RAM/save/regs. */
    memcpy(&step,(char *)core+SG_STEP_PTR_OFFSET,sizeof step);
    memcpy(&frame,(char *)core+SG_FRAME_PTR_OFFSET,sizeof frame);
    memcpy(&read8,(char *)core+SG_READ8_PTR_OFFSET,sizeof read8);
    memcpy(&read32,(char *)core+SG_READ32_PTR_OFFSET,sizeof read32);
    if (!step || !frame || !read8 || !read32) {out->status=4;return;}
    out->start_frame=frame(core);
    out->start_inbattle=read8(core,SG_MAIN_BASE+0x439u,0);
    out->start_callback1=read32(core,SG_MAIN_BASE,0);
    out->start_callback2=read32(core,SG_MAIN_BASE+4u,0);
    for (uint64_t index=0; index<maxsteps; index++) {
        const uint32_t f=frame(core), raw_pc=regs[15];
        uint32_t r[8], addr=0, value=0, form=0, rn=0, rm=0, rt=0;
        uint16_t h=0;
        uint32_t old=0;
        int candidate=0;
        if (f-out->start_frame>=frames) {out->status=1;break;}
        for (uint32_t k=0;k<8;k++)r[k]=regs[k];
        /* Thumb original CPU trace uses PC=instruction+2. Never claim
         * ARM-mode decode from this source-only observer. */
        if (raw_pc>=0x08000002u && raw_pc<0x0A000002u && !(raw_pc&1u)) {
            const uint32_t pc=raw_pc-2u;
            h=(uint16_t)(read8(core,pc,0)&255u);
            h|=(uint16_t)((read8(core,pc+1u,0)&255u)<<8);
            candidate=sg_decode_thumb_strb(h,r,&addr,&value,&form,&rn,&rm,&rt)
                      && addr>=range_lo && addr<=range_hi && value<=7u;
            if (candidate) old=read8(core,addr,0)&255u;
        }
        step(core);out->guest_steps++;
        if (candidate) {
            const uint32_t after=read8(core,addr,0)&255u;
            /* Accept only an actual guest byte mutation consistent with the
             * source register. No CPU store inference from a quiet state. */
            if (old!=after && old<=7u && after==value) {
                if (out->event_count>=cap) {out->status=3;break;}
                SG_ThumbByteStore *e=&events[out->event_count++];
                *e=(SG_ThumbByteStore){0};
                e->frame=f;
                e->step_index=(uint32_t)index;
                e->pc=raw_pc-2u;
                e->halfword=h;
                e->form=form;
                e->address=addr;
                e->base_register=rn;
                e->offset_register=rm;
                e->source_register=rt;
                e->old_byte=old;
                e->new_byte=after;
                e->expected_byte=value;
                for (uint32_t k=0;k<8;k++)e->registers[k]=r[k];
                e->battle_flags=read32(core,SG_FLAGS_ADDR,0);
                e->battlers=read8(core,0x02001AB8u,0);
                e->pending=read32(core,SG_PENDING_ADDR,0);
                e->inbattle=read8(core,SG_MAIN_BASE+0x439u,0);
                e->callback1=read32(core,SG_MAIN_BASE,0);
                e->callback2=read32(core,SG_MAIN_BASE+4u,0);
            }
        }
    }
    out->end_frame=frame(core);
    out->end_inbattle=read8(core,SG_MAIN_BASE+0x439u,0);
    out->end_callback1=read32(core,SG_MAIN_BASE,0);
    out->end_callback2=read32(core,SG_MAIN_BASE+4u,0);
    if (!out->status)out->status=2; /* CPU budget exhausted: incomplete */
}
