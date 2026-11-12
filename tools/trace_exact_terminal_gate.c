/* Read-only original exact modified-ROM terminal/state observer.
 * NO guest writes, no button input, no ROM/save output or hook. This observer
 * measures flags/count/pending/own-PP and marks native player command PCs.
 * A quiet callback trace CANNOT authorize overworld or battle completion.
 */
#include <stdint.h>
#include <string.h>
typedef struct {
    uint32_t frame,flags,battlers,pending,player_auto_callbacks,
             player_move_emitters,manual_move_menu_visits,own_pp[4];
} SG_TerminalSample;
typedef struct {uint32_t status,start_frame,end_frame,samples;uint64_t steps;} SG_TerminalRun;
void sg_trace_exact_terminal(void *core,uint32_t *regs,uint32_t frames,
                             uint64_t maxsteps,uint32_t interval,
                             SG_TerminalSample *rows,uint32_t cap,
                             SG_TerminalRun *out){
    if(!core||!regs||!rows||!out||!cap||!interval)return;
    memset(out,0,sizeof *out);
    void(*step)(void*)=*(void(**)(void*))((char*)core+0x13e8);
    uint32_t(*frame)(void*)=*(uint32_t(**)(void*))((char*)core+0x1428);
    uint32_t(*read8)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1488);
    uint32_t(*read32)(void*,uint32_t,int)=*(uint32_t(**)(void*,uint32_t,int))((char*)core+0x1498);
    out->start_frame=frame(core);
    uint32_t next=out->start_frame, last=out->start_frame;
    uint32_t callbacks=0,emitters=0,menus=0;
    for(uint64_t i=0;i<maxsteps;i++){
        uint32_t f=frame(core);
        if(f-out->start_frame>=frames){out->status=1;break;}
        uint32_t pc=regs[15];
        if(pc==0x09F1F002u)callbacks++;
        if(pc==0x0806BD82u && regs[0]==0 && regs[2]==10)emitters++;
        if(pc==0x0806449Eu)menus++;
        if(f>=next && (last!=f || out->samples==0)){
            if(out->samples>=cap){out->status=3;break;}
            SG_TerminalSample *r=&rows[out->samples++];
            memset(r,0,sizeof *r);
            r->frame=f;
            r->flags=read32(core,0x02001AB4u,0);
            r->battlers=read8(core,0x02001AB8u,0);
            r->pending=read32(core,0x02001D2Cu,0);
            r->player_auto_callbacks=callbacks;
            r->player_move_emitters=emitters;
            r->manual_move_menu_visits=menus;
            for(uint32_t j=0;j<4;j++)r->own_pp[j]=read8(core,0x02001ECCu+37u+j,0);
            next=f+interval;
        }
        last=f;step(core);out->steps++;
    }
    out->end_frame=frame(core);
    if(!out->status)out->status=2;
}
