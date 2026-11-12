/* Executable self-contained FAKE core tests. No real game is run. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "trace_exact_joint_player_terminal.c"
#define WRITER 0x0809E6BAu

typedef struct {
    unsigned char abi[0x1500];
    uint32_t regs[16],index,frame;
    uint32_t main_byte,cb1,cb2,phase,flags,pending,battlers,pp[4];
} Mock;
static uint32_t fake_frame(void *v){return ((Mock *)v)->frame;}
static uint32_t fake_read8(void *v,uint32_t addr,int unused){
    Mock *m=v;(void)unused;
    if(addr==MAIN_BATTLE)return m->main_byte;
    if(addr==MAIN_PHASE)return m->phase;
    if(addr==BATTLE_COUNT)return m->battlers;
    if(addr>=OWN_PP&&addr<OWN_PP+4u)return m->pp[addr-OWN_PP];
    if(addr>=0x08000000u&&addr<0x0A000000u){
        /* Static Thumb opcode only; the mock has no game ROM. */
        if(addr==WRITER)return 0x0Eu;
        if(addr==WRITER+1u)return 0x70u;
        return 0u;
    }
    return 0u;
}
static uint32_t fake_read32(void *v,uint32_t addr,int unused){
    Mock *m=v;(void)unused;
    if(addr==MAIN_BASE)return m->cb1;
    if(addr==MAIN_BASE+4u)return m->cb2;
    if(addr==BATTLE_FLAGS)return m->flags;
    if(addr==PENDING_WORD)return m->pending;
    return 0;
}
static void prepare_regs(Mock *m){
    memset(m->regs,0,sizeof m->regs);
    switch(m->index){
    case 0:m->regs[15]=0x0806BD82u;m->regs[2]=10;m->regs[3]=256;break;
    case 1:m->regs[15]=0x0806B372u;m->regs[1]=1;m->regs[3]=6;break;
    case 2:m->regs[15]=0x0806261Eu;break;
    case 3:m->regs[15]=0x08094332u;break;
    case 4:m->regs[15]=0x0809435Eu;break;
    case 5:m->regs[15]=0x08094376u;m->regs[0]=325;break;
    case 6:m->regs[15]=0x08094382u;m->regs[2]=1;break;
    case 7:m->regs[15]=WRITER+2u;m->regs[1]=OWN_PP;break;
    case 8:m->regs[15]=0x081C1236u;break;
    case 9:m->regs[15]=0x0808E33Eu;break;
    case 10:m->regs[15]=0x081AED5Au;break;
    default:m->regs[15]=0x08000002u;break;
    }
}
static void fake_step(void *v){
    Mock *m=v;
    switch(m->index){
    case 7:m->pp[0]=19;break;
    case 8:m->main_byte=0;break;
    case 9:m->cb1=0x081C7589u;break;
    case 10:m->cb2=0x081C9FC5u;break;
    default:break;
    }
    m->index++;
    if(m->index>=11)m->frame=3202;
    prepare_regs(m);
}
static void install(Mock *m){
    void (*s)(void *)=fake_step;
    uint32_t (*f)(void *)=fake_frame;
    uint32_t (*r8)(void *,uint32_t,int)=fake_read8;
    uint32_t (*r32)(void *,uint32_t,int)=fake_read32;
    memcpy(m->abi+0x13e8,&s,sizeof s);
    memcpy(m->abi+0x1428,&f,sizeof f);
    memcpy(m->abi+0x1488,&r8,sizeof r8);
    memcpy(m->abi+0x1498,&r32,sizeof r32);
    m->index=0;m->frame=3200;m->main_byte=2;m->flags=4;m->battlers=2;
    m->cb1=0x0808CBDDu;m->cb2=0x0808F225u;
    m->pp[0]=20;m->pp[1]=10;m->pp[2]=10;m->pp[3]=20;
    prepare_regs(m);
}
int main(void){
    Mock m={0};SG_JointRun out={0};SG_JointEvent e[64]={0};
    install(&m);
    sg_trace_exact_joint_player_terminal(&m,m.regs,2,1000,e,64,&out);
    assert(out.status==1&&out.end_frame==3202);
    assert(out.steps==11&&out.count==11&&out.final_pp[0]==19);
    assert(out.initial_main==2&&out.final_main==0);
    unsigned types[14]={0};
    for(uint32_t i=0;i<out.count;i++){
        assert(e[i].kind>=1&&e[i].kind<=13);
        types[e[i].kind]++;
    }
    for(uint32_t i=1;i<=7;i++)assert(types[i]==1);
    assert(types[9]==1&&types[10]==1&&types[11]==1&&types[12]==1);
    assert(types[8]==0&&types[13]==0);
    assert(e[7].pc==WRITER&&e[7].before==20&&e[7].after==19);
    assert(e[8].pc==0x081C1234u&&e[9].pc==0x0808E33Cu);
    assert(e[10].pc==0x081AED58u);
    install(&m);sg_trace_exact_joint_player_terminal(&m,m.regs,2,1000,e,2,&out);
    assert(out.status==3);
    install(&m);sg_trace_exact_joint_player_terminal(&m,m.regs,2,2,e,64,&out);
    assert(out.status==2);
    sg_trace_exact_joint_player_terminal(0,m.regs,2,1000,e,64,&out);
    assert(out.status==4);
    puts("original joint actor/PP/Main FAKE core PASS (no native ROM replay)");
    return 0;
}
