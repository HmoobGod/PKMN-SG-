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
    R7OriginalFightReceipt receipt;
    unsigned receipt_reads;
    int deny_receipt, drift_receipt;
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
static int read_receipt(void *ctx,const R7Original *p,R7OriginalFightReceipt *out)
{
    Fake *f=ctx;
    assert(p->request_id==f->original.request_id);
    ++f->receipt_reads;
    if(f->deny_receipt) return 0;
    *out=f->receipt;
    if(f->drift_receipt && f->receipt_reads==2) out->unusable_mask^=1u;
    return 1;
}
static void setup_post(Fake *f)
{
    setup(f);next(f);
    f->original.choosemove_layout=R7_LAYOUT_CURRENT44;
    f->original.payload_length=44;
    for(unsigned i=20;i<44;i++) f->original.original_payload[i]=(uint8_t)(i+1u);
    f->receipt.move_request=f->original;
    f->receipt.fight_request_id=10;
    f->receipt.check_mask=0xffff;
}
static R7Plan post(Fake *f,R7Lease *l)
{
    f->reads=f->receipt_reads=0;
    R7TypedHost h={{f,read_original,read_legal},read_obs};
    R7Plan p=r7_plan_typed_after_original_fight(&h,l,read_receipt);
    assert(!p.native_move_accepted && !p.native_manual_fallback_accepted &&
           !p.no_forced_switch_certified && !p.production_authorized);
    return p;
}
static void post_denied(Fake *f)
{
    R7Lease l={7,11,0};
    R7Plan p=post(f,&l);
    assert(p.outcome==R7_DEFER && p.action==R7_NO_ACTION &&
           p.slot==R7_NO_SLOT && p.manual_defer_requested && l.consumed);
    assert(post(f,&l).reason==R7_BAD_LEASE);
}
static void test_original_fight_receipt(void)
{
    Fake f;setup_post(&f);
    R7Lease l={7,11,0};
    R7Plan p=post(&f,&l);
    assert(p.outcome==R7_MOVE && p.action==10 && p.slot==1 && l.consumed);
    assert(post(&f,&l).reason==R7_BAD_LEASE);
    setup_post(&f);f.receipt.unusable_mask=2;l=(R7Lease){7,11,0};
    p=post(&f,&l);
    assert(p.outcome==R7_MOVE && p.slot==0 && l.consumed);
    setup_post(&f);f.receipt.unusable_mask=3;post_denied(&f);
    setup_post(&f);f.receipt.unusable_mask=15;post_denied(&f);
    setup_post(&f);f.receipt.unusable_mask=16;post_denied(&f);
    setup_post(&f);f.receipt.check_mask=1;post_denied(&f);
    setup_post(&f);f.receipt.fight_request_id=0;post_denied(&f);
    setup_post(&f);f.receipt.fight_request_id=11;post_denied(&f);
    setup_post(&f);f.deny_receipt=1;post_denied(&f);
    setup_post(&f);f.drift_receipt=1;post_denied(&f);
    setup_post(&f);f.receipt.move_request.turn++;post_denied(&f);
    setup_post(&f);f.receipt.move_request.owner_party++;post_denied(&f);
    setup_post(&f);f.receipt.move_request.request_id++;post_denied(&f);
    setup_post(&f);f.legal.target_helpers_verified=0;post_denied(&f);
    setup_post(&f);f.legal.ineffectiveness_verified=0;post_denied(&f);
    setup_post(&f);f.legal.verified_foe_target_mask=0;post_denied(&f);
    setup_post(&f);f.mutate_after_rank=1;post_denied(&f);
    for(unsigned i=0;i<44;i++){
        setup_post(&f);f.receipt.move_request.original_payload[i]^=1u;
        post_denied(&f);
    }
    setup_post(&f);f.original.choosemove_layout=R7_LAYOUT_SOURCE40;
    f.original.payload_length=40;f.receipt.move_request=f.original;post_denied(&f);
    setup(&f);f.receipt.move_request=f.original;f.receipt.fight_request_id=9;
    f.receipt.check_mask=0xffff;l=(R7Lease){7,10,0};
    assert(post(&f,&l).outcome==R7_DEFER && l.consumed);
}
int main(void)
{
    test_original_fight_receipt();
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
    /* Same existing controller, raw source fixed-point type multipliers. */
    setup(&f);f.obs.effect_quarters[0][1]=f.obs.effect_quarters[1][1]=0;
    f.obs.use_engine_q12_effects=true;
    assert(sg_store_engine_type_q12(&f.obs,0,1,512u));
    assert(sg_store_engine_type_q12(&f.obs,1,1,32768u));
    l=(R7Lease){7,10,0};t=(R7FightTicket){0};
    p=run(&f,&l,&t);assert(p.outcome==R7_FIGHT && p.slot==1);
    next(&f);l=(R7Lease){7,11,0};
    p=run(&f,&l,&t);assert(p.outcome==R7_MOVE && p.slot==1 && !t.pending);
    setup(&f);f.obs.use_engine_q12_effects=true;defer(&f); /* legacy mix */
    /* Source-only 44-byte profile exercises the real typed composition. */
    setup(&f);f.original.choosemove_layout=R7_LAYOUT_CURRENT44;
    l=(R7Lease){7,10,0};t=(R7FightTicket){0};
    p=run(&f,&l,&t);
    assert(p.outcome==R7_FIGHT && p.slot==1 && t.pending);
    next(&f);f.original.payload_length=R7_CHOOSEMOVE_CURRENT44_BYTES;
    for(unsigned i=20;i<44;i++)f.original.original_payload[i]=(uint8_t)(i+1u);
    l=(R7Lease){7,11,0};p=run(&f,&l,&t);
    assert(p.outcome==R7_MOVE && p.slot==1 && l.consumed && !t.pending);
    puts("PASS: typed scorer composed with existing R7 Fight/Move, continuity and fallback; source UQ4.12 inputs");
    return 0;
}
