/* Synthetic original player0 44-byte request-copy CPU fixture. No
 * commercial ROM, save, emulator, or host/guest memory writes are involved.
 * The observer is read-only; ONLY this owned FAKE core performs writes. */
#ifdef NDEBUG
#error "Original player0 request-copy tests require enabled assertions"
#endif
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "alternate_mgba_capture_player_copy.c"

typedef struct {
    uint8_t abi[0x1600];
    uint8_t ram[0x40000];
    uint32_t regs[16], frame, buffer, source, dest, count, mode;
} FakeCore;
static uint32_t fr(void *v){return ((FakeCore *)v)->frame;}
static uint32_t rb(void *v,uint32_t addr,int unused)
{
    FakeCore *m=v;(void)unused;
    /* These are intentionally generated fake Thumb instructions, never
     * original protected ROM halfwords or real emulator traces. */
    if(addr==ENTRY_PC)return 0x01u;
    if(addr==ENTRY_PC+1u)return 0x21u;
    /* Valid public fake opcode 0x5443: STRB r3,[r0,r1].
     * PRE-step r0=destination base, r1=index, r3=source[index].
     * The old 0x7003 fake opcode instead addressed ONLY destination[0]
     * even as the fixture wrote destination[index]; that could not
     * demonstrate the claimed source CPU STORE_PC semantics. */
    if(addr==STORE_PC) {
        if(m->count>=7u&&m->mode==9u)return 0x44u; /* changed opcode */
        if(m->count>=7u&&m->mode==12u)return 0x03u; /* WRONG address */
        if(m->count>=7u&&m->mode==13u)return 0x42u; /* WRONG Rt */
        return 0x43u;
    }
    if(addr==STORE_PC+1u)return (m->count>=7u&&m->mode==12u)?0x70u:
                                 (m->count>=7u&&m->mode==14u)?0x5Cu:0x54u;
    if(addr==POST_PC)return 0x18u;
    if(addr==POST_PC+1u)return 0x47u;
    return (addr>=EWRAM_BASE&&addr<EWRAM_END)?
        m->ram[addr-EWRAM_BASE]:0u;
}
static uint32_t rw(void *v,uint32_t addr,int unused)
{
    FakeCore *m=v;(void)unused;
    if(addr==0x02001C6Cu)return m->buffer;
    return 0u;
}
static void arm_store(FakeCore *m,uint32_t index)
{
    m->regs[15]=STORE_PC;
    m->regs[0]=m->dest;
    m->regs[1]=index;
    m->regs[3]=m->ram[m->source-EWRAM_BASE+index];
    m->regs[4]=m->source;
    m->regs[13]=0x03007000u-8u;
    if(m->mode==4u&&index==5u)m->regs[4]++;
}
static void st(void *v)
{
    FakeCore *m=v;
    uint32_t pc=m->regs[15];
    if(pc==ENTRY_PC){
        arm_store(m,0u);
        if(m->mode==5u)m->frame=49u; /* 50 -> 49 must fail closed */
    }else if(pc==STORE_PC){
        uint32_t k=m->count++;
        assert(k<44u);
        if(!(m->mode==1u&&k==7u))
            m->ram[m->dest-EWRAM_BASE+k]=(uint8_t)m->regs[3];
        /* Deliberately corrupt then restore a *previous* destination or
         * source byte. Endpoint-only post-loop checks miss these. */
        if(k==7u&&m->mode==10u)m->ram[m->dest-EWRAM_BASE]=0xFFu;
        if(k==8u&&m->mode==10u)
            m->ram[m->dest-EWRAM_BASE]=m->ram[m->source-EWRAM_BASE];
        if(k==7u&&m->mode==11u)m->ram[m->source-EWRAM_BASE]=0xFFu;
        if(k==8u&&m->mode==11u)m->ram[m->source-EWRAM_BASE]=19u;
        if(k+1u<44u)arm_store(m,k+1u);
        else {
            m->regs[15]=POST_PC;
            m->regs[0]=m->dest;
            m->regs[1]=SRC_N;
            m->regs[2]=SRC_N;
            m->regs[4]=m->source;
        }
    }else assert(0 && "unexpected fake CPU program counter");
}
static void install(FakeCore *m,uint32_t mode)
{
    void (*step)(void *)=st;
    uint32_t (*frame)(void *)=fr;
    uint32_t (*read8)(void *,uint32_t,int)=rb;
    uint32_t (*read32)(void *,uint32_t,int)=rw;
    memset(m,0,sizeof *m);
    memcpy(m->abi+0x13e8,&step,sizeof step);
    memcpy(m->abi+0x1428,&frame,sizeof frame);
    memcpy(m->abi+0x1488,&read8,sizeof read8);
    memcpy(m->abi+0x1498,&read32,sizeof read32);
    m->source=EWRAM_BASE+0x1000u;
    m->buffer=EWRAM_BASE+0x2000u;
    m->dest=m->buffer+0x10u;
    m->frame=50u;m->mode=mode;
    for(uint32_t i=0;i<SRC_N;i++)
        m->ram[m->source-EWRAM_BASE+i]=(uint8_t)(19u+i);
    m->regs[15]=ENTRY_PC;m->regs[0]=0;
    m->regs[1]=0;m->regs[2]=m->source;m->regs[3]=SRC_N;
    m->regs[13]=0x03007000u;m->regs[14]=0x0800ABCDu;
}
static void run(FakeCore *m,Proof *p,uint32_t frames,uint32_t steps)
{
    sg_capture_player_request(m,m->regs,frames,steps,p);
}
int main(void)
{
    static FakeCore m;Proof p={0};
    install(&m,0u);run(&m,&p,2u,1000u);
    assert(p.state==2u&&p.error==0u&&p.stores==SRC_N);
    assert(p.total_steps==SRC_N+1u&&p.entry_frame==p.post_frame);
    assert(p.opcode_post==19u&&p.actor==0u&&p.length==44u);
    assert(p.source==m.source&&p.dest==m.dest);
    assert(p.entry_insn==0x2101u&&p.store_insn==0x5443u&&
           p.post_insn==0x4718u);
    for(uint32_t i=0;i<SRC_N;i++){
        assert(p.store_indices[i]==i);
        assert(p.store_values[i]==p.source_before[i]);
        assert(p.dest_before[i]!=p.store_values[i]);
        assert(p.store_effective_addresses[i]==m.dest+i);
        assert(p.store_encoded_source_bytes[i]==p.store_values[i]);
        assert(p.dest_after[i]==p.source_before[i]);
        assert(p.source_after[i]==p.source_before[i]);
    }
    install(&m,1u);run(&m,&p,2u,1000u);
    assert(p.state==1u&&p.error==7u&&p.stores==7u);

    /* Pre-existing same byte is not observable proof of a CPU store. */
    install(&m,8u);
    m.ram[m.dest-EWRAM_BASE+7u]=m.ram[m.source-EWRAM_BASE+7u];
    run(&m,&p,2u,1000u);
    assert(p.error==10u&&p.state==1u&&p.stores==7u);

    /* Changing a CPU halfword mid-copy invalidates its provenance. */
    install(&m,9u);run(&m,&p,2u,1000u);
    assert(p.error==11u&&p.state==1u&&p.stores==7u);

    /* The fake CPU may physically write dest+k while its claimed
     * instruction points elsewhere, uses the wrong source register,
     * or is not even a byte STORE. None may count as original CPU proof. */
    for(uint32_t mode=12u;mode<=14u;mode++){
        install(&m,mode);run(&m,&p,2u,1000u);
        assert(p.error==14u&&p.state==1u&&p.stores==7u);
    }

    uint32_t test_regs[16]={0},a=0,b=0;
    test_regs[0]=m.dest;test_regs[1]=17u;test_regs[3]=55u;
    assert(sg_decode_thumb_strb(0x5443u,test_regs,&a,&b));
    assert(a==m.dest+17u && b==55u);
    assert(!sg_decode_thumb_strb(0x5C43u,test_regs,&a,&b)); /* LDRB */
    assert(sg_decode_thumb_strb(0x7003u,test_regs,&a,&b));
    assert(a==m.dest); /* cannot explain destination[index>0] */
    test_regs[0]=UINT32_MAX;
    assert(!sg_decode_thumb_strb(0x5443u,test_regs,&a,&b));

    install(&m,10u);run(&m,&p,2u,1000u);
    assert(p.error==12u&&p.state==1u&&p.stores==7u);
    install(&m,11u);run(&m,&p,2u,1000u);
    assert(p.error==13u&&p.state==1u&&p.stores==7u);

    install(&m,2u);m.ram[m.source-EWRAM_BASE]=18u;
    run(&m,&p,2u,1000u);
    assert(p.error==3u&&p.state==0u&&p.total_steps==0u);

    install(&m,3u);m.buffer=0x01FFFFF0u; /* would alias EWRAM if +16 wraps */
    run(&m,&p,2u,1000u);
    assert(p.error==2u&&p.state==0u&&p.total_steps==0u);

    install(&m,4u);run(&m,&p,2u,1000u);
    assert(p.error==4u&&p.state==1u&&p.stores==5u);

    install(&m,5u);run(&m,&p,2u,1000u);
    /* Final-frame rollback additionally invalidates the staged witness. */
    assert(p.error==9u&&p.state==0u&&p.total_steps==1u);

    install(&m,0u);run(&m,&p,2u,1u);
    assert(p.state==1u&&p.error==0u&&p.stores==0u);

    install(&m,0u);run(&m,&p,10001u,1000u);
    assert(p.error==8u&&p.state==0u&&p.total_steps==0u);

    install(&m,0u);
    memset(m.abi+0x13e8,0,sizeof(void (*)(void *)));
    run(&m,&p,2u,1000u);
    assert(p.error==8u&&p.state==0u&&p.total_steps==0u);

    puts("PUBLIC_PLAYER0_REQUEST_COPY: PASS original 44-byte poststep fake-core checks");
    return 0;
}
