#include "../source-first/player0_fail_closed_guard.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static unsigned assertions=0u;
#define CHECK(p) do{ assertions++; if(!(p)){fprintf(stderr,"assertion failed line %d: %s\n",__LINE__,#p);exit(1);} }while(0)
static struct sg_guard_input good(void){
 struct sg_guard_input a;memset(&a,0,sizeof(a));
 a.battler=0; a.command=SG_COMMAND_CHOOSE_MOVE; a.player_owned=1;
 a.wild_single=1; a.auto_enabled=1; a.foe_is_live_enemy=1; a.engine_command_authenticated=1;
 a.owner_lease_unconsumed=1; a.request_id_before=a.request_id_after=99;
 a.turn_before=a.turn_after=5; a.owner_party_before=a.owner_party_after=1;
 a.foe_party_before=a.foe_party_after=2; a.resources_before=a.resources_after=0x02010000;
 a.controller_flags_before=a.controller_flags_after=1;
 a.current_buffer_matches_original=a.original_menu_payload_matches=1;
 a.move_limitations_evaluated=a.target_helpers_evaluated=1;
 a.moves[0]=10; a.moves[1]=20; a.moves[2]=30; a.moves[3]=40;
 a.pp[0]=20; a.pp[1]=10; a.pp[2]=10; a.pp[3]=20;
 a.legal_move_mask=a.verified_foe_target_mask=15;
 a.relative_priority[0]=3; a.relative_priority[1]=10;
 a.relative_priority[2]=5; a.relative_priority[3]=15;
 return a;
}
static void expect_defer(struct sg_guard_input a, enum sg_guard_reason reason){
 struct sg_guard_output b=sg_guard_evaluate(&a);
 CHECK(b.outcome==SG_DEFER_TO_ORIGINAL_MANUAL);
 CHECK(b.reason==reason);
 CHECK(b.requires_verified_manual_controller==1);
 CHECK(b.slot==SG_NO_SLOT && b.action==SG_NO_ACTION);
 CHECK(b.native_accepted==0);
}
int main(void){
 struct sg_guard_input a=good();struct sg_guard_output x=sg_guard_evaluate(&a);
 CHECK(x.outcome==SG_PROPOSE_MOVE && x.action==SG_ACTION_MOVE && x.slot==3);
 CHECK(x.requires_verified_manual_controller==0 && x.native_accepted==0);
 a.command=SG_COMMAND_CHOOSE_ACTION; x=sg_guard_evaluate(&a);
 CHECK(x.outcome==SG_PROPOSE_FIGHT && x.action==SG_ACTION_FIGHT && x.slot==3);
 /* A Taunt-like move is skipped ONLY when the engine-backed adapter has
  * independently established redundancy; inferred flags are not enough. */
 a=good();a.known_ineffective_mask=8; x=sg_guard_evaluate(&a);
 CHECK(x.outcome==SG_PROPOSE_MOVE && x.slot==1);
 a=good();a.relative_priority[0]=15;a.relative_priority[3]=15;
 x=sg_guard_evaluate(&a);CHECK(x.slot==0); /* stable tie-break */
 a=good();a.battler=1;expect_defer(a,SG_GUARD_UNSUPPORTED_OWNER);
 a=good();a.player_owned=0;expect_defer(a,SG_GUARD_UNSUPPORTED_OWNER);
 a=good();a.wild_single=0;expect_defer(a,SG_GUARD_UNSUPPORTED_BATTLE);
 a=good();a.partner_present=1;expect_defer(a,SG_GUARD_UNSUPPORTED_BATTLE);
 a=good();a.doubles_or_multi=1;expect_defer(a,SG_GUARD_UNSUPPORTED_BATTLE);
 a=good();a.auto_enabled=0;expect_defer(a,SG_GUARD_UNSUPPORTED_BATTLE);
 a=good();a.foe_is_live_enemy=0;expect_defer(a,SG_GUARD_UNSUPPORTED_BATTLE);
 a=good();a.command=0;expect_defer(a,SG_GUARD_UNSUPPORTED_COMMAND);
 a=good();a.command=18;expect_defer(a,SG_GUARD_UNSUPPORTED_COMMAND);
 a=good();a.engine_command_authenticated=0;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.owner_lease_unconsumed=0;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.request_id_before=0;a.request_id_after=0;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.request_id_after=100;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.turn_after=6;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.owner_party_after=2;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.foe_party_after=3;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.resources_after=0;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.resources_before=0;a.resources_after=0;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.controller_flags_after=2;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.current_buffer_matches_original=0;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.original_menu_payload_matches=0;expect_defer(a,SG_GUARD_STALE_REQUEST);
 a=good();a.move_limitations_evaluated=0;expect_defer(a,SG_GUARD_MISSING_ENGINE_LEGALITY);
 a=good();a.target_helpers_evaluated=0;expect_defer(a,SG_GUARD_MISSING_ENGINE_LEGALITY);
 a=good();a.legal_move_mask=0;expect_defer(a,SG_GUARD_NO_ELIGIBLE_MOVE);
 a=good();a.verified_foe_target_mask=0;expect_defer(a,SG_GUARD_NO_ELIGIBLE_MOVE);
 a=good();a.known_ineffective_mask=15;expect_defer(a,SG_GUARD_NO_ELIGIBLE_MOVE);
 a=good();a.legal_move_mask=0x8f;expect_defer(a,SG_GUARD_MISSING_ENGINE_LEGALITY);
 a=good();a.verified_foe_target_mask=0x80;expect_defer(a,SG_GUARD_MISSING_ENGINE_LEGALITY);
 a=good();a.known_ineffective_mask=0x80;expect_defer(a,SG_GUARD_MISSING_ENGINE_LEGALITY);
 a=good();for(unsigned i=0;i<4;i++)a.pp[i]=0;expect_defer(a,SG_GUARD_NO_ELIGIBLE_MOVE);
 a=good();a.pp[3]=0;x=sg_guard_evaluate(&a);CHECK(x.outcome==SG_PROPOSE_MOVE && x.slot==1);
 a=good();a.moves[3]=0;x=sg_guard_evaluate(&a);CHECK(x.outcome==SG_PROPOSE_MOVE && x.slot==1);
 a=good();a.moves[3]=UINT16_MAX;x=sg_guard_evaluate(&a);CHECK(x.outcome==SG_PROPOSE_MOVE && x.slot==1);
 a=good();a.legal_move_mask=7;x=sg_guard_evaluate(&a);CHECK(x.slot==1);
 a=good();a.verified_foe_target_mask=7;x=sg_guard_evaluate(&a);CHECK(x.slot==1);
 a=good();a.command=255;expect_defer(a,SG_GUARD_UNSUPPORTED_COMMAND);
 x=sg_guard_evaluate(NULL);CHECK(x.outcome==SG_DEFER_TO_ORIGINAL_MANUAL && x.native_accepted==0 && x.action==SG_NO_ACTION);
 printf("PASS %u source-only C assertions; no original game or menu integration\n",assertions);
 return 0;
}
