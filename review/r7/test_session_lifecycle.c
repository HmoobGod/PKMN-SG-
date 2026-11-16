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
  CHECK(s.pending_fight_request_id==101u);
  CHECK(s.consumed[0].epoch==72u && s.consumed[0].request_id==101u);
  CHECK(r7_session_init(&s,72u)==0 && r7_session_init(&s,73u)==0);
  /* Genuine uninterrupted next request is allowed by the SOURCE model. */
  choose_move(&f);f.before.request_id=f.after.request_id=f.legal.request_id=102u;
  l=(R7Lease){72,102,0};
  p=session_perform(&f,&l,&s);
  CHECK(p.outcome==R7_MOVE && p.action==10u && p.slot==1u);
  CHECK(l.consumed==1u && s.count==2u && s.ticket.pending==0u);
  CHECK(s.pending_fight_request_id==0u);
  expect_source_only_success(p);
  /* Replayed request from a new, unconsumed caller lease is rejected,
   * then quarantines auto for the rest of this epoch. */
  setup(&f);R7Lease replay={72,101,0};
  p=session_perform(&f,&replay,&s);
  check_session_defer(p,R7_BAD_LEASE);
  CHECK(replay.consumed==0u && s.count==2u && s.manual_locked==1u);
  CHECK(s.ticket.pending==0u && f.law_reads==0u);
  setup(&f);f.before.request_id=f.after.request_id=f.legal.request_id=103u;
  l=(R7Lease){72,103,0};p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
  CHECK(s.count==2u && l.consumed==0u && f.reads==0u);
}
static void test_failed_proposals_never_record_requests(void){
  Fake f;setup(&f);R7Session s={0};
  CHECK(r7_session_init(&s,72u)==1);
  R7Lease l={72,101,0};f.legal.move_legal_mask=0u;
  R7Plan p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_NO_VALID_MOVE);
  CHECK(s.count==0u && s.ticket.pending==0u && l.consumed==0u);
  CHECK(s.manual_locked==0u); /* allowed only with no pending Fight */
  setup(&f);p=session_perform(&f,&l,&s);
  CHECK(p.outcome==R7_FIGHT && s.count==1u && l.consumed==1u);
  /* A missing original response read after a successful Fight is NOT a
   * benign defer. Do not accept a later manual ChooseMove. */
  choose_move(&f);f.before.request_id=f.after.request_id=f.legal.request_id=102u;
  l=(R7Lease){72,102,0};f.fail_second=1;
  p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_ORIGINAL_REQUEST_CHANGED);
  CHECK(s.count==1u && s.ticket.pending==0u && s.manual_locked==1u);
  CHECK(l.consumed==0u);
  f.fail_second=0;
  p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
  CHECK(f.reads==0u && l.consumed==0u);
}
static void test_stale_and_invalid_epoch_boundary(void){
  Fake f;setup(&f);R7Session s={0};R7Lease l={72,101,0};
  CHECK(r7_session_init(&s,72u)==1);
  CHECK(session_perform(&f,&l,&s).outcome==R7_FIGHT);
  /* A new epoch cannot silently wipe an outstanding Fight ticket. The
   * violation permanently quarantines this epoch and retires the ticket. */
  setup(&f);f.before.original_epoch=f.after.original_epoch=f.legal.original_epoch=73u;
  l=(R7Lease){73,101,0};
  R7Plan p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
  CHECK(s.epoch==72u && s.manual_locked==1u);
  CHECK(s.ticket.pending==0u && s.pending_fight_request_id==0u);
  CHECK(l.consumed==0u && s.count==1u);
  BoundaryFake b={{72u,73u,1u,1u},0,0u};
  R7BoundaryHost h={&b,check_boundary};
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  b.result=2;CHECK(r7_session_advance_epoch(&s,&h)==0);
  b.result=1;b.boundary.to_epoch=72u;CHECK(r7_session_advance_epoch(&s,&h)==0);
  b.boundary.to_epoch=71u;CHECK(r7_session_advance_epoch(&s,&h)==0);
  b.boundary.to_epoch=73u;b.boundary.from_epoch=71u;
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  b.boundary.from_epoch=72u;b.boundary.observed_battle_closed=0u;
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  b.boundary.observed_battle_closed=1u;b.boundary.observed_controller_idle=0u;
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  CHECK(s.epoch==72u && s.manual_locked==1u && s.count==1u);
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
  CHECK(s.count==1u && l.consumed==0u && s.manual_locked==1u);
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
  check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
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

/* Claude B1: interrupted auto Fight must NEVER be usable by an original
 * human-driven ChooseMove request, even when every R7 ticket field matches. */
static void test_interrupted_fight_17_17_19_never_resumes(void){
  Fake f;setup(&f);R7Session s={0};R7Lease lease={72,101,0};
  CHECK(r7_session_init(&s,72u)==1);
  R7Plan plan=session_perform(&f,&lease,&s);
  CHECK(plan.outcome==R7_FIGHT && s.ticket.pending==1u);
  CHECK(s.pending_fight_request_id==101u && s.count==1u);
  /* Player cancelled the move menu; engine reissues ChooseAction. */
  setup(&f);f.before.request_id=f.after.request_id=f.legal.request_id=102u;
  lease=(R7Lease){72,102,0};
  plan=session_perform(&f,&lease,&s);
  check_session_defer(plan,R7_STAGE_CONTINUITY_FAILED);
  CHECK(s.manual_locked==1u && s.ticket.pending==0u);
  CHECK(s.pending_fight_request_id==0u && s.count==1u && lease.consumed==0u);
  CHECK(f.law_reads==0u);
  /* Human next picks Fight manually and enters ChooseMove. Even a matching
   * slot, party, epoch and turn cannot reactivate the old auto-Fight. */
  choose_move(&f);f.before.request_id=f.after.request_id=f.legal.request_id=103u;
  lease=(R7Lease){72,103,0};
  plan=session_perform(&f,&lease,&s);
  check_session_defer(plan,R7_STAGE_CONTINUITY_FAILED);
  CHECK(s.manual_locked==1u && s.ticket.pending==0u);
  CHECK(s.count==1u && lease.consumed==0u);
  CHECK(f.reads==0u && f.law_reads==0u);
}

/* A missing immediate successor may be a controller/menu interruption, even
 * without a visible intervening planner call. Fail closed, not auto-continue. */
static void test_fight_requires_immediate_successor_request(void){
  Fake f;setup(&f);R7Session s={0};R7Lease l={72,101,0};
  CHECK(r7_session_init(&s,72u)==1);
  CHECK(session_perform(&f,&l,&s).outcome==R7_FIGHT);
  choose_move(&f);f.before.request_id=f.after.request_id=f.legal.request_id=103u;
  l=(R7Lease){72,103,0};
  R7Plan p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
  CHECK(s.manual_locked==1u && s.ticket.pending==0u && s.count==1u);
  CHECK(f.law_reads==0u && l.consumed==0u);
}

/* Claude B2: a mismatch must be caught even WITHOUT an existing pending
 * ticket (otherwise a missing epoch guard could issue an auto Fight). */
static void test_first_request_epoch_binding_is_independent(void){
  Fake f;setup(&f);R7Session s={0};
  CHECK(r7_session_init(&s,72u)==1);
  f.before.original_epoch=f.after.original_epoch=f.legal.original_epoch=73u;
  R7Lease l={73,101,0};
  R7Plan p=session_perform(&f,&l,&s);
  check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
  CHECK(l.consumed==0u && s.count==0u && s.manual_locked==1u);
  CHECK(f.law_reads==0u);
}

typedef struct {
  Fake outer,inner;
  R7Session *session;
  R7Lease inner_lease;
  R7Plan inner_plan;
  unsigned attempts;
} ReentryPlanFake;
static int read_outer(void *ctx,R7Original *out){
  ReentryPlanFake *c=ctx;
  return rd(&c->outer,out);
}
static int legal_with_reentry(void *ctx,const R7Original *orig,R7Legal *out){
  ReentryPlanFake *c=ctx;
  c->attempts++;
  if(c->attempts==1u){
    R7Host inner_host={&c->inner,rd,law};
    c->inner_plan=r7_session_plan(&inner_host,&c->inner_lease,c->session);
  }
  return law(&c->outer,orig,out);
}
static void test_plan_legal_callback_cannot_reenter(void){
  ReentryPlanFake c={0};setup(&c.outer);setup(&c.inner);
  c.inner.before.request_id=c.inner.after.request_id=
    c.inner.legal.request_id=102u;
  R7Session s={0};CHECK(r7_session_init(&s,72u)==1);
  c.session=&s;c.inner_lease=(R7Lease){72,102,0};
  R7Lease outer_lease={72,101,0};
  R7Host host={&c,read_outer,legal_with_reentry};
  R7Plan p=r7_session_plan(&host,&outer_lease,&s);
  check_session_defer(c.inner_plan,R7_STAGE_CONTINUITY_FAILED);
  check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
  CHECK(c.attempts==1u && c.inner_lease.consumed==0u);
  CHECK(outer_lease.consumed==0u && s.count==0u);
  CHECK(s.busy==0u && s.manual_locked==1u && s.reentrant==1u);
  CHECK(s.ticket.pending==0u);
}

typedef struct {
  R7Session *session;
  int nested_return;
  unsigned calls;
} ReentryManualFake;
static int manual_reenter(void *ctx,const R7FightTicket *ticket){
  ReentryManualFake *c=ctx;
  (void)ticket;
  c->calls++;
  if(c->calls==1u){
    R7ManualHost h={c,manual_reenter};
    c->nested_return=r7_session_manual_takeover(c->session,&h);
  }
  return 1;
}
static void test_manual_takeover_callback_cannot_reenter(void){
  Fake f;setup(&f);R7Session s={0};R7Lease l={72,101,0};
  CHECK(r7_session_init(&s,72u)==1);
  CHECK(session_perform(&f,&l,&s).outcome==R7_FIGHT);
  ReentryManualFake c={&s,-9,0u};R7ManualHost h={&c,manual_reenter};
  CHECK(r7_session_manual_takeover(&s,&h)==0);
  CHECK(c.calls==1u && c.nested_return==0);
  CHECK(s.busy==0u && s.reentrant==1u);
  CHECK(s.manual_locked==1u && s.ticket.pending==0u);
  CHECK(s.count==1u);
}

typedef struct {
  R7Session *session;
  int nested_return;
  unsigned calls;
} ReentryBoundaryFake;
static int boundary_reenter(void *ctx,R7EpochBoundary *out){
  ReentryBoundaryFake *c=ctx;
  c->calls++;
  if(c->calls==1u){
    R7BoundaryHost h={c,boundary_reenter};
    c->nested_return=r7_session_advance_epoch(c->session,&h);
  }
  *out=(R7EpochBoundary){72u,73u,1u,1u};
  return 1;
}
static void test_epoch_boundary_callback_cannot_reenter(void){
  R7Session s={0};CHECK(r7_session_init(&s,72u)==1);
  ReentryBoundaryFake c={&s,-9,0u};R7BoundaryHost h={&c,boundary_reenter};
  CHECK(r7_session_advance_epoch(&s,&h)==0);
  CHECK(c.calls==1u && c.nested_return==0);
  CHECK(s.epoch==72u && s.busy==0u && s.reentrant==1u);
  CHECK(s.manual_locked==1u && s.initialized==1u);
  /* Legitimate verified subsequent epoch transition may still recover. */
  BoundaryFake b={{72u,73u,1u,1u},1,0u};
  R7BoundaryHost valid={&b,check_boundary};
  CHECK(r7_session_advance_epoch(&s,&valid)==1);
  CHECK(s.epoch==73u && s.reentrant==0u && s.manual_locked==0u);
  /* Re-entrant lock can recover only after a verified higher epoch; then
   * the new epoch is still able to propose a source-model Fight. */
  Fake f;setup(&f);
  f.before.original_epoch=f.after.original_epoch=f.legal.original_epoch=73u;
  R7Lease lease={73,101,0};
  R7Plan p=session_perform(&f,&lease,&s);
  CHECK(p.outcome==R7_FIGHT && lease.consumed==1u);
  CHECK(s.count==1u && s.ticket.pending==1u && s.manual_locked==0u);
  expect_source_only_success(p);
}
static void test_takeover_prerequisites_and_uint32_epoch_bound(void){
  Fake f;setup(&f);R7Session s={0};R7Lease l={72,101,0};
  CHECK(r7_session_init(&s,72u)==1);
  ManualFake m={1,0u,0u,0u};R7ManualHost h={&m,check_manual};
  CHECK(r7_session_manual_takeover(&s,&h)==0);
  CHECK(m.calls==0u && s.manual_locked==0u);
  CHECK(session_perform(&f,&l,&s).outcome==R7_FIGHT);
  s.ticket.epoch=73u;
  CHECK(r7_session_manual_takeover(&s,&h)==0);
  CHECK(m.calls==0u && s.ticket.pending==1u);
  s.ticket.epoch=72u;
  BoundaryFake b={{72u,UINT32_MAX,1u,1u},1,0u};
  R7BoundaryHost boundary={&b,check_boundary};
  CHECK(r7_session_advance_epoch(&s,&boundary)==0);
  CHECK(s.epoch==72u && s.ticket.pending==1u);
  R7Session new_session={0};CHECK(r7_session_init(&new_session,UINT32_MAX)==0);
}


/* Claude R2 coverage gap B1: a benign-reason defer while a Fight ticket is
 * outstanding MUST retire the ticket and lock the rest of the epoch.
 * Retrying the same original command19 must never auto Move. */
static void test_pending_ticket_benign_defer_quarantines(void){
  for(unsigned mode=0u;mode<2u;mode++){
    Fake f;setup(&f);R7Session s={0};R7Lease l={72,101,0};
    CHECK(r7_session_init(&s,72u)==1);
    R7Plan p=session_perform(&f,&l,&s);
    CHECK(p.outcome==R7_FIGHT && s.ticket.pending==1u);
    CHECK(s.pending_fight_request_id==101u && s.count==1u);
    choose_move(&f);
    f.before.request_id=f.after.request_id=f.legal.request_id=102u;
    if(mode==0u) f.fail_legality=1;
    else f.legal.move_legal_mask=0u;
    l=(R7Lease){72,102,0};
    p=session_perform(&f,&l,&s);
    check_session_defer(p,mode==0u?R7_NO_ENGINE_LEGALITY:R7_NO_VALID_MOVE);
    CHECK(l.consumed==0u && s.count==1u);
    CHECK(s.manual_locked==1u && s.ticket.pending==0u);
    CHECK(s.pending_fight_request_id==0u);
    /* The external condition is fixed; the stale ticket must still be dead. */
    f.fail_legality=0;f.legal.move_legal_mask=0xfu;
    p=session_perform(&f,&l,&s);
    check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
    CHECK(f.reads==0u && f.law_reads==0u && l.consumed==0u);
    CHECK(s.manual_locked==1u && s.ticket.pending==0u && s.count==1u);
  }
}

/* Claude R2 coverage gap B2: without a Fight ticket, every anomalous reason
 * must quarantine and deny the NEXT valid request, not just return DEFER.
 * This pins each non-benign reason independently against whitelist mutants. */
static void test_no_ticket_anomaly_reason_table_quarantines(void){
  const R7Reason reasons[]={
    R7_BAD_API,R7_BAD_ENGINE_READ,R7_UNSUPPORTED_SCOPE,
    R7_BAD_LEASE,R7_ORIGINAL_REQUEST_CHANGED,
    R7_STAGE_CONTINUITY_FAILED
  };
  for(unsigned i=0u;i<sizeof reasons/sizeof reasons[0];i++){
    Fake f;setup(&f);R7Session s={0};R7Lease l={72,101,0};
    CHECK(r7_session_init(&s,72u)==1);
    switch(reasons[i]){
      case R7_BAD_ENGINE_READ:f.fail_first=1;break;
      case R7_UNSUPPORTED_SCOPE:f.before.doubles=f.after.doubles=1u;break;
      case R7_BAD_LEASE:l.consumed=1u;break;
      case R7_ORIGINAL_REQUEST_CHANGED:f.after.turn++;break;
      case R7_STAGE_CONTINUITY_FAILED:choose_move(&f);break;
      default:break;
    }
    R7Plan p=reasons[i]==R7_BAD_API?
      r7_session_plan(NULL,&l,&s):session_perform(&f,&l,&s);
    check_session_defer(p,reasons[i]);
    CHECK(s.manual_locked==1u && s.ticket.pending==0u);
    CHECK(s.pending_fight_request_id==0u && s.count==0u);
    /* Valid new request in the same epoch cannot bypass quarantine. */
    setup(&f);
    f.before.request_id=f.after.request_id=f.legal.request_id=102u;
    R7Lease next={72,102,0};
    p=session_perform(&f,&next,&s);
    check_session_defer(p,R7_STAGE_CONTINUITY_FAILED);
    CHECK(f.reads==0u && f.law_reads==0u);
    CHECK(next.consumed==0u && s.manual_locked==1u && s.count==0u);
  }
}

/* Benign no-ticket deferrals must be retriable; otherwise the lifecycle
 * locks auto unnecessarily, including when legality becomes available. */
static void test_no_ticket_benign_retry_table(void){
  for(unsigned mode=0u;mode<2u;mode++){
    Fake f;setup(&f);R7Session s={0};R7Lease l={72,101,0};
    CHECK(r7_session_init(&s,72u)==1);
    if(mode==0u) f.fail_legality=1;
    else f.legal.move_legal_mask=0u;
    R7Plan p=session_perform(&f,&l,&s);
    check_session_defer(p,mode==0u?R7_NO_ENGINE_LEGALITY:R7_NO_VALID_MOVE);
    CHECK(s.manual_locked==0u && s.ticket.pending==0u);
    CHECK(s.count==0u && l.consumed==0u);
    setup(&f);
    p=session_perform(&f,&l,&s);
    CHECK(p.outcome==R7_FIGHT && l.consumed==1u);
    CHECK(s.manual_locked==0u && s.ticket.pending==1u && s.count==1u);
    expect_source_only_success(p);
  }
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
  test_interrupted_fight_17_17_19_never_resumes();
  test_fight_requires_immediate_successor_request();
  test_first_request_epoch_binding_is_independent();
  test_plan_legal_callback_cannot_reenter();
  test_manual_takeover_callback_cannot_reenter();
  test_epoch_boundary_callback_cannot_reenter();
  test_takeover_prerequisites_and_uint32_epoch_bound();
  test_pending_ticket_benign_defer_quarantines();
  test_no_ticket_anomaly_reason_table_quarantines();
  test_no_ticket_benign_retry_table();
  printf("R7 R5 source-only lifecycle suite: %u cumulative assertions, %u failures\n",checks,failures);
  return failures?1:0;
}
