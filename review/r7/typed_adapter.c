#include "typed_adapter.h"
#include <string.h>

typedef struct {
    const R7TypedHost *host;
    R7ReadFightReceipt receipt;
    uint32_t unusable_mask;
} TypedContext;

static int typed_read(void *ctx, R7Original *out)
{
    const R7TypedHost *h=((TypedContext *)ctx)->host;
    return h->engine.read_original(h->engine.ctx,out);
}

/* Existing R7 calls this between its original request reads. Restrict
 * eligibility to one scored slot; never add a legality or target bit. */
static int typed_legal(void *ctx, const R7Original *s, R7Legal *out)
{
    const TypedContext *c=ctx;
    const R7TypedHost *h=c->host;
    R7Legal legal={0};
    SG_PublicBattleObservation o={0};
    if (h->engine.read_engine_legality(h->engine.ctx,s,&legal)!=1 ||
        legal.original_epoch!=s->original_epoch ||
        legal.request_id!=s->request_id || legal.turn!=s->turn ||
        legal.move_limitations_verified!=1u ||
        legal.target_helpers_verified!=1u || legal.ineffectiveness_verified!=1u ||
        ((legal.move_legal_mask|legal.verified_foe_target_mask|
          legal.known_ineffective_mask)&0xf0u) || s->turn==UINT32_MAX)
        return 0;
    /* The already executed restriction mask can only REMOVE eligibility.
     * All other positive engine legality and target proofs remain required. */
    if (c->receipt)
        legal.move_legal_mask&=(uint8_t)~c->unusable_mask;
    if (h->read_rank_observation(h->engine.ctx,s,&o)!=1)
        return 0;
    /* Use the mod's positively bound type chart, not the fixed Gen-IV
     * fallback. A normalized turn token is original turn+1, including turn 0. */
    if (o.battle_token!=s->original_epoch || o.turn_token!=s->turn+1u ||
        o.choice_token!=s->request_id || o.actor!=0u ||
        !o.use_engine_type_effect_heuristic || !o.engine_type_effect_bound ||
        !o.require_owned_move_identity_proof || !o.require_non_self_ko_proof ||
        o.use_public_support_tactics || o.use_public_type_heuristic ||
        o.effect_public_foe_mask!=2u)
        return 0;
    SG_View v={0};
    v.battle_token=s->original_epoch;v.turn_token=s->turn+1u;
    v.choice_token=s->request_id;v.actor=0;v.controller=1;
    v.phase=2;v.battler_count=2;v.battle_mode_flags=4;
    v.supported_mode=true; /* normalized source model, not native mode proof */
    unsigned eligible=legal.move_legal_mask & legal.verified_foe_target_mask &
                      (unsigned)~legal.known_ineffective_mask;
    for (unsigned i=0;i<4u;i++) {
        unsigned bit=1u<<i;
        if(o.owned_move_identity[i]!=s->moves[i] ||
           o.classified_move_identity[i]!=s->moves[i]) return 0;
        if (!(eligible&bit) || !s->pp[i] || !s->moves[i] ||
            s->moves[i]==UINT16_MAX || !o.moves[i].known_damaging_move ||
            (o.known_self_ko_move_mask&bit)) continue;
        if (!(o.known_non_self_ko_move_mask&bit) ||
            !(o.effect_known_move_mask&bit)) return 0;
        v.permitted_move_mask|=(uint8_t)bit;
        v.permitted_targets[i]=2u;
    }
    SG_Proposal p={0};
    if (!sg_rank_typed_damage_best(&v,&o,&p) ||
        p.action!=SG_USE_MOVE || p.actor!=0u || p.target!=1u ||
        p.move_slot>=4u || !(v.permitted_move_mask&(1u<<p.move_slot)))
        return 0;
    /* Pass a subset to the existing R5/R7 guard. In particular, an immunity
     * or no scored move cannot accidentally fall back to priority zero. */
    legal.move_legal_mask&=(uint8_t)(1u<<p.move_slot);
    memset(legal.priorities,0,sizeof legal.priorities);
    legal.priorities[p.move_slot]=1u;
    *out=legal;
    return 1;
}

R7Plan r7_plan_typed(const R7TypedHost *h,R7Lease *lease,R7FightTicket *ticket)
{
    if(!h || !h->engine.read_original || !h->engine.read_engine_legality ||
       !h->read_rank_observation)
        return r7_plan(NULL,lease,ticket);
    TypedContext c={h,0,0};
    R7Host wrapped={&c,typed_read,typed_legal};
    return r7_plan(&wrapped,lease,ticket);
}

static int typed_receipt(void *ctx,const R7Original *p,R7OriginalFightReceipt *out)
{
    TypedContext *c=ctx;
    if (c->receipt(c->host->engine.ctx,p,out)!=1) return 0;
    c->unusable_mask=out->unusable_mask;
    return 1;
}
R7Plan r7_plan_typed_after_original_fight(const R7TypedHost *h,R7Lease *lease,
                                         R7ReadFightReceipt receipt)
{
    if (!h || !h->engine.read_original || !h->engine.read_engine_legality ||
        !h->read_rank_observation || !receipt)
        return r7_plan(NULL,lease,NULL);
    TypedContext c={h,receipt,0};
    R7Host wrapped={&c,typed_read,typed_legal};
    return r7_plan_after_original_fight(&wrapped,lease,typed_receipt,&c);
}
