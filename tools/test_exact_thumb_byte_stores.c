/* Standalone mock-core tests for the READ-ONLY original Thumb STRB scout.
 * Fake core is deliberately NOT the real modified ROM or an acceptance test. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "trace_exact_thumb_byte_stores.c"

static uint16_t instruction;
static uint32_t regs[16], clock_frame;
static uint8_t value_before, value_after;
static uint32_t steps;
static uint32_t store_address;
static int inject_store;

static uint32_t mock_read8(void *core,uint32_t a,int bus) {
    (void)core;(void)bus;
    if (a==0x08001000u)return instruction&255u;
    if (a==0x08001001u)return instruction>>8;
    if (a==store_address)return value_before;
    if (a==SG_MAIN_BASE+0x439u)return 2u;
    if (a==0x02001AB8u)return 2u;
    return 0u;
}
static uint32_t mock_read32(void *core,uint32_t a,int bus) {
    (void)core;(void)bus;
    if (a==SG_FLAGS_ADDR)return 4u;
    if (a==SG_MAIN_BASE)return 0x0808CBDDu;
    if (a==SG_MAIN_BASE+4u)return 0x0808F225u;
    return 0;
}
static uint32_t mock_frame(void *core) {(void)core;return clock_frame;}
static void mock_step(void *core) {
    (void)core;
    if (inject_store && steps==0) value_before=value_after;
    steps++;
    clock_frame++;
    regs[15]+=2u;
}
static void mock_initialize(uint8_t core[0x1600],uint16_t op) {
    void (*step)(void*)=mock_step;
    uint32_t (*frame)(void*)=mock_frame;
    uint32_t (*read8)(void*,uint32_t,int)=mock_read8;
    uint32_t (*read32)(void*,uint32_t,int)=mock_read32;
    memset(core,0,0x1600);
    memcpy(core+SG_STEP_PTR_OFFSET,&step,sizeof step);
    memcpy(core+SG_FRAME_PTR_OFFSET,&frame,sizeof frame);
    memcpy(core+SG_READ8_PTR_OFFSET,&read8,sizeof read8);
    memcpy(core+SG_READ32_PTR_OFFSET,&read32,sizeof read32);
    memset(regs,0,sizeof regs);
    regs[15]=0x08001002u;
    regs[1]=0x02000100u;
    regs[0]=2u;
    instruction=op;
    value_before=0;value_after=2;
    clock_frame=0;steps=0;
    inject_store=1;
    store_address=0x02000100u;
}
static SG_ThumbByteStoreRun run_case(uint16_t h,SG_ThumbByteStore events[4]) {
    uint8_t core[0x1600];SG_ThumbByteStoreRun out;
    mock_initialize(core,h);
    sg_trace_exact_thumb_byte_stores(core,regs,2,10,0x02000000u,0x0203FFFFu,
                                     events,4,&out);
    return out;
}
int main(void) {
    uint32_t addr,byte,form,rn,rm,rt;
    uint32_t r[8]={2,0x02000100u,0,0,0,0,0,0};
    /* STRB r0,[r1,#0] */
    uint16_t h=0x7008u;
    assert(sg_decode_thumb_strb(h,r,&addr,&byte,&form,&rn,&rm,&rt));
    assert(addr==0x02000100u && byte==2 && form==1 && rn==1 && rm==255 && rt==0);
    /* Genuine protected Current ROM halfword at original own-PP writer
     * PC0x0809E6BA is 0x700E (STRB r6,[r1,#0]), independently read
     * from user-supplied Current bytes. This tests decoding ONLY; its
     * occurrence is NOT a new native runtime witness. */
    r[1]=0x02001EF1u;r[6]=19u;
    assert(sg_decode_thumb_strb(0x700Eu,r,&addr,&byte,&form,&rn,&rm,&rt));
    assert(addr==0x02001EF1u && byte==19u && rn==1 && rt==6u);
    r[1]=0x02000100u;r[6]=0u;
    /* STRB r0,[r1,r2] */
    uint16_t hreg=0x5488u;
    assert(sg_decode_thumb_strb(hreg,r,&addr,&byte,&form,&rn,&rm,&rt));
    assert(addr==0x02000100u && form==2 && rm==2);
    assert(!sg_decode_thumb_strb(0x7808u,r,&addr,&byte,&form,&rn,&rm,&rt)); /* LDRB */
    assert(!sg_decode_thumb_strb(0x6008u,r,&addr,&byte,&form,&rn,&rm,&rt)); /* STR */
    assert(!sg_decode_thumb_strb(0x8008u,r,&addr,&byte,&form,&rn,&rm,&rt)); /* STRH */
    assert(!sg_decode_thumb_strb(h,NULL,&addr,&byte,&form,&rn,&rm,&rt));
    r[1]=0xFFFFFFFFu;
    assert(!sg_decode_thumb_strb(0x7048u,r,&addr,&byte,&form,&rn,&rm,&rt)); /* address overflow */
    r[1]=0x02000100u;
    assert(!sg_decode_thumb_strb(h,r,NULL,&byte,&form,&rn,&rm,&rt));
    assert(sg_valid_ram_range(0x02000000u,0x0203FFFFu));
    assert(sg_valid_ram_range(0x03000000u,0x03007FFFu));
    assert(!sg_valid_ram_range(0x02000000u,0x03007FFFu));
    assert(!sg_valid_ram_range(0x04000000u,0x04000100u));
    assert(!sg_valid_ram_range(0x02000005u,0x02000000u));

    SG_ThumbByteStore events[4];SG_ThumbByteStoreRun out;
    out=run_case(h,events);
    assert(out.status==1 && out.event_count==1 && out.guest_steps==2);
    assert(events[0].pc==0x08001000u && events[0].halfword==h);
    assert(events[0].address==0x02000100u && events[0].old_byte==0u);
    assert(events[0].new_byte==2u && events[0].expected_byte==2u);
    assert(events[0].registers[1]==0x02000100u && events[0].source_register==0);
    assert(events[0].battle_flags==4u && events[0].inbattle==2u);
    out=run_case(hreg,events);
    assert(out.status==1 && out.event_count==1 && events[0].form==2u);
    out=run_case(0x7808u,events);
    assert(out.status==1 && out.event_count==0);

    {
        uint8_t core[0x1600];
        mock_initialize(core,h);value_before=2;
        sg_trace_exact_thumb_byte_stores(core,regs,2,10,0x02000000u,0x0203FFFFu,events,4,&out);
        assert(out.status==1 && out.event_count==0); /* unchanged */
        mock_initialize(core,h);value_after=3;
        sg_trace_exact_thumb_byte_stores(core,regs,2,10,0x02000000u,0x0203FFFFu,events,4,&out);
        assert(out.status==1 && out.event_count==0); /* wrong encoded source */
        mock_initialize(core,h);inject_store=0;
        sg_trace_exact_thumb_byte_stores(core,regs,2,10,0x02000000u,0x0203FFFFu,events,4,&out);
        assert(out.status==1 && out.event_count==0); /* no guest mutation */
        mock_initialize(core,h);
        sg_trace_exact_thumb_byte_stores(core,regs,2,10,0x03000000u,0x03007FFFu,events,4,&out);
        assert(out.status==1 && out.event_count==0); /* wrong region */
        mock_initialize(core,h);
        sg_trace_exact_thumb_byte_stores(core,regs,2,10,0x04000000u,0x040000FFu,events,4,&out);
        assert(out.status==4); /* forbidden MMIO */
        mock_initialize(core,h);
        sg_trace_exact_thumb_byte_stores(core,regs,2,10,0x02000000u,0x0203FFFFu,events,0,&out);
        assert(out.status==4); /* invalid capacity */
        mock_initialize(core,h);
        sg_trace_exact_thumb_byte_stores(core,regs,2,1,0x02000000u,0x0203FFFFu,events,4,&out);
        assert(out.status==2 && out.guest_steps==1); /* budget != frame completion */
        mock_initialize(core,h);
        sg_trace_exact_thumb_byte_stores(core,regs,2,0x100000000ULL,
                                         0x02000000u,0x0203FFFFu,events,4,&out);
        assert(out.status==4); /* truncated step-index forbidden */
    }
    puts("original Thumb STRB scout mock-core assertions PASS");
    return 0;
}
