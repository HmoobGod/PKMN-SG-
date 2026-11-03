#include "sg_choice_lease.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
static unsigned checks;
static void ok(bool b){assert(b);++checks;}
static SG_ClaimEvidence evidence(uint64_t epoch){
 return (SG_ClaimEvidence){.epoch=epoch,.actor=0,.pending_word=1,.opcode=19,
 .battle_flags=4,.battler_count=2,.controller_kind=1,
 .controller_completion=0x080625f9u,.present_mask=3,.move_slot=0,.target=1,
 .own_move_id=157,.request_move_id=157,.pp=8,.fresh_copy_witness=true,
 .authoritative_player_owner=true,.complete_move_legality=true,
 .complete_target_legality=true,.original_native_emitter_exclusive=true};
}
int main(void){
 SG_ChoiceLease l;sg_lease_init(&l);
 ok(l.state==SG_LEASE_IDLE&&l.epoch==0);
 ok(!sg_lease_claim_model(&l,&(SG_ClaimEvidence){0}));
 ok(!sg_lease_on_buffer_a_copy(&l,1,19,44,true));
 ok(l.epoch==0&&l.state==SG_LEASE_IDLE);
 ok(sg_lease_on_buffer_a_copy(&l,0,19,44,true));
 SG_ClaimEvidence e=evidence(l.epoch);
 ok(l.state==SG_LEASE_STAGED);
 ok(!sg_lease_claim_model(&l,&e)); /* completed copy is NOT pending */
 ok(!sg_lease_on_original_pending(&l,e.epoch,1,1,19,true));
 ok(l.state==SG_LEASE_STAGED);
 ok(sg_lease_on_original_pending(&l,e.epoch,0,1,19,true));
 ok(l.state==SG_LEASE_OPEN);
#define DENY(f,v) do { SG_ClaimEvidence n=e;n.f=(v);ok(!sg_lease_claim_model(&l,&n));ok(l.state==SG_LEASE_OPEN); } while(0)
 DENY(fresh_copy_witness,false);
 DENY(authoritative_player_owner,false);
 DENY(complete_move_legality,false);
 DENY(complete_target_legality,false);
 DENY(original_native_emitter_exclusive,false);
 DENY(epoch,0);DENY(actor,2);DENY(pending_word,0);DENY(pending_word,3);DENY(opcode,20);
 DENY(battle_flags,13);DENY(battler_count,4);DENY(controller_kind,2);
 DENY(controller_completion,0x08065e39u);DENY(present_mask,1);
 DENY(move_slot,4);DENY(target,0);DENY(own_move_id,0);DENY(own_move_id,936);
 DENY(request_move_id,325);DENY(pp,0);
#undef DENY
 ok(sg_lease_claim_model(&l,&e));ok(!sg_lease_claim_model(&l,&e));
 ok(l.state==SG_LEASE_CLAIMED);
 ok(sg_lease_on_terminal(&l,e.epoch));
 ok(!sg_lease_claim_model(&l,&e));ok(!sg_lease_on_terminal(&l,e.epoch));
 /* Same 44-byte payload can be reused in a new original native request. */
 ok(sg_lease_on_buffer_a_copy(&l,0,19,44,true));
 SG_ClaimEvidence newer=evidence(l.epoch);
 ok(newer.epoch!=e.epoch);ok(!sg_lease_claim_model(&l,&newer));
 ok(l.state==SG_LEASE_STAGED);ok(!sg_lease_on_original_pending(&l,e.epoch,0,1,19,true));
 ok(l.state==SG_LEASE_IDLE);ok(!sg_lease_claim_model(&l,&newer));
 ok(sg_lease_on_buffer_a_copy(&l,0,19,44,true));
 uint64_t old=l.epoch;
 ok(!sg_lease_on_buffer_a_copy(&l,2,19,44,true));
 ok(l.state==SG_LEASE_STAGED&&l.epoch==old);
 ok(!sg_lease_on_buffer_a_copy(&l,0,20,44,true));
 ok(l.state==SG_LEASE_IDLE);
 ok(sg_lease_on_buffer_a_copy(&l,0,19,44,true));
 ok(!sg_lease_on_buffer_a_copy(&l,0,19,44,false));
 ok(l.state==SG_LEASE_IDLE);
 ok(sg_lease_on_buffer_a_copy(&l,0,19,44,true));
 sg_lease_on_untrusted_transition(&l);ok(l.state==SG_LEASE_IDLE);
 /* Adversarial pending transitions cannot open a stale/inconsistent lease. */
 for(int i=0;i<4;i++){
   ok(sg_lease_on_buffer_a_copy(&l,0,19,44,true));
   uint64_t id=l.epoch;
   uint32_t pending=(i==0)?0:(i==1)?3:1;
   uint32_t opcode=(i==2)?20:19;
   bool same=(i!=3);
   ok(!sg_lease_on_original_pending(&l,id,0,pending,opcode,same));
   ok(l.state==SG_LEASE_IDLE);
 }
 ok(sg_lease_on_buffer_a_copy(&l,0,19,44,true));
 old=l.epoch;
 ok(sg_lease_on_terminal(&l,old)); /* cancellation before pending */
 ok(!sg_lease_on_original_pending(&l,old,0,1,19,true));
 ok(sg_lease_on_buffer_a_copy(&l,0,19,44,true));
 l.epoch=UINT64_MAX;
 ok(!sg_lease_on_buffer_a_copy(&l,0,19,44,true));
 ok(l.state==SG_LEASE_POISONED);
 ok(!sg_lease_on_buffer_a_copy(&l,0,19,44,true));
 sg_lease_on_untrusted_transition(&l);
 ok(l.state==SG_LEASE_POISONED);
 ok(!sg_lease_claim_model(&l,&e));
 ok(!sg_lease_on_original_pending(&l,UINT64_MAX,0,1,19,true));
 ok(!sg_lease_on_terminal(&l,UINT64_MAX));
 ok(!sg_lease_on_buffer_a_copy(NULL,0,19,44,true));
 ok(!sg_lease_on_original_pending(NULL,1,0,1,19,true));
 ok(!sg_lease_claim_model(NULL,&e));
 ok(!sg_lease_claim_model(&l,NULL));
 ok(!sg_lease_on_terminal(NULL,1));
 sg_lease_init(NULL);sg_lease_on_untrusted_transition(NULL);
 printf("PASS model-only staged/armed lease: %u assertions (no emitter)\n",checks);
 return 0;
}