#ifndef SG_CHOICE_LEASE_H
#define SG_CHOICE_LEASE_H
#include <stdbool.h>
#include <stdint.h>
/* ROM-free reference only: a lease is NOT engine action authority. */
typedef enum {
 SG_LEASE_IDLE=0, SG_LEASE_OPEN=1, SG_LEASE_CLAIMED=2,
 SG_LEASE_POISONED=3, SG_LEASE_STAGED=4
} SG_LeaseState;
typedef struct { uint64_t epoch; SG_LeaseState state; uint8_t actor; } SG_ChoiceLease;
typedef struct {
 uint64_t epoch;
 uint32_t actor,pending_word,opcode,battle_flags,battler_count;
 uint32_t controller_kind,controller_completion,present_mask;
 uint32_t move_slot,target,own_move_id,request_move_id,pp;
 bool fresh_copy_witness,authoritative_player_owner,complete_move_legality;
 bool complete_target_legality,original_native_emitter_exclusive;
} SG_ClaimEvidence;
void sg_lease_init(SG_ChoiceLease *lease);
/* A completed buffer-A copy only STAGES a request; pending is not set yet. */
bool sg_lease_on_buffer_a_copy(SG_ChoiceLease *lease,uint32_t actor,uint32_t opcode,uint32_t size,bool original_copy_executed);
/* Only a paired, original actor-0 pending transition can OPEN a staged lease. */
bool sg_lease_on_original_pending(SG_ChoiceLease *lease,uint64_t epoch,uint32_t actor,uint32_t pending_word,uint32_t opcode,bool same_original_request);
bool sg_lease_on_terminal(SG_ChoiceLease *lease,uint64_t epoch);
void sg_lease_on_untrusted_transition(SG_ChoiceLease *lease);
bool sg_lease_claim_model(SG_ChoiceLease *lease,const SG_ClaimEvidence *e);
#endif