/* Deterministic MOCK mGBA ABI, not authenticated modified-ROM gameplay. */
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include "trace_exact_main_battle_edge.c"
static uint32_t rr[16], f, steps, c1, c2, flags;
static uint8_t battle;
static unsigned mode;
static uint32_t r8(void *x,uint32_t a,int bus){(void)x;(void)bus;
 if(a==EDGE_INBATTLE)return battle;
 if(a==EDGE_BATTLERS)return 2;
 if(a==0x08001000u)return 0x01;
 if(a==0x08001001u)return 0x70;
 return 0;
}
static uint32_t r32(void *x,uint32_t a,int bus){(void)x;(void)bus;
 if(a==EDGE_MAIN)return c1;
 if(a==EDGE_MAIN+4u)return c2;
 if(a==EDGE_FLAGS)return flags;
 if(a==EDGE_PENDING)return 0;
 return 0;
}
static uint32_t getframe(void *x){(void)x;return f;}
static void dostep(void *x){(void)x;
 if(steps==0 && mode==1)battle=3; /* low bit only, no inBattle edge */
 if(steps==1)battle=1; /* TRUE 2 -> FALSE 0, regardless of low bit */
 if(steps==2 && mode==2)battle=3; /* FALSE -> TRUE */
 if(steps==3 && mode==2)battle=1; /* TRUE -> FALSE */
 if(steps==1){c1=0x081C7589; c2=0x081C9FC5;}
 steps++;f++;if(rr[15]!=0x03000002u)rr[15]=0x08001002u;
}
static void init(uint8_t core[0x1600]){
 void(*a)(void*)=dostep;uint32_t(*b)(void*)=getframe;
 uint32_t(*c)(void*,uint32_t,int)=r8;
 uint32_t(*d)(void*,uint32_t,int)=r32;
 memset(core,0,0x1600);memcpy(core+EDGE_STEP_OFFSET,&a,sizeof a);
 memcpy(core+EDGE_FRAME_OFFSET,&b,sizeof b);
 memcpy(core+EDGE_R8_OFFSET,&c,sizeof c);
 memcpy(core+EDGE_R32_OFFSET,&d,sizeof d);
 memset(rr,0,sizeof rr);rr[15]=0x08001002u;
 steps=0;f=100;mode=0;battle=2;flags=4;
 c1=0x0808CBDD;c2=0x0808F225;
}
int main(void){
 uint8_t core[0x1600];SG_MainBattleEdge rows[8];SG_MainBattleEdgeRun out;
 init(core);sg_trace_main_battle_edge(core,rr,5,16,rows,8,&out);
 assert(out.status==1 && out.total_edges==1 && out.guest_steps==5);
 assert(rows[0].frame==101 && rows[0].step_index==1);
 assert(rows[0].before_byte==2 && rows[0].after_byte==1);
 assert(rows[0].pc==0x08001000 && rows[0].opcode_halfword==0x7001);
 assert(rows[0].before_callback2==0x0808F225 && rows[0].after_callback2==0x081C9FC5);
 assert(rows[0].before_flags==4 && rows[0].after_flags==4);
 assert(out.end_byte==1 && out.end_callback2==0x081C9FC5);
 init(core);mode=1;sg_trace_main_battle_edge(core,rr,5,16,rows,8,&out);
 assert(out.status==1 && out.total_edges==1); /* 2->3 low bit not counted */
 assert(rows[0].before_byte==3 && rows[0].after_byte==1);
 init(core);mode=2;sg_trace_main_battle_edge(core,rr,5,16,rows,8,&out);
 assert(out.status==1 && out.total_edges==3); /* inBattle 2 ->0 ->2 ->0 */
 assert(rows[1].before_byte==1 && rows[1].after_byte==3);
 init(core);sg_trace_main_battle_edge(core,rr,5,16,rows,1,&out);
 assert(out.status==1 && out.total_edges==1);
 init(core);mode=2;sg_trace_main_battle_edge(core,rr,5,16,rows,1,&out);
 assert(out.status==3); /* cannot claim completed full trace */
 init(core);sg_trace_main_battle_edge(core,rr,5,1,rows,8,&out);
 assert(out.status==2 && out.guest_steps==1); /* no frame completion */
 init(core);sg_trace_main_battle_edge(core,rr,5,0,rows,8,&out);
 assert(out.status==4);
 init(core);sg_trace_main_battle_edge(core,rr,5,16,rows,0,&out);
 assert(out.status==4);
 init(core);sg_trace_main_battle_edge(core,rr,5,16,rows,257,&out);
 assert(out.status==4);
 init(core);rr[15]=0x03000002u;sg_trace_main_battle_edge(core,rr,5,16,rows,8,&out);
 assert(out.status==1 && out.total_edges==1 && rows[0].pc==0); /* unknown PC is NOT certified */
 puts("original gMain inBattle edge mock CPU PASS");return 0;
}
