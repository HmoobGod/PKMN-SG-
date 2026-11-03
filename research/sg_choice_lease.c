#include "sg_choice_lease.h"
#include <limits.h>
#include <stddef.h>
void sg_lease_init(SG_ChoiceLease *l) { if(l)*l=(SG_ChoiceLease){0}; }
void sg_lease_on_untrusted_transition(SG_ChoiceLease *l) {
 if(l && l->state!=SG_LEASE_POISONED)l->state=SG_LEASE_IDLE;
}
bool sg_lease_on_buffer_a_copy(SG_ChoiceLease *l,uint32_t actor,uint32_t opcode,uint32_t size,bool original_copy_executed) {
 if(!l||l->state==SG_LEASE_POISONED)return false;
 /* Opponent copies do not open/close an actor0 lease. Positive ownership is not implied. */
 if(actor!=0u)return false;
 /* Any new actor0 event replaces the previous lease, even if request bytes repeat. */
 l->state=SG_LEASE_IDLE;
 if(!original_copy_executed||opcode!=19u||size!=44u)return false;
 if(l->epoch==UINT64_MAX){l->state=SG_LEASE_POISONED;return false;}
 ++l->epoch;l->actor=0;l->state=SG_LEASE_STAGED;return true;
}
bool sg_lease_on_original_pending(SG_ChoiceLease *l,uint64_t epoch,uint32_t actor,uint32_t pending_word,uint32_t opcode,bool same_original_request) {
 if(!l||l->state==SG_LEASE_POISONED)return false;
 /* Actor1 pending is not evidence for actor0; preserve its staged lease. */
 if(actor!=0u)return false;
 /* An unexpected player-side event is untrusted and invalidates the proposal. */
 if(l->state!=SG_LEASE_STAGED||l->epoch!=epoch||l->actor!=0u||
    pending_word!=1u||opcode!=19u||!same_original_request){
   l->state=SG_LEASE_IDLE;return false;
 }
 l->state=SG_LEASE_OPEN;return true;
}
bool sg_lease_on_terminal(SG_ChoiceLease *l,uint64_t epoch) {
 if(!l||l->state==SG_LEASE_POISONED)return false;
 if(l->state==SG_LEASE_IDLE||l->epoch!=epoch){l->state=SG_LEASE_IDLE;return false;}
 l->state=SG_LEASE_IDLE;return true;
}
bool sg_lease_claim_model(SG_ChoiceLease *l,const SG_ClaimEvidence *e) {
 if(!l||!e||l->state!=SG_LEASE_OPEN)return false;
 /* All positive claim inputs are HYPOTHETICAL, not supplied by live Smart AI. */
 if(e->epoch!=l->epoch||e->actor!=0u||e->pending_word!=1u||e->opcode!=19u||
 e->battle_flags!=4u||e->battler_count!=2u||e->controller_kind!=1u||
 e->controller_completion!=0x080625f9u||e->present_mask!=3u||
 e->move_slot>=4u||e->target!=1u||!e->own_move_id||e->own_move_id>=936u||
 e->request_move_id!=e->own_move_id||!e->pp||
 !e->fresh_copy_witness||!e->authoritative_player_owner||
 !e->complete_move_legality||!e->complete_target_legality||
 !e->original_native_emitter_exclusive)return false;
 l->state=SG_LEASE_CLAIMED;return true;
}