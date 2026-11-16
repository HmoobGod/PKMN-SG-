/* Synthetic fixtures only: reuse the already-tested R7 R4 fake controller.
 * The original R7 suite is also executed before these added cases. */
#define main r7_r4_original_test_main
#include "test_engine_adapter.c"
#undef main
#include "session_lifecycle.h"

typedef struct {
  R7EpochBoundary boundary;
  int result;
  unsigned calls;
} BoundaryFake;
static int check_boundary(void *ctx,R7EpochBoundary *out){
  BoundaryFake *f=(BoundaryFake *)ctx;
  f->calls++;
  *out=f->boundary;
  return f->result;
}
typedef struct {
  int result;
  unsigned calls;
  uint32_t observed_epoch;
  uint16_t observed_move;
} ManualFake;
static int check_manual(void *ctx,const R7FightTicket *ticket){
  ManualFake *f=(ManualFake *)ctx;
  f->calls++;
  f->observed_epoch=ticket->epoch;
  f->observed_move=ticket->planned_move;
  return f->result;
}
static R7Plan session_perform(Fake *f,R7Lease *lease,R7Session *session){
  f->reads=f->law_reads=f->call_count=0;
  memset(f->call_order,0,sizeof f->call_order);
  R7Host host={f,rd,law};
  return r7_session_plan(&host,lease,session);
}
static void check_session_defer(R7Plan p,R7Reason reason){
  CHECK(p.outcome==R7_DEFER && p.reason==reason);
  CHECK(p.action==R7_NO_ACTION && p.slot==R7_NO_SLOT);
  CHECK(p.manual_defer_requested==1u);
  CHECK(p.native_move_accepted==0u);
  CHECK(p.native_manual_fallback_accepted==0u);
  CHECK(p.no_forced_switch_certified==0u && p.production_authorized==0u);
}
static void test_fresh_lease_replay_and_two_stage(void){
  Fake f;setup(&f);R7Session s={0};R7Lease l={72,101,0};
  CHECK(r7_session_init(&s,72u)==1);
  R7Plan p=session_perform(&f,&l,&s);
  CHECK(p.outcome==R7_FIGHT && p.action==0u);
  CHECK(s.count==1u && s.ticket.pending==1u && l.consumed==1u);
  CHECK(s.consumed[0].epoch==72u && s.consumed[0].request_id==101u);
  /* Initializer cannot be reused to clear the accepted-request ledger. */
  CHECK(r7_session_init(&s,72u)==0);
  CHECK(r7_session_init(&s,73u)==0);
  CHECK(s.count==1u && s.ticket.pending==1u && s.epoch==72u);
  R7Lease fresh={72,101,0};R7FightTicket old=s.ticket;
  p=session_perform(&f,&fresh,&s);
  check_session_defer(p,R7_BAD_LEASE);
  CHECK(fresh.consumed==0u && s.count==1u);
  CHECK(s.ticket.pending==old.pending && s.ticket.planned_move==old.planned_move);
  CHECK(f.law_reads==0u);
  choose_move(&f);f.before.request_id=f.after.request_id=f.legal.request_id=102u;
  l=(R7Lease){72,102,0};
  p=session_perform(&f,&l,&s);
  CHECK(p.outcome==R7_MOVE && p.action==10u && p.slot==1u);
  CHECK(l.consumed==1u && s.count==2u && s.ticket.pending==0u);
  expect_source_only_success(p);
  fresh=(R7Lease){72,102,0};
  p=session_perform(&f,&fresh,&s);
  check_session_defer(p,R7_BAD_LEASE);
  CHECK(fresh.consumed==0u && s.count==2u);
  /* A distinct new ChooseAction request may proceed after Move completed. */
  setup(&f);f.before.request_id=f.after.request_id=f.legal.request_id=103u;
  l=(R7Lease){72,103,0};
  p=session_perform(&f,&l,&s);
  CHECK(p.outcome==R7_FIGHT && s.count==3u && s.ticket.pending==1u);
  expect_source_only_success(p);
}
static void test_failed_proposals_never_record_requests(void){
  Fake f;setup(&f);R7Session s={0};
  CHECK(r7_session_init(&s,72u)==1);
  R7Lease l={72,101,0};f.legal.move_legal_mask=0u;
  R7Plan p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_NO_VALID_MOVE);
  CHECK(s.count==0u && s.ticket.pending==0u && l.consumed==0u);
  setup(&f);f.fail_second=1;
  p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_ORIGINAL_REQUEST_CHANGED);
  CHECK(s.count==0u && s.ticket.pending==0u && l.consumed==0u);
  setup(&f);
  p=session_perform(&f,&l,&s);
  CHECK(p.outcome==R7_FIGHT && s.count==1u && l.consumed==1u);
}
static void test_stale_and_invalid_epoch_boundary(void){
  Fake f;setup(&f);R7Session s={0};R7Lease l={72,101,0};
  CHECK(r7_session_init(&s,72u)==1);
  CHECK(session_perform(&f,&l,&s).outcome==R7_FIGHT);
  R7FightTicket t=s.ticket;
  /* A new epoch's original request cannot silently wipe a stuck ticket. */
  setup(&f);
  f.before.original_epoch=f.after.original_epoch=f.legal.original_epoch=73u;
  l=(R7Lease){73,101,0};
  R7Plan p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
  CHECK(s.epoch==72u && s.ticket.pending==1u && l.consumed==0u);
  CHECK(s.ticket.planned_move==t.planned_move);
  BoundaryFake b={{72u,73u,1u,1u},0,0u};
  R7BoundaryHost h={&b,check_boundary};
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  CHECK(s.epoch==72u && s.ticket.pending==1u);
  b.result=2;
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  b.result=1;b.boundary.to_epoch=72u;
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  b.boundary.to_epoch=71u;
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  b.boundary.to_epoch=73u;b.boundary.from_epoch=71u;
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  b.boundary.from_epoch=72u;b.boundary.observed_battle_closed=0u;
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  b.boundary.observed_battle_closed=1u;b.boundary.observed_controller_idle=0u;
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  CHECK(s.epoch==72u && s.ticket.pending==1u && s.count==1u);
  b.boundary.observed_controller_idle=1u;
  CHECK(r7_session_advance_epoch(&s,&h)==1);
  CHECK(s.epoch==73u && s.count==0u && s.ticket.pending==0u);
  CHECK(s.manual_locked==0u && s.initialized==1u);
  p=session_perform(&f,&l,&s);
  CHECK(p.outcome==R7_FIGHT && s.count==1u && l.consumed==1u);
  expect_source_only_success(p);
  /* Older epoch must not regain auto even with reused request ID. */
  setup(&f);l=(R7Lease){72,101,0};
  p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
  CHECK(s.count==1u && l.consumed==0u);
}
static void test_manual_takes_over_and_locks_epoch(void){
  Fake f;setup(&f);R7Session s={0};R7Lease l={72,101,0};
  CHECK(r7_session_init(&s,72u)==1);
  CHECK(session_perform(&f,&l,&s).outcome==R7_FIGHT);
  ManualFake m={0,0,0,0};
  R7ManualHost h={&m,check_manual};
  CHECK(r7_session_manual_takeover(&s,NULL)==0);
  CHECK(r7_session_manual_takeover(&s,&h)==0);
  CHECK(s.ticket.pending==1u && s.manual_locked==0u);
  m.result=2;
  CHECK(r7_session_manual_takeover(&s,&h)==0);
  CHECK(s.ticket.pending==1u && s.manual_locked==0u);
  m.result=1;
  CHECK(r7_session_manual_takeover(&s,&h)==1);
  CHECK(m.observed_epoch==72u && m.observed_move==157u);
  CHECK(s.ticket.pending==0u && s.manual_locked==1u && s.count==1u);
  /* No auto for this epoch even on a fresh lease and new request. */
  setup(&f);f.before.request_id=f.after.request_id=f.legal.request_id=102u;
  l=(R7Lease){72,102,0};
  R7Plan p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
  CHECK(l.consumed==0u && s.count==1u && f.reads==0u);
  CHECK(r7_session_manual_takeover(&s,&h)==0);
  BoundaryFake b={{72u,73u,1u,1u},1,0u};
  R7BoundaryHost boundary={&b,check_boundary};
  CHECK(r7_session_advance_epoch(&s,&boundary)==1);
  CHECK(s.manual_locked==0u && s.count==0u);
}
static void test_ledger_capacity_is_hard_fail_closed(void){
  Fake f;R7Session s={0};CHECK(r7_session_init(&s,72u)==1);
  for(unsigned i=0u;i<R7_SESSION_REPLAY_CAP/2u;i++) {
    setup(&f);uint32_t req=101u+i*2u;
    f.before.request_id=f.after.request_id=f.legal.request_id=req;
    R7Lease l={72u,req,0};
    R7Plan p=session_perform(&f,&l,&s);
    CHECK(p.outcome==R7_FIGHT && l.consumed==1u);
    choose_move(&f);
    f.before.request_id=f.after.request_id=f.legal.request_id=req+1u;
    l=(R7Lease){72u,req+1u,0u};
    p=session_perform(&f,&l,&s);
    CHECK(p.outcome==R7_MOVE && l.consumed==1u);
  }
  CHECK(s.count==R7_SESSION_REPLAY_CAP && s.ticket.pending==0u);
  setup(&f);f.before.request_id=f.after.request_id=f.legal.request_id=999u;
  R7Lease extra={72,999,0};
  R7Plan p=session_perform(&f,&extra,&s);
  check_session_defer(p,R7_BAD_LEASE);
  CHECK(extra.consumed==0u && s.count==R7_SESSION_REPLAY_CAP);
  CHECK(f.reads==0u && f.law_reads==0u);
  /* Cannot evade a full ledger by submitting a new epoch without proof. */
  f.before.original_epoch=f.after.original_epoch=f.legal.original_epoch=73u;
  extra=(R7Lease){73,999,0};
  p=session_perform(&f,&extra,&s);
  check_session_defer(p,R7_BAD_LEASE);
  CHECK(s.epoch==72u && s.count==R7_SESSION_REPLAY_CAP);
}
static void test_bad_api_and_uninitialized(void){
  Fake f;setup(&f);R7Session s={0};R7Lease l={72,101,0};
  CHECK(r7_session_init(NULL,72u)==0);
  CHECK(r7_session_init(&s,0u)==0);
  R7Host host={&f,rd,law};
  check_session_defer(r7_session_plan(&host,&l,&s),R7_STAGE_CONTINUITY_FAILED);
  CHECK(r7_session_init(&s,72u)==1);
  check_session_defer(r7_session_plan(NULL,&l,&s),R7_BAD_API);
  check_session_defer(r7_session_plan(&host,NULL,&s),R7_BAD_API);
  check_session_defer(r7_session_plan(&host,&l,NULL),R7_BAD_API);
  R7Host missing_read={&f,NULL,law};
  check_session_defer(r7_session_plan(&missing_read,&l,&s),R7_BAD_API);
  R7Host missing_law={&f,rd,NULL};
  check_session_defer(r7_session_plan(&missing_law,&l,&s),R7_BAD_API);
  s.busy=1u;
  check_session_defer(r7_session_plan(&host,&l,&s),R7_STAGE_CONTINUITY_FAILED);
  s.busy=0u;
}
int main(void){
  int baseline_result=r7_r4_original_test_main();
  CHECK(baseline_result==0);
  test_fresh_lease_replay_and_two_stage();
  test_failed_proposals_never_record_requests();
  test_stale_and_invalid_epoch_boundary();
  test_manual_takes_over_and_locks_epoch();
  test_ledger_capacity_is_hard_fail_closed();
  test_bad_api_and_uninitialized();
  printf("R7 R5 source-only lifecycle suite: %u cumulative assertions, %u failures\n",checks,failures);
  return failures?1:0;
}
