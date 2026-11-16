/* Fake original-engine provider ONLY. No emulator, ROM or save touched. */
#include "engine_adapter.h"
#include <stdio.h>
#include <string.h>

static unsigned checks=0, failures=0;
#define CHECK(x) do {++checks;if(!(x)){++failures;fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);}} while(0)

typedef struct {
  R7Original before,after;
  R7Legal legal;
  unsigned reads, law_reads;
  unsigned call_count;
  char call_order[4];
  int fail_first,fail_second,fail_legality,mutate_pp_during_legality;
} Fake;
static int rd(void *p,R7Original *out){
  Fake *f=p;f->reads++;
  if(f->call_count<sizeof(f->call_order)-1u)
    f->call_order[f->call_count++]='R';
  if ((f->reads==1&&f->fail_first)||(f->reads!=1&&f->fail_second))return 0;
  *out=f->reads==1?f->before:f->after;return 1;
}
static int law(void *p,const R7Original *orig,R7Legal *out){
  Fake *f=p;f->law_reads++;
  if(f->call_count<sizeof(f->call_order)-1u)
    f->call_order[f->call_count++]='L';
  if(f->mutate_pp_during_legality) f->after.pp[1]++;
  CHECK(orig->request_id==f->before.request_id);
  if(f->fail_legality)return 0;
  *out=f->legal;return 1;
}
static void encode_move_payload(R7Original *o){
  /* Source-only ChooseMoveStruct layout: 4-byte command header,
   * 4 little-endian u16 move IDs, then 4 current PP bytes. */
  for(unsigned i=0;i<4u;i++){
    o->original_payload[4u+2u*i]=(uint8_t)(o->moves[i]&0xffu);
    o->original_payload[5u+2u*i]=(uint8_t)(o->moves[i]>>8);
    o->original_payload[12u+i]=o->pp[i];
  }
}
static void choose_move(Fake *f){
  f->before.command=f->after.command=19u;
  f->before.original_header[0]=f->after.original_header[0]=19u;
  f->before.original_payload[0]=f->after.original_payload[0]=19u;
  f->before.original_header[1]=f->after.original_header[1]=0u;
  f->before.original_header[2]=f->after.original_header[2]=0u;
  f->before.original_header[3]=f->after.original_header[3]=0u;
  for (unsigned i=1u;i<4u;i++)
    f->before.original_payload[i]=f->after.original_payload[i]=0u;
  f->before.payload_length=f->after.payload_length=R7_CHOOSEMOVE_TOTAL_BYTES;
  encode_move_payload(&f->before);
  encode_move_payload(&f->after);
  for(unsigned i=0u;i<4u;i++){
    /* Host fixtures model the source maxPp[4] immediately after currentPp. */
    f->before.original_payload[16u+i]=f->before.pp[i];
    f->after.original_payload[16u+i]=f->after.pp[i];
  }
}
static void setup(Fake *f){
  memset(f,0,sizeof *f);
  R7Original *o=&f->before;
  o->original_epoch=72;o->request_id=101;o->command=17;o->battler=0;
  o->owner_party=1;o->foe_party=0;o->turn=9;o->resources=0x02001000;
  o->flags=0x100;
  o->player_owned=1;o->wild_single=1;o->doubles=0;o->partner=0;
  o->auto_enabled=1;o->foe_live=1;
  o->original_header[0]=17;o->original_header[1]=2;
  o->payload_length=4u;
  memcpy(o->original_payload,o->original_header,4);
  o->moves[0]=247;o->moves[1]=157;o->moves[2]=92;o->moves[3]=269;
  o->pp[0]=20;o->pp[1]=10;o->pp[2]=10;o->pp[3]=20;
  f->after=*o;
  f->legal.original_epoch=o->original_epoch;f->legal.request_id=o->request_id;
  f->legal.turn=o->turn;f->legal.move_limitations_verified=1;
  f->legal.target_helpers_verified=1;f->legal.ineffectiveness_verified=1;
  f->legal.move_legal_mask=0xf;f->legal.verified_foe_target_mask=0xf;
  f->legal.known_ineffective_mask=0x8; /* Taunt known ineffective: skip slot 3. */
  f->legal.priorities[0]=9;f->legal.priorities[1]=100;
  f->legal.priorities[2]=5;f->legal.priorities[3]=250;
}
static R7Plan perform(Fake *f,R7Lease *lease,R7FightTicket *ticket){
  f->reads=f->law_reads=f->call_count=0;
  memset(f->call_order,0,sizeof(f->call_order));
  R7Host host={f,rd,law};
  return r7_plan(&host,lease,ticket);
}
static void expect_source_only_success(R7Plan p){
  CHECK(p.outcome==R7_FIGHT || p.outcome==R7_MOVE);
  CHECK(p.manual_defer_requested==0u);
  CHECK(p.native_move_accepted==0u);
  CHECK(p.native_manual_fallback_accepted==0u);
  CHECK(p.no_forced_switch_certified==0u);
  CHECK(p.production_authorized==0u);
}
static void expect_defer(Fake *f,R7Reason reason){
  R7Lease lease={72,101,0};R7FightTicket ticket={0};
  R7Plan p=perform(f,&lease,&ticket);
  CHECK(p.outcome==R7_DEFER);CHECK(p.reason==reason);
  CHECK(p.action==R7_NO_ACTION);CHECK(p.slot==R7_NO_SLOT);
  CHECK(p.manual_defer_requested==1u);
  CHECK(p.native_move_accepted==0u && p.native_manual_fallback_accepted==0u);
  CHECK(p.no_forced_switch_certified==0u && p.production_authorized==0u);
  CHECK(lease.consumed==0u);CHECK(ticket.pending==0u);
}
static void test_two_stage_and_replay(void){
  Fake f;setup(&f);R7Lease lease={72,101,0};R7FightTicket ticket={0};
  R7Plan p=perform(&f,&lease,&ticket);
  CHECK(p.outcome==R7_FIGHT && p.action==0u && p.slot==1u);
  expect_source_only_success(p);
  CHECK(lease.consumed==1u && ticket.pending==1u);
  CHECK(ticket.slot==1u && ticket.planned_move==157u);
  /* An overlapping ChooseAction never clobbers a pending first-stage ticket. */
  R7FightTicket pending_copy=ticket;
  R7Lease new_request={72,103,0};
  f.before.request_id=f.after.request_id=f.legal.request_id=103;
  R7Plan overlap=perform(&f,&new_request,&ticket);
  CHECK(overlap.reason==R7_STAGE_CONTINUITY_FAILED && new_request.consumed==0u);
  CHECK(ticket.pending==pending_copy.pending && ticket.planned_move==pending_copy.planned_move);
  f.before.request_id=f.after.request_id=f.legal.request_id=101;
  /* A consumed lease cannot be reused for the same engine request. */
  p=perform(&f,&lease,&ticket);
  CHECK(p.outcome==R7_DEFER && p.reason==R7_BAD_LEASE);
  CHECK(ticket.pending==1u);
  /* ChooseMove must be a distinct, engine-owned request in the same battle. */
  choose_move(&f);
  f.before.request_id=f.after.request_id=f.legal.request_id=102;
  lease=(R7Lease){72,102,0};
  p=perform(&f,&lease,&ticket);
  CHECK(p.outcome==R7_MOVE && p.action==10u && p.slot==1u);
  expect_source_only_success(p);
  CHECK(lease.consumed==1u && ticket.pending==0u);
  /* Other command numbers NEVER cause emitted actions. */
  f.before.command=f.after.command=18;
  f.before.original_header[0]=f.after.original_header[0]=18;
  f.before.original_payload[0]=f.after.original_payload[0]=18;
  f.before.request_id=f.after.request_id=f.legal.request_id=103;
  lease=(R7Lease){72,103,0};
  expect_defer(&f,R7_UNSUPPORTED_SCOPE);
}
static void test_owner_and_scope(void){
  Fake f;
#define REJECT_SCOPE(field, value) do{setup(&f);f.before.field=f.after.field=(value);expect_defer(&f,R7_UNSUPPORTED_SCOPE);}while(0)
  REJECT_SCOPE(battler,1);REJECT_SCOPE(player_owned,0);
  REJECT_SCOPE(wild_single,0);REJECT_SCOPE(doubles,1);
  REJECT_SCOPE(partner,1);REJECT_SCOPE(auto_enabled,0);REJECT_SCOPE(foe_live,0);
  REJECT_SCOPE(player_owned,2);REJECT_SCOPE(wild_single,2);
  REJECT_SCOPE(command,20);REJECT_SCOPE(original_epoch,0);
  REJECT_SCOPE(request_id,0);REJECT_SCOPE(resources,0);
  REJECT_SCOPE(payload_length,0);REJECT_SCOPE(payload_length,3);
  REJECT_SCOPE(payload_length,41);
  setup(&f);f.before.original_header[0]=f.after.original_header[0]=12;
  expect_defer(&f,R7_UNSUPPORTED_SCOPE);
  setup(&f);f.before.original_payload[1]=f.after.original_payload[1]=88;
  expect_defer(&f,R7_UNSUPPORTED_SCOPE);
#undef REJECT_SCOPE
}
static void test_lease_and_host_failures(void){
  Fake f;setup(&f);R7FightTicket ticket={0};R7Lease lease={72,101,1};
  R7Plan p=perform(&f,&lease,&ticket);
  CHECK(p.outcome==R7_DEFER&&p.reason==R7_BAD_LEASE);
  lease=(R7Lease){72,102,0};p=perform(&f,&lease,&ticket);
  CHECK(p.reason==R7_BAD_LEASE);
  lease=(R7Lease){71,101,0};p=perform(&f,&lease,&ticket);
  CHECK(p.reason==R7_BAD_LEASE);
  setup(&f);f.fail_first=1;expect_defer(&f,R7_BAD_ENGINE_READ);
  setup(&f);f.fail_second=1;expect_defer(&f,R7_ORIGINAL_REQUEST_CHANGED);
  setup(&f);f.fail_legality=1;expect_defer(&f,R7_NO_ENGINE_LEGALITY);
  CHECK(r7_plan(NULL,&lease,&ticket).reason==R7_BAD_API);
  R7Host empty={0};CHECK(r7_plan(&empty,&lease,&ticket).reason==R7_BAD_API);
  CHECK(r7_plan(&empty,NULL,&ticket).reason==R7_BAD_API);
  CHECK(r7_plan(&empty,&lease,NULL).reason==R7_BAD_API);
}
static void test_engine_legality_binding(void){
  Fake f;
#define LAW_FAIL(field,value) do{setup(&f);f.legal.field=(value);expect_defer(&f,R7_NO_ENGINE_LEGALITY);}while(0)
  LAW_FAIL(original_epoch,0);LAW_FAIL(request_id,102);LAW_FAIL(turn,10);
  LAW_FAIL(move_limitations_verified,0);LAW_FAIL(target_helpers_verified,0);
  LAW_FAIL(ineffectiveness_verified,0);LAW_FAIL(ineffectiveness_verified,2);
  LAW_FAIL(move_legal_mask,0xf0);LAW_FAIL(verified_foe_target_mask,0x80);
  LAW_FAIL(known_ineffective_mask,0x10);
#undef LAW_FAIL
  setup(&f);f.legal.move_legal_mask=0;expect_defer(&f,R7_NO_VALID_MOVE);
  setup(&f);f.legal.verified_foe_target_mask=0;expect_defer(&f,R7_NO_VALID_MOVE);
  setup(&f);f.legal.known_ineffective_mask=15;expect_defer(&f,R7_NO_VALID_MOVE);
  setup(&f);f.before.pp[1]=f.after.pp[1]=0;
  R7Lease lease={72,101,0};R7FightTicket ticket={0};
  R7Plan p=perform(&f,&lease,&ticket);
  CHECK(p.outcome==R7_FIGHT && p.slot==0u);
  expect_source_only_success(p);
  setup(&f);f.legal.known_ineffective_mask=0;
  lease=(R7Lease){72,101,0};ticket=(R7FightTicket){0};
  p=perform(&f,&lease,&ticket);
  CHECK(p.outcome==R7_FIGHT && p.slot==3u); /* uncertainty vs known ineffective */
  expect_source_only_success(p);
}
static void test_original_data_drift(void){
  Fake f;
#define DRIFT(field) do {setup(&f);++f.after.field;expect_defer(&f,R7_ORIGINAL_REQUEST_CHANGED);}while(0)
  DRIFT(original_epoch);DRIFT(request_id);DRIFT(command);DRIFT(battler);
  DRIFT(owner_party);DRIFT(foe_party);DRIFT(turn);DRIFT(resources);DRIFT(flags);
  DRIFT(player_owned);DRIFT(wild_single);DRIFT(doubles);DRIFT(partner);
  DRIFT(auto_enabled);DRIFT(foe_live);DRIFT(payload_length);
#undef DRIFT
  for(unsigned i=0;i<4;i++){
    setup(&f);++f.after.original_header[i];expect_defer(&f,R7_ORIGINAL_REQUEST_CHANGED);
    setup(&f);++f.after.moves[i];expect_defer(&f,R7_ORIGINAL_REQUEST_CHANGED);
    setup(&f);++f.after.pp[i];expect_defer(&f,R7_ORIGINAL_REQUEST_CHANGED);
  }
  for(unsigned i=0;i<4;i++){
    setup(&f);++f.after.original_payload[i];expect_defer(&f,R7_ORIGINAL_REQUEST_CHANGED);
  }
}
static void test_stage_continuity(void){
  Fake f;setup(&f);R7Lease l={72,101,0};R7FightTicket t={0};
  CHECK(perform(&f,&l,&t).outcome==R7_FIGHT);
  choose_move(&f);
  f.before.request_id=f.after.request_id=f.legal.request_id=102;
  l=(R7Lease){72,102,0};
  R7FightTicket bad=t;bad.epoch=71;
  R7Plan p=perform(&f,&l,&bad);
  CHECK(p.reason==R7_STAGE_CONTINUITY_FAILED && l.consumed==0u);
  bad=t;bad.turn=8;p=perform(&f,&l,&bad);CHECK(p.reason==R7_STAGE_CONTINUITY_FAILED);
  bad=t;bad.owner_party=2;p=perform(&f,&l,&bad);CHECK(p.reason==R7_STAGE_CONTINUITY_FAILED);
  bad=t;bad.foe_party=2;p=perform(&f,&l,&bad);CHECK(p.reason==R7_STAGE_CONTINUITY_FAILED);
  bad=t;bad.slot=2;p=perform(&f,&l,&bad);CHECK(p.reason==R7_STAGE_CONTINUITY_FAILED);
  bad=t;bad.planned_move=99;p=perform(&f,&l,&bad);CHECK(p.reason==R7_STAGE_CONTINUITY_FAILED);
  bad=t;bad.pending=0;p=perform(&f,&l,&bad);CHECK(p.reason==R7_STAGE_CONTINUITY_FAILED);
  /* Engine has stopped validating the earlier move; never pick a substitute. */
  f.legal.move_legal_mask &=~(1u<<1);
  p=perform(&f,&l,&t);CHECK(p.reason==R7_STAGE_CONTINUITY_FAILED);
  CHECK(l.consumed==0u && t.pending==1u);
}
/* Full source-side ChooseMove size is 40 including the four-byte header.
 * A shorter prefix is NOT an authenticated command even if moves+PP match. */
static void test_command19_length_boundary(void){
  Fake f;
  for(unsigned n=4u;n<R7_CHOOSEMOVE_TOTAL_BYTES;n++){
    setup(&f);choose_move(&f);
    f.before.payload_length=f.after.payload_length=(uint8_t)n;
    expect_defer(&f,R7_UNSUPPORTED_SCOPE);
  }
  setup(&f);choose_move(&f);
  CHECK(f.before.payload_length==40u);
  expect_defer(&f,R7_STAGE_CONTINUITY_FAILED); /* valid, but no Fight ticket */
  setup(&f);choose_move(&f);
  f.before.payload_length=f.after.payload_length=41u;
  expect_defer(&f,R7_UNSUPPORTED_SCOPE);
}
static void test_header_agrees_with_payload_but_not_command(void){
  Fake f;setup(&f);
  f.before.original_header[0]=f.after.original_header[0]=19u;
  f.before.original_payload[0]=f.after.original_payload[0]=19u;
  /* header == payload; command is still original ChooseAction=17. */
  expect_defer(&f,R7_UNSUPPORTED_SCOPE);
  setup(&f);choose_move(&f);
  f.before.original_header[0]=f.after.original_header[0]=17u;
  f.before.original_payload[0]=f.after.original_payload[0]=17u;
  /* header == payload; command is ChooseMove=19. */
  expect_defer(&f,R7_UNSUPPORTED_SCOPE);
}
static void test_command19_move_and_pp_payload_are_authoritative(void){
  Fake f;
  for(unsigned i=4u;i<16u;i++){
    setup(&f);choose_move(&f);
    f.before.original_payload[i]^=0x55u;
    f.after.original_payload[i]^=0x55u;
    /* Both snapshots match, but original payload contradicts host fields. */
    expect_defer(&f,R7_UNSUPPORTED_SCOPE);
  }
  for(unsigned i=0u;i<4u;i++){
    setup(&f);choose_move(&f);
    f.before.moves[i]++;f.after.moves[i]++;
    expect_defer(&f,R7_UNSUPPORTED_SCOPE);
    setup(&f);choose_move(&f);
    f.before.pp[i]++;f.after.pp[i]++;
    expect_defer(&f,R7_UNSUPPORTED_SCOPE);
  }
  /* The exact hostile-host example: command19 payload body full of junk. */
  setup(&f);choose_move(&f);
  memset(&f.before.original_payload[4],0xaa,16u);
  memset(&f.after.original_payload[4],0xaa,16u);
  expect_defer(&f,R7_UNSUPPORTED_SCOPE);
}
static void test_legality_callback_precedes_second_original_read(void){
  Fake f;setup(&f);
  R7Lease lease={72,101,0};R7FightTicket ticket={0};
  R7Plan p=perform(&f,&lease,&ticket);
  CHECK(p.outcome==R7_FIGHT);
  expect_source_only_success(p);
  CHECK(strcmp(f.call_order,"RLR")==0);
  CHECK(f.reads==2u && f.law_reads==1u);
  setup(&f);f.mutate_pp_during_legality=1;
  lease=(R7Lease){72,101,0};ticket=(R7FightTicket){0};
  p=perform(&f,&lease,&ticket);
  CHECK(p.outcome==R7_DEFER && p.reason==R7_ORIGINAL_REQUEST_CHANGED);
  CHECK(strcmp(f.call_order,"RLR")==0);
  CHECK(f.reads==2u && f.law_reads==1u);
  CHECK(lease.consumed==0u && ticket.pending==0u);
  CHECK(p.manual_defer_requested==1u);
  CHECK(p.native_move_accepted==0u);
  CHECK(p.native_manual_fallback_accepted==0u);
  CHECK(p.no_forced_switch_certified==0u);
  CHECK(p.production_authorized==0u);
}

/* R7 R3: the original ChooseMove header must not contradict the host's
 * single-battle scope or silently toggle source NoPpNumber/reserved bytes. */
static void test_choose_move_header_is_engine_scope_bound(void){
  Fake f;
  for(unsigned field=1u;field<=3u;field++){
    setup(&f);choose_move(&f);
    f.before.original_header[field]=f.after.original_header[field]=1u;
    f.before.original_payload[field]=f.after.original_payload[field]=1u;
    /* header and payload STILL agree. The scope is untrusted. */
    expect_defer(&f,R7_UNSUPPORTED_SCOPE);
  }
  /* A double-battle header is disallowed even when the separate host flag
   * agrees that this is a double battle. */
  setup(&f);choose_move(&f);
  f.before.doubles=f.after.doubles=1u;
  f.before.original_header[1]=f.after.original_header[1]=1u;
  f.before.original_payload[1]=f.after.original_payload[1]=1u;
  expect_defer(&f,R7_UNSUPPORTED_SCOPE);
  /* A legitimate single header is structurally accepted with a full buffer
   * but still cannot Move without the authenticated prior Fight ticket. */
  setup(&f);choose_move(&f);
  expect_defer(&f,R7_STAGE_CONTINUITY_FAILED);
}
static void test_command19_full_tail_snapshot_continuity(void){
  Fake f;
  /* Ensure every byte after the move+currentPP prefix is still compared,
   * including the exact 40th byte which R2's 32-byte cap lost. */
  for(unsigned i=16u;i<R7_CHOOSEMOVE_TOTAL_BYTES;i++){
    setup(&f);choose_move(&f);
    f.before.original_payload[i]=0xa5u;
    f.after.original_payload[i]=0x5au;
    R7Lease l={72,101,0};R7FightTicket ticket={0};
    R7Plan plan=perform(&f,&l,&ticket);
    CHECK(plan.outcome==R7_DEFER && plan.reason==R7_ORIGINAL_REQUEST_CHANGED);
    CHECK(l.consumed==0u && ticket.pending==0u);
    CHECK(plan.native_move_accepted==0u && plan.no_forced_switch_certified==0u);
  }
}
static void test_full_length_move_proposal(void){
  Fake f;setup(&f);R7Lease lease={72,101,0};R7FightTicket ticket={0};
  R7Plan p=perform(&f,&lease,&ticket);
  CHECK(p.outcome==R7_FIGHT && ticket.pending==1u);
  setup(&f);choose_move(&f);
  f.before.request_id=f.after.request_id=f.legal.request_id=102u;
  lease=(R7Lease){72,102,0};
  CHECK(f.before.payload_length==R7_PAYLOAD_CAP);
  p=perform(&f,&lease,&ticket);
  CHECK(p.outcome==R7_MOVE && p.action==10u && p.slot==1u);
  CHECK(lease.consumed==1u && ticket.pending==0u);
  expect_source_only_success(p);
}
/* R7 R4: original ChooseAction is exactly four bytes, never a menu-like
 * 20/40-byte buffer. A structurally invalid request cannot earn Fight. */
static void test_choose_action_exact_four_bytes(void){
  Fake f;
  for(unsigned n=0u;n<=R7_PAYLOAD_CAP+1u;n++){
    setup(&f);
    f.before.payload_length=f.after.payload_length=(uint8_t)n;
    R7Lease lease={72,101,0};R7FightTicket ticket={0};
    R7Plan p=perform(&f,&lease,&ticket);
    if(n==4u){
      CHECK(p.outcome==R7_FIGHT && p.action==0u && p.slot==1u);
      CHECK(lease.consumed==1u && ticket.pending==1u);
      expect_source_only_success(p);
    }else{
      CHECK(p.outcome==R7_DEFER && p.reason==R7_UNSUPPORTED_SCOPE);
      CHECK(p.action==R7_NO_ACTION && p.slot==R7_NO_SLOT);
      CHECK(p.manual_defer_requested==1u && lease.consumed==0u && ticket.pending==0u);
      CHECK(p.native_move_accepted==0u && p.native_manual_fallback_accepted==0u);
      CHECK(p.no_forced_switch_certified==0u && p.production_authorized==0u);
    }
  }
  /* All three item/action bytes remain part of the immutable original
   * ChooseAction header. Their actual values are not guest-authenticated. */
  for(unsigned i=1u;i<4u;i++){
    setup(&f);
    f.before.original_header[i]=f.after.original_header[i]=(uint8_t)(i+20u);
    f.before.original_payload[i]=f.after.original_payload[i]=(uint8_t)(i+20u);
    R7Lease lease={72,101,0};R7FightTicket ticket={0};
    R7Plan p=perform(&f,&lease,&ticket);
    CHECK(p.outcome==R7_FIGHT && lease.consumed==1u);
    expect_source_only_success(p);
    /* But a change of that byte during legality evaluation always defers. */
    setup(&f);f.after.original_payload[i]^=0x01u;
    expect_defer(&f,R7_ORIGINAL_REQUEST_CHANGED);
  }
}

/* Bytes 16..19 are maxPp[4], immediately following original currentPp[4].
 * Equality alone is insufficient if both snapshots contain contradictory
 * host PP / maximum PP values. The check must be performed pre-legality. */
static void test_choose_move_max_pp_consistency(void){
  Fake f;
  for(unsigned i=0u;i<4u;i++){
    setup(&f);choose_move(&f);
    CHECK(f.before.original_payload[16u+i]==f.before.pp[i]);
    f.before.original_payload[16u+i]=(uint8_t)(f.before.pp[i]-1u);
    f.after.original_payload[16u+i]=f.before.original_payload[16u+i];
    expect_defer(&f,R7_UNSUPPORTED_SCOPE);

    setup(&f);choose_move(&f);
    f.before.original_payload[16u+i]=f.after.original_payload[16u+i]=0u;
    expect_defer(&f,R7_UNSUPPORTED_SCOPE);

    setup(&f);choose_move(&f);
    f.before.original_payload[16u+i]=(uint8_t)(f.before.pp[i]+1u);
    f.after.original_payload[16u+i]=f.before.original_payload[16u+i];
    /* Valid contents but no original player Fight ticket. */
    expect_defer(&f,R7_STAGE_CONTINUITY_FAILED);

    setup(&f);choose_move(&f);
    f.before.pp[i]=f.after.pp[i]=0u;
    f.before.original_payload[12u+i]=f.after.original_payload[12u+i]=0u;
    f.before.original_payload[16u+i]=f.after.original_payload[16u+i]=1u;
    expect_defer(&f,R7_STAGE_CONTINUITY_FAILED);
    /* A populated slot with zero current and zero max PP has no
     * trustworthy source-side PP capacity; do not automate from it. */
    f.before.original_payload[16u+i]=f.after.original_payload[16u+i]=0u;
    expect_defer(&f,R7_UNSUPPORTED_SCOPE);
  }
  /* The R7 R3 tail snapshot equality is still mandatory for maxPp. */
  for(unsigned i=16u;i<20u;i++){
    setup(&f);choose_move(&f);
    f.after.original_payload[i]^=0x01u;
    R7Lease lease={72,101,0};R7FightTicket ticket={0};
    R7Plan p=perform(&f,&lease,&ticket);
    CHECK(p.outcome==R7_DEFER && p.reason==R7_ORIGINAL_REQUEST_CHANGED);
    CHECK(lease.consumed==0u && ticket.pending==0u);
  }
}

int main(void){
  test_two_stage_and_replay();test_owner_and_scope();test_lease_and_host_failures();
  test_engine_legality_binding();test_original_data_drift();test_stage_continuity();
  test_command19_length_boundary();
  test_header_agrees_with_payload_but_not_command();
  test_command19_move_and_pp_payload_are_authoritative();
  test_legality_callback_precedes_second_original_read();
  test_choose_move_header_is_engine_scope_bound();
  test_command19_full_tail_snapshot_continuity();
  test_full_length_move_proposal();
  test_choose_action_exact_four_bytes();
  test_choose_move_max_pp_consistency();
  printf("R7 source-only host adapter: %u assertions, %u failures\n",checks,failures);
  return failures?1:0;
}
