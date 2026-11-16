#include "lifecycle_adapter.h"
#include <string.h>

/* The wrapper consumes a read before calling r7_plan. Supplying the exact
 * captured first read to r7_plan and allowing its second read to call the
 * original host preserves read -> legal -> read ordering without accepting
 * a manufactured second snapshot. A dishonest host can still fake BOTH. */
typedef struct {const R7Host *real;R7Original first;unsigned reads;} R7Bound;
static int r7_bound_read(void *ctx,R7Original *out) {
  R7Bound *b=ctx;
  if (b->reads++==0u) { *out=b->first;return 1; }
  return b->real->read_original(b->real->ctx,out);
}
static int r7_bound_legality(void *ctx,const R7Original *pinned,R7Legal *out) {
  R7Bound *b=ctx;
  return b->real->read_engine_legality(b->real->ctx,pinned,out);
}
static R7LifecycleResult deny(R7LifecycleReason why,R7Reason adapter_why) {
  R7LifecycleResult r={{R7_DEFER,adapter_why,R7_NO_ACTION,R7_NO_SLOT,
   1u,0u,0u,0u,0u},why};return r;
}
void r7_lifecycle_init(R7Lifecycle *s) {if(s)memset(s,0,sizeof(*s));}
int r7_lifecycle_abandon(R7Lifecycle *s) {
  if(!s||!s->initialized)return 0;
  s->quarantined=1u;
  /* The pending ticket is retained as evidence, not silently discarded. */
  return 1;
}
R7LifecycleResult r7_lifecycle_plan(const R7Host *host,R7Lifecycle *s) {
  R7Original o={0};
  if (!s||!host||!host->read_original||!host->read_engine_legality) {
    if(s&&s->initialized)s->quarantined=1u;
    return deny(R7_LC_BAD_API,R7_BAD_API);
  }
  if (s->quarantined) return deny(R7_LC_QUARANTINED,R7_STAGE_CONTINUITY_FAILED);
  if(host->read_original(host->ctx,&o)!=1) {
    if(s->initialized)s->quarantined=1u;
    return deny(R7_LC_BAD_READ,R7_BAD_ENGINE_READ);
  }
  if (!o.original_epoch||!o.request_id) {
    if(s->initialized)s->quarantined=1u;
    return deny(R7_LC_BAD_ORIGINAL,R7_UNSUPPORTED_SCOPE);
  }
  if(s->initialized && o.original_epoch!=s->epoch) {
    s->quarantined=1u;
    return deny(R7_LC_EPOCH_ADVANCE,R7_STAGE_CONTINUITY_FAILED);
  }
  if(s->initialized) {
    for(unsigned i=0u;i<s->seen_count;i++)
      if(s->seen_ids[i]==o.request_id) {
        /* A replay is a manual-takeover barrier, not an auto retry. */
        s->quarantined=1u;
        return deny(R7_LC_DUPLICATE,R7_BAD_LEASE);
      }
  }
  if(s->seen_count>=R7_LIFECYCLE_SEEN_CAP) {
    s->quarantined=1u;
    return deny(R7_LC_LEDGER_FULL,R7_BAD_LEASE);
  }
  /* r7_plan receives a private lease and ticket. Any failed engine read,
   * legality check or stage continuity cannot consume the public state. */
  R7Lease lease={o.original_epoch,o.request_id,0u};
  R7FightTicket proposed_ticket=s->ticket;
  R7Bound bound={host,o,0u};
  R7Host wrapped={&bound,r7_bound_read,r7_bound_legality};
  R7Plan plan=r7_plan(&wrapped,&lease,&proposed_ticket);
  if(plan.outcome==R7_DEFER) {
    /* A manual-defer decision is sticky within this battle.  Continuing to
     * auto-propose on a later request could race a human/manual controller. */
    if (!s->initialized) {s->initialized=1u;s->epoch=o.original_epoch;}
    s->quarantined=1u;
    return (R7LifecycleResult){plan,R7_LC_ADAPTER_DEFER};
  }
  if(plan.outcome!=R7_FIGHT&&plan.outcome!=R7_MOVE) {
    s->quarantined=1u;
    return deny(R7_LC_BAD_ORIGINAL,R7_UNSUPPORTED_SCOPE);
  }
  /* Sanity-check a successful primitive call before marking consumption. */
  if(lease.consumed!=1u||bound.reads!=2u||
     plan.native_move_accepted||plan.native_manual_fallback_accepted||
     plan.no_forced_switch_certified||plan.production_authorized||
     plan.manual_defer_requested||
     (plan.outcome==R7_FIGHT&&plan.action!=0u)||
     (plan.outcome==R7_MOVE&&plan.action!=10u)) {
    s->quarantined=1u;
    return deny(R7_LC_BAD_ORIGINAL,R7_UNSUPPORTED_SCOPE);
  }
  s->ticket=proposed_ticket;
  s->seen_ids[s->seen_count++]=o.request_id;
  s->epoch=o.original_epoch;s->initialized=1u;
  return (R7LifecycleResult){plan,R7_LC_OK};
}
int r7_lifecycle_rearm(const R7Host *host,R7Lifecycle *s,
                       const R7RecoveryEvidence *e) {
  R7Original o={0};
  if(!host||!host->read_original||!s||!e||!s->initialized||!s->quarantined||
     !e->previous_epoch||e->previous_epoch!=s->epoch||
     e->new_epoch<=s->epoch||
     e->previous_battle_finished_verified!=1u||
     e->original_controller_rearmed_verified!=1u||
     e->original_response_queue_empty_verified!=1u)
    return 0;
  if(host->read_original(host->ctx,&o)!=1||
     o.original_epoch!=e->new_epoch||!o.request_id||o.battler!=0u||
     o.command!=17u||o.player_owned!=1u||o.wild_single!=1u||
     o.doubles!=0u||o.partner!=0u)return 0;
  /* This cannot prove the host was honest; native integration MUST validate
   * the original game outcome, controller and response queue independently. */
  s->epoch=e->new_epoch;s->seen_count=0u;s->quarantined=0u;
  memset(s->seen_ids,0,sizeof(s->seen_ids));
  memset(&s->ticket,0,sizeof(s->ticket));
  return 1;
}
