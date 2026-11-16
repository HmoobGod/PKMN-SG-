/* Synthetic host only: no game, emulator, ROM/save, CPU trace or native proof. */
#include "lifecycle_adapter.h"
#include <stdio.h>
#include <string.h>

static unsigned assertions=0u,failed=0u;
#define T(cond) do{assertions++;if(!(cond)){failed++;fprintf(stderr,"FAIL:%u %s\n",(unsigned)__LINE__,#cond);}}while(0)
typedef struct {
 R7Original original;
 R7Legal legal;
 unsigned reads,law_reads,mutate_pp;
 int read_result,law_result;
 char order[12];unsigned orders;
} Fake;
static int read_original(void *p,R7Original *o){
 Fake *f=p;f->reads++;
 if(f->orders<11u)f->order[f->orders++]='R';
 if(f->read_result!=1)return f->read_result;
 *o=f->original;return 1;
}
static int read_legal(void *p,const R7Original *before,R7Legal *l){
 Fake *f=p;f->law_reads++;
 if(f->orders<11u)f->order[f->orders++]='L';
 if(f->law_result!=1)return f->law_result;
 T(before->request_id==f->original.request_id);
 if(f->mutate_pp){f->original.pp[1]++;f->original.original_payload[13]++;}
 *l=f->legal;return 1;
}
static R7Host host(Fake *f){R7Host h={f,read_original,read_legal};return h;}
static void set_command(Fake *f,unsigned cmd,unsigned id){
 R7Original *o=&f->original;
 o->command=cmd;o->request_id=id;
 o->original_header[0]=o->original_payload[0]=(uint8_t)cmd;
 o->payload_length=cmd==17u?4u:40u;
 f->legal.request_id=id;
 if(cmd==19u){
  o->original_header[1]=o->original_header[2]=o->original_header[3]=0u;
  o->original_payload[1]=o->original_payload[2]=o->original_payload[3]=0u;
  for(unsigned i=0;i<4u;i++){
    o->original_payload[4u+2u*i]=(uint8_t)o->moves[i];
    o->original_payload[5u+2u*i]=(uint8_t)(o->moves[i]>>8);
    o->original_payload[12u+i]=o->pp[i];
    o->original_payload[16u+i]=o->pp[i];
  }
 }
}
static void setup(Fake *f){
 memset(f,0,sizeof *f);f->read_result=f->law_result=1;
 R7Original *o=&f->original;
 o->original_epoch=72u;o->request_id=101u;o->command=17u;
 o->battler=0u;o->owner_party=1u;o->foe_party=0u;
 o->turn=9u;o->resources=0x02001000u;o->flags=0x100u;
 o->player_owned=1u;o->wild_single=1u;o->auto_enabled=1u;o->foe_live=1u;
 o->moves[0]=247u;o->moves[1]=157u;o->moves[2]=92u;o->moves[3]=269u;
 o->pp[0]=20u;o->pp[1]=10u;o->pp[2]=10u;o->pp[3]=20u;
 set_command(f,17u,101u);
 R7Legal *l=&f->legal;
 l->original_epoch=72u;l->turn=9u;
 l->move_limitations_verified=l->target_helpers_verified=l->ineffectiveness_verified=1u;
 l->move_legal_mask=l->verified_foe_target_mask=15u;
 l->known_ineffective_mask=8u;
 l->priorities[0]=9u;l->priorities[1]=100u;l->priorities[2]=5u;l->priorities[3]=250u;
}
static void reset_count(Fake *f){f->reads=f->law_reads=f->orders=0u;memset(f->order,0,sizeof f->order);}
static R7LifecycleResult run(Fake *f,R7Lifecycle *state){R7Host h=host(f);reset_count(f);return r7_lifecycle_plan(&h,state);}
static void no_cert(R7LifecycleResult r){
 T(r.plan.native_move_accepted==0u);T(r.plan.native_manual_fallback_accepted==0u);
 T(r.plan.no_forced_switch_certified==0u);T(r.plan.production_authorized==0u);
}
static void check_defer(R7LifecycleResult r,R7LifecycleReason lc){
 T(r.plan.outcome==R7_DEFER);T(r.lifecycle_reason==lc);
 T(r.plan.action==R7_NO_ACTION);T(r.plan.slot==R7_NO_SLOT);
 T(r.plan.manual_defer_requested==1u);no_cert(r);
}
static void check_success(R7LifecycleResult r,R7Outcome expected){
 T(r.lifecycle_reason==R7_LC_OK);T(r.plan.outcome==expected);
 T(r.plan.action==(expected==R7_FIGHT?0u:10u));
 T(r.plan.slot==1u);T(r.plan.manual_defer_requested==0u);no_cert(r);
}
static void test_two_stage_replay_and_strict_callback(void){
 Fake f;setup(&f);R7Lifecycle state; r7_lifecycle_init(&state);
 R7LifecycleResult r=run(&f,&state);check_success(r,R7_FIGHT);
 T(f.reads==2u);T(f.law_reads==1u);T(strcmp(f.order,"RLR")==0);
 T(state.initialized==1u&&state.epoch==72u&&state.ticket.pending==1u);
 T(state.seen_count==1u&&state.seen_ids[0]==101u);
 set_command(&f,19u,102u);r=run(&f,&state);check_success(r,R7_MOVE);
 T(state.ticket.pending==0u&&state.seen_count==2u&&state.seen_ids[1]==102u);
 r=run(&f,&state);check_defer(r,R7_LC_DUPLICATE);
 T(state.seen_count==2u&&state.quarantined==1u);
 /* Replay detection is sticky, even if a fresh lease/other id appears. */
 set_command(&f,17u,103u);r=run(&f,&state);
 check_defer(r,R7_LC_QUARANTINED);T(f.reads==0u);
 /* A synthetic host returning 2 is not an authenticated read. */
 setup(&f);r7_lifecycle_init(&state);f.read_result=2;
 r=run(&f,&state);check_defer(r,R7_LC_BAD_READ);
 T(state.seen_count==0u && state.initialized==0u);
 f.read_result=1;f.law_result=2;
 r=run(&f,&state);check_defer(r,R7_LC_ADAPTER_DEFER);
 T(r.plan.reason==R7_NO_ENGINE_LEGALITY&&state.seen_count==0u);
 T(state.quarantined==1u&&state.initialized==1u);
 f.law_result=1;r=run(&f,&state);
 check_defer(r,R7_LC_QUARANTINED);T(f.reads==0u);
 /* A callback-mutated original buffer must not consume request ownership. */
 setup(&f);r7_lifecycle_init(&state);f.mutate_pp=1u;
 r=run(&f,&state);check_defer(r,R7_LC_ADAPTER_DEFER);
 T(r.plan.reason==R7_ORIGINAL_REQUEST_CHANGED);
 T(state.seen_count==0u && state.ticket.pending==0u&&state.quarantined==1u);
}
static void test_stale_ticket_and_fail_closed_rearm(void){
 Fake f;setup(&f);R7Lifecycle s; r7_lifecycle_init(&s);
 check_success(run(&f,&s),R7_FIGHT);
 /* A different, overlapping command 17 is a sticky manual barrier. */
 set_command(&f,17u,102u);
 R7LifecycleResult r=run(&f,&s);
 check_defer(r,R7_LC_ADAPTER_DEFER);
 T(r.plan.reason==R7_STAGE_CONTINUITY_FAILED&&s.ticket.pending==1u);
 T(s.seen_count==1u&&s.quarantined==1u);
 f.original.original_epoch=f.legal.original_epoch=73u;
 set_command(&f,17u,201u);
 r=run(&f,&s);check_defer(r,R7_LC_QUARANTINED);
 T(s.quarantined==1u&&s.epoch==72u&&s.ticket.pending==1u);
 T(f.reads==0u);
 R7RecoveryEvidence p={72u,73u,1u,1u,1u};R7Host h=host(&f);
 T(r7_lifecycle_rearm(&h,&s,NULL)==0);
 T(r7_lifecycle_rearm(NULL,&s,&p)==0);
 for(unsigned j=0;j<3u;j++){
  R7RecoveryEvidence bad=p;
  if(j==0u)bad.previous_battle_finished_verified=0u;
  if(j==1u)bad.original_controller_rearmed_verified=0u;
  if(j==2u)bad.original_response_queue_empty_verified=0u;
  T(r7_lifecycle_rearm(&h,&s,&bad)==0);
  T(s.quarantined==1u&&s.ticket.pending==1u);
 }
 R7RecoveryEvidence bad=p;bad.new_epoch=72u;
 T(r7_lifecycle_rearm(&h,&s,&bad)==0);
 bad=p;bad.previous_epoch=71u;T(r7_lifecycle_rearm(&h,&s,&bad)==0);
 f.read_result=2;T(r7_lifecycle_rearm(&h,&s,&p)==0);
 f.read_result=1;f.original.player_owned=0;
 T(r7_lifecycle_rearm(&h,&s,&p)==0);
 f.original.player_owned=1;
 f.original.original_epoch=74u;T(r7_lifecycle_rearm(&h,&s,&p)==0);
 f.original.original_epoch=73u;
 T(r7_lifecycle_rearm(&h,&s,&p)==1);
 T(s.quarantined==0u&&s.seen_count==0u&&s.epoch==73u&&s.ticket.pending==0u);
 T(r7_lifecycle_rearm(&h,&s,&p)==0);
 r=run(&f,&s);check_success(r,R7_FIGHT);
 T(s.ticket.pending==1u&&s.seen_ids[0]==201u);
 /* A fresh pending ticket expires safely at a NEW observed engine epoch.
  * Expiry does not authorize automatic action in that epoch. */
 f.original.original_epoch=f.legal.original_epoch=74u;
 set_command(&f,17u,203u);
 r=run(&f,&s);check_defer(r,R7_LC_EPOCH_ADVANCE);
 T(s.quarantined==1u&&s.epoch==73u&&s.ticket.pending==1u);
 r=run(&f,&s);check_defer(r,R7_LC_QUARANTINED);
}
static void test_api_errors_stick_after_started_epoch(void){
 Fake f;setup(&f);R7Lifecycle s;r7_lifecycle_init(&s);
 check_success(run(&f,&s),R7_FIGHT);
 /* Missing one callback must fail and disable further automatic requests. */
 R7Host bad=host(&f);bad.read_engine_legality=NULL;
 R7LifecycleResult r=r7_lifecycle_plan(&bad,&s);
 check_defer(r,R7_LC_BAD_API);T(s.quarantined==1u);
 set_command(&f,19u,102u);
 check_defer(run(&f,&s),R7_LC_QUARANTINED);
 /* A read failure after an emitted candidate is also sticky. */
 setup(&f);r7_lifecycle_init(&s);check_success(run(&f,&s),R7_FIGHT);
 f.read_result=2;
 r=run(&f,&s);check_defer(r,R7_LC_BAD_READ);T(s.quarantined==1u);
 f.read_result=1;check_defer(run(&f,&s),R7_LC_QUARANTINED);
 /* Contradictory read after a prior stage cannot be retried automatically. */
 setup(&f);r7_lifecycle_init(&s);check_success(run(&f,&s),R7_FIGHT);
 f.original.request_id=0u;
 r=run(&f,&s);check_defer(r,R7_LC_BAD_ORIGINAL);
 T(s.quarantined==1u);
 f.original.request_id=102u;
 check_defer(run(&f,&s),R7_LC_QUARANTINED);
}
static void test_explicit_abandon_and_bounded_ledger(void){
 Fake f;setup(&f);R7Lifecycle s; r7_lifecycle_init(&s);
 T(r7_lifecycle_abandon(&s)==0);
 check_success(run(&f,&s),R7_FIGHT);
 T(r7_lifecycle_abandon(&s)==1);
 T(s.quarantined==1u&&s.ticket.pending==1u);
 set_command(&f,19u,102u);
 check_defer(run(&f,&s),R7_LC_QUARANTINED);
 T(s.ticket.pending==1u);
 /* Re-arm new, independently reported epoch and exhaust 64 unique records. */
 R7RecoveryEvidence p={72u,73u,1u,1u,1u};
 f.original.original_epoch=f.legal.original_epoch=73u;
 set_command(&f,17u,200u);R7Host h=host(&f);
 T(r7_lifecycle_rearm(&h,&s,&p)==1);
 for(unsigned i=0u;i<R7_LIFECYCLE_SEEN_CAP/2u;i++) {
  set_command(&f,17u,200u+2u*i);check_success(run(&f,&s),R7_FIGHT);
  set_command(&f,19u,201u+2u*i);check_success(run(&f,&s),R7_MOVE);
 }
 T(s.seen_count==R7_LIFECYCLE_SEEN_CAP);
 T(s.ticket.pending==0u);
 set_command(&f,17u,400u);
 check_defer(run(&f,&s),R7_LC_LEDGER_FULL);
 T(s.quarantined==1u&&s.seen_count==R7_LIFECYCLE_SEEN_CAP);
 check_defer(run(&f,&s),R7_LC_QUARANTINED);
 /* Empty state cannot be used with unverified input. */
 T(r7_lifecycle_plan(NULL,&s).lifecycle_reason==R7_LC_BAD_API);
 T(r7_lifecycle_plan(&h,NULL).lifecycle_reason==R7_LC_BAD_API);
}
int main(void){
 test_two_stage_replay_and_strict_callback();
 test_stale_ticket_and_fail_closed_rearm();
 test_explicit_abandon_and_bounded_ledger();
 test_api_errors_stick_after_started_epoch();
 if(failed)fprintf(stderr,"R7 R6 lifecycle: %u/%u checks failed\n",failed,assertions);
 else printf("R7 R6 lifecycle: %u/%u assertions passed (synthetic only)\n",assertions,assertions);
 return failed?1:0;
}
