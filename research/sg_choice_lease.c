#include "sg_choice_lease.h"
#include <limits.h>
#include <stddef.h>
void sg_lease_init(SG_ChoiceLease *l) { if(l)*l=(SG_ChoiceLease){0}; }
void sg_lease_on_untrusted_transition(SG_ChoiceLease *l) {
 if(l && l->state!=SG_LEASE_POISONED)l->state=SG_LEASE_IDLE;
}
bool sg_lease_on_buffer_a_copy(SG_ChoiceLease *l,uint32_t actor,uint32_t opcode,uint32_t size,bool original_copy_executed) {
 if(!l||l->state==SG_LEASE_POISONED)return false;
 /* Opponent copies do not open/close player leases. Caller must still prove ownership. */
 if(actor!=0u)return false;
 /* Any new actor-0 buffer-A event replaces the previous lease, even if bytes repeat. */
 l->state=SG_LEASE_IDLE;
 if(!original_copy_executed||opcode!=19u||size!=44u)return false;
 if(l->epoch==UINT64_MAX){l->state=SG_LEASE_POISONED;return false;}
 ++l->epoch;l->actor=0;l->state=SG_LEASE_OPEN;return true;
}
bool sg_lease_on_terminal(SG_ChoiceLease *l,uint64_t epoch) {
 if(!l||l->state==SG_LEASE_POISONED)return false;
 if(l->state==SG_LEASE_IDLE||l->epoch!=epoch){l->state=SG_LEASE_IDLE;return false;}
 l->state=SG_LEASE_IDLE;return true;
}
bool sg_lease_claim_model(SG_ChoiceLease *l,const SG_ClaimEvidence *e) {
 if(!l||!e||l->state!=SG_LEASE_OPEN)return false;
 /* Positive witnesses are HYPOTHETICAL inputs. The live scorer supplies none. */
 if(e->epoch!=l->epoch||e->actor!=0u||!(e->pending_word&1u)||e->opcode!=19u||
 e->battle_flags!=4u||e->battler_count!=2u||e->controller_kind!=1u||
 e->controller_completion!=0x080625f9u||e->present_mask!=3u||
 e->move_slot>=4u||e->target!=1u||!e->own_move_id||e->own_move_id>=936u||
 e->request_move_id!=e->own_move_id||!e->pp||
 !e->fresh_copy_witness||!e->authoritative_player_owner||
 !e->complete_move_legality||!e->complete_target_legality||
 !e->original_native_emitter_exclusive)return false;
 l->state=SG_LEASE_CLAIMED;return true;
}
