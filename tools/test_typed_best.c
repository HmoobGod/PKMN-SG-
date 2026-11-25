#include <assert.h>
#include <stdio.h>
#include "ranker_workspace.h"

static void fixture(SG_View *v, SG_PublicBattleObservation *o)
{
    *v=(SG_View){0}; *o=(SG_PublicBattleObservation){0};
    v->battle_token=o->battle_token=1;
    v->turn_token=o->turn_token=2;
    v->choice_token=o->choice_token=3;
    v->controller=1; v->phase=2; v->battler_count=2;
    v->supported_mode=true; v->battle_mode_flags=4;
    v->permitted_move_mask=3;
    v->permitted_targets[0]=v->permitted_targets[1]=2;
    o->active[0].role=SG_PUBLIC_SELF;
    o->active[1].role=SG_PUBLIC_FOE;
    o->require_owned_move_identity_proof=true;
    o->owned_move_identity[0]=o->classified_move_identity[0]=1;
    o->owned_move_identity[1]=o->classified_move_identity[1]=2;
    o->moves[0]=(SG_PublicMove){.known_damaging_move=true,
        .displayed_base_power=100,.displayed_accuracy=100};
    o->moves[1]=(SG_PublicMove){.known_damaging_move=true,
        .displayed_base_power=60,.displayed_accuracy=100};
    o->use_engine_type_effect_heuristic=true;
    o->engine_type_effect_bound=true;
    o->effect_known_move_mask=3; o->effect_public_foe_mask=2;
    o->effect_quarters[0][1]=2; o->effect_quarters[1][1]=8;
}
static void parity(SG_View *v, SG_PublicBattleObservation *o, size_t n, unsigned slot)
{
    SG_Proposal best={0}, all[SG_PUBLIC_MAX_CHOICES]={0};
    SG_RankWorkspace ws;
    assert(sg_rank_public_damage_workspace(v,o,all,SG_PUBLIC_MAX_CHOICES,&ws)==n);
    assert(sg_rank_typed_damage_best(v,o,&best)==n);
    if(n) {
        assert(best.move_slot==slot && best.move_slot==all[0].move_slot);
        assert(best.target==all[0].target && best.actor==all[0].actor);
        assert(best.action==SG_USE_MOVE && best.choice_token==all[0].choice_token);
    }
}
static void q12_cases(void)
{
    SG_View v; SG_PublicBattleObservation o; SG_Proposal p={0};
    fixture(&v,&o);
    o.effect_quarters[0][1]=o.effect_quarters[1][1]=0;
    o.use_engine_q12_effects=true;
    assert(sg_store_engine_type_q12(&o,0,1,512u)); /* 1/8x, NOT immunity */
    assert(sg_store_engine_type_q12(&o,1,1,32768u)); /* 8x */
    parity(&v,&o,2,1);
    v.permitted_move_mask=1; parity(&v,&o,1,0);
    v.permitted_move_mask=3;
    assert(sg_store_engine_type_q12(&o,0,1,32768u));
    o.moves[0].displayed_base_power=999; /* unsigned product > INT32_MAX */
    parity(&v,&o,2,0);
    assert(!sg_store_engine_type_q12(&o,0,1,32769u));
    assert(!sg_store_engine_type_q12(&o,0,1,65536u));
    assert(!sg_store_engine_type_q12(&o,0,1,UINT32_MAX));
    assert(o.effect_q12[0][1]==32768u);
    assert(!sg_store_engine_type_q12(&o,4,1,4096u));
    assert(!sg_store_engine_type_q12(&o,0,0,4096u));
    assert(sg_store_engine_type_q12(&o,0,1,0u)); parity(&v,&o,1,1);
    assert(sg_store_engine_type_q12(&o,1,1,0u)); parity(&v,&o,0,0);
    assert(sg_store_engine_type_q12(&o,0,1,4096u));
    assert(sg_store_engine_type_q12(&o,1,1,6144u)); /* 1.5 exact */
    o.moves[0].displayed_base_power=80; parity(&v,&o,2,1);
    o.effect_quarters[0][1]=4; parity(&v,&o,0,0); /* conflicting formats */
    o.effect_quarters[0][1]=0;
    o.effect_q12[0][0]=4096; parity(&v,&o,0,0); /* absent cell */
    o.effect_q12[0][0]=0;
    o.use_engine_q12_effects=false; parity(&v,&o,0,0);
    fixture(&v,&o); assert(!sg_store_engine_type_q12(&o,0,1,4096u));
    o.use_engine_type_effect_heuristic=false; o.engine_type_effect_bound=false;
    o.effect_known_move_mask=o.effect_public_foe_mask=0;
    o.effect_quarters[0][1]=o.effect_quarters[1][1]=0;
    o.use_engine_q12_effects=true; p.move_slot=3;
    assert(sg_rank_damage_best(&v,&o,&p)==0 && p.move_slot==3);
}
int main(void)
{
    SG_View v; SG_PublicBattleObservation o; SG_Proposal p={0};
    fixture(&v,&o); parity(&v,&o,2,1);
    assert(sg_rank_damage_best(&v,&o,&p)==0); /* old API unchanged */
    o.effect_quarters[0][1]=0; parity(&v,&o,1,1);
    o.effect_quarters[1][1]=0; parity(&v,&o,0,0);
    fixture(&v,&o); v.permitted_move_mask=1; parity(&v,&o,1,0);
    fixture(&v,&o); o.effect_known_move_mask=1; o.effect_quarters[1][1]=0;
    parity(&v,&o,2,1); /* unknown is neutral */
    fixture(&v,&o); o.effect_quarters[0][1]=o.effect_quarters[1][1]=4;
    o.moves[1].displayed_base_power=100; parity(&v,&o,2,0); /* stable tie */
    fixture(&v,&o); o.classified_move_identity[0]=9;
    p.move_slot=3; assert(sg_rank_typed_damage_best(&v,&o,&p)==0 && p.move_slot==3);
    fixture(&v,&o); o.use_engine_type_effect_heuristic=false;
    o.engine_type_effect_bound=false; o.effect_known_move_mask=o.effect_public_foe_mask=0;
    o.effect_quarters[0][1]=o.effect_quarters[1][1]=0;
    o.use_public_type_heuristic=o.type_heuristic_bound=true;
    o.owned_move_type[0]=SG_TYPE_NORMAL; o.owned_move_type[1]=SG_TYPE_DARK;
    o.public_foe_type_mask=2; o.foe_type1[1]=SG_TYPE_GHOST;
    parity(&v,&o,1,1);
    o.type_heuristic_bound=false; assert(sg_rank_typed_damage_best(&v,&o,&p)==0);
    q12_cases();
    puts("PASS: type-aware best move parity, immunity, masks, unknowns, ties and legacy API; UQ4.12 triple-type range and overflow checks");
    return 0;
}
