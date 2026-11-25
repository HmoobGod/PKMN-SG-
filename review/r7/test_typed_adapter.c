/* Real scorer + existing R7 controller with synthetic engine inputs only. */
#include "typed_adapter.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    R7Original original;
    R7Legal legal;
    SG_PublicBattleObservation obs;
    unsigned reads;
    int mutate_after_rank;
} Fake;
static int read_original(void *ctx,R7Original *out)
{
    Fake *f=ctx;f->reads++;
    *out=f->original;
    if(f->mutate_after_rank && f->reads==2)out->pp[0]++;
    return 1;
}
static int read_legal(void *ctx,const R7Original *p,R7Legal *out)
{ Fake *f=ctx;assert(p->request_id==f->original.request_id);*out=f->legal;return 1; }
static int read_obs(void *ctx,const R7Original *p,SG_PublicBattleObservation *out)
{ Fake *f=ctx;assert(p->request_id==f->original.request_id);*out=f->obs;return 1; }

static void setup(Fake *f)
{
    memset(f,0,sizeof *f);
    R7Original *s=&f->original;R7Legal *l=&f->legal;
    SG_PublicBattleObservation *o=&f->obs;
    s->original_epoch=l->original_epoch=o->battle_token=7;
    s->request_id=l->request_id=o->choice_token=10;
    s->turn=l->turn=0;o->turn_token=1;
    s->command=17;s->original_header[0]=s->original_payload[0]=17;
    s->payload_length=4;s->resources=1;s->owner_party=1;
    s->player_owned=s->wild_single=s->auto_enabled=s->foe_live=1;
    s->moves[0]=100;s->moves[1]=200;s->pp[0]=s->pp[1]=10;
    l->move_limitations_verified=l->target_helpers_verified=l->ineffectiveness_verified=1;
    l->move_legal_mask=l->verified_foe_target_mask=3;
    l->priorities[0]=255; /* replaced by the actual scorer, not blindly trusted */
    o->active[0].role=SG_PUBLIC_SELF;o->active[1].role=SG_PUBLIC_FOE;
    o->require_owned_move_identity_proof=o->require_non_self_ko_proof=true;
    o->known_non_self_ko_move_mask=3;
    o->use_engine_type_effect_heuristic=o->engine_type_effect_bound=true;
    o->effect_known_move_mask=3;o->effect_public_foe_mask=2;
    for(unsigned i=0;i<2;i++){
        o->owned_move_identity[i]=o->classified_move_identity[i]=s->moves[i];
        o->moves[i]=(SG_PublicMove){.known_damaging_move=true,
            .displayed_base_power=i?60:100,.displayed_accuracy=100};
    }
    o->effect_quarters[0][1]=2;o->effect_quarters[1][1]=8;
}
static void next(Fake *f)
{
    R7Original *s=&f->original;
    s->command=19;s->original_header[0]=s->original_payload[0]=19;
    s->payload_length=R7_CHOOSEMOVE_TOTAL_BYTES;
    s->request_id=f->legal.request_id=f->obs.choice_token=11;
    for(unsigned i=0;i<4;i++){
        s->original_payload[4+2*i]=(uint8_t)s->moves[i];
        s->original_payload[5+2*i]=(uint8_t)(s->moves[i]>>8);
        s->original_payload[12+i]=s->original_payload[16+i]=s->pp[i];
    }
}
static R7Plan run(Fake *f,R7Lease *lease,R7FightTicket *ticket)
{
    f->reads=0;
    R7TypedHost h={{f,read_original,read_legal},read_obs};
    R7Plan p=r7_plan_typed(&h,lease,ticket);
    assert(!p.native_move_accepted && !p.native_manual_fallback_accepted &&
           !p.no_forced_switch_certified && !p.production_authorized);
    return p;
}
static void defer(Fake *f)
{
    R7Lease l={7,10,0};R7FightTicket t={0};
    R7Plan p=run(f,&l,&t);
    assert(p.outcome==R7_DEFER && p.action==R7_NO_ACTION &&
           p.slot==R7_NO_SLOT && !l.consumed && !t.pending);
}
int main(void)
{
    Fake f;R7Lease l={7,10,0};R7FightTicket t={0};
    setup(&f);R7Plan p=run(&f,&l,&t);
    assert(p.outcome==R7_FIGHT && p.slot==1 && l.consumed && t.pending);
    next(&f);l=(R7Lease){7,11,0};p=run(&f,&l,&t);
    assert(p.outcome==R7_MOVE && p.slot==1 && l.consumed && !t.pending);
    setup(&f);l=(R7Lease){7,10,0};t=(R7FightTicket){0};
    assert(run(&f,&l,&t).slot==1);
    next(&f);f.legal.move_legal_mask=1;l=(R7Lease){7,11,0};
    p=run(&f,&l,&t);assert(p.outcome==R7_DEFER && !l.consumed);
    setup(&f);f.obs.effect_quarters[0][1]=f.obs.effect_quarters[1][1]=0;defer(&f);
    setup(&f);f.obs.classified_move_identity[1]=201;defer(&f);
    setup(&f);f.obs.choice_token=9;defer(&f);
    setup(&f);f.obs.effect_known_move_mask=1;f.obs.effect_quarters[1][1]=0;defer(&f);
    setup(&f);f.original.pp[0]=f.original.pp[1]=0;defer(&f);
    setup(&f);f.legal.verified_foe_target_mask=0;defer(&f);
    setup(&f);f.original.player_owned=0;defer(&f);
    setup(&f);f.mutate_after_rank=1;defer(&f);
    setup(&f);f.legal.known_ineffective_mask=2;l=(R7Lease){7,10,0};t=(R7FightTicket){0};
    p=run(&f,&l,&t);assert(p.outcome==R7_FIGHT && p.slot==0);
    puts("PASS: typed scorer composed with existing R7 Fight/Move, continuity and fallback");
    return 0;
}
