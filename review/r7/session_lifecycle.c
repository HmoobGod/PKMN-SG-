#include "session_lifecycle.h"
#include <string.h>

typedef struct {
  const R7Host *real;
  const R7Session *session;
  R7Original first;
  unsigned reads;
  R7Reason blocked;
} R7Proxy;

static R7Plan deny(R7Reason why) {
  R7Plan p={R7_DEFER,why,R7_NO_ACTION,R7_NO_SLOT,1u,0u,0u,0u,0u};
  return p;
}

int r7_session_init(R7Session *session, uint32_t first_epoch) {
  if (!session || !first_epoch || session->initialized==1u) return 0;
  memset(session,0,sizeof *session);
  session->epoch=first_epoch;
  session->initialized=1u;
  return 1;
}

static int seen_id(const R7Session *s,uint32_t epoch,uint32_t id) {
  unsigned i;
  for(i=0u;i<s->count;i++)
    if(s->consumed[i].epoch==epoch && s->consumed[i].request_id==id)
      return 1;
  return 0;
}

/* Re-check the original host on both adapter reads. A synthetic caller lease
 * that has consumed=0 cannot hide a request that this session consumed. */
static int scoped_read(void *ctx,R7Original *out) {
  R7Proxy *p=(R7Proxy *)ctx;
  if(p->real->read_original(p->real->ctx,out)!=1) return 0;
  if(p->reads==0u) {
    if(out->original_epoch!=p->session->epoch) {
      p->blocked=R7_STAGE_CONTINUITY_FAILED;
      return 0;
    }
    if(seen_id(p->session,out->original_epoch,out->request_id)) {
      p->blocked=R7_BAD_LEASE;
      return 0;
    }
    p->first=*out;
  }
  p->reads++;
  return 1;
}
static int scoped_legality(void *ctx,const R7Original *pinned,R7Legal *out) {
  R7Proxy *p=(R7Proxy *)ctx;
  return p->real->read_engine_legality(p->real->ctx,pinned,out);
}

R7Plan r7_session_plan(const R7Host *host,R7Lease *lease,R7Session *session) {
  if(!host || !host->read_original || !host->read_engine_legality ||
     !lease || !session) return deny(R7_BAD_API);
  if(session->initialized!=1u || !session->epoch || session->busy!=0u ||
     session->manual_locked!=0u) return deny(R7_STAGE_CONTINUITY_FAILED);
  if(session->count>=R7_SESSION_REPLAY_CAP) return deny(R7_BAD_LEASE);
  R7Lease trial_lease=*lease;
  R7FightTicket trial_ticket=session->ticket;
  R7Proxy proxy={0};
  proxy.real=host;
  proxy.session=session;
  R7Host scoped={&proxy,scoped_read,scoped_legality};
  session->busy=1u;
  R7Plan result=r7_plan(&scoped,&trial_lease,&trial_ticket);
  session->busy=0u;
  if(proxy.blocked!=R7_REASON_NONE) return deny(proxy.blocked);
  if(result.outcome==R7_DEFER) return result;
  /* Only commit the authenticated-in-model original request identity when
   * both original reads succeeded and the parent adapter consumed the lease. */
  if(proxy.reads!=2u || trial_lease.consumed!=1u ||
     proxy.first.original_epoch!=session->epoch ||
     seen_id(session,proxy.first.original_epoch,proxy.first.request_id))
     return deny(R7_BAD_LEASE);
  session->consumed[session->count].epoch=proxy.first.original_epoch;
  session->consumed[session->count].request_id=proxy.first.request_id;
  session->count++;
  session->ticket=trial_ticket;
  *lease=trial_lease;
  return result;
}

int r7_session_manual_takeover(R7Session *session,const R7ManualHost *host) {
  if(!session || session->initialized!=1u || session->busy!=0u ||
     session->manual_locked!=0u || session->ticket.pending!=1u ||
     session->ticket.epoch!=session->epoch ||
     !host || !host->verify_original_manual_takeover) return 0;
  session->busy=1u;
  R7FightTicket ticket=session->ticket;
  int verified=host->verify_original_manual_takeover(host->ctx,&ticket);
  session->busy=0u;
  if(verified!=1) return 0;
  /* Force manual for the rest of this epoch. Clearing a pending ticket alone
   * would let a stale ChooseAction enter automation again. */
  session->ticket.pending=0u;
  session->manual_locked=1u;
  return 1;
}

int r7_session_advance_epoch(R7Session *session,const R7BoundaryHost *host) {
  if(!session || session->initialized!=1u || session->busy!=0u ||
     !host || !host->read_verified_boundary) return 0;
  R7EpochBoundary boundary={0};
  session->busy=1u;
  int verified=host->read_verified_boundary(host->ctx,&boundary);
  session->busy=0u;
  if(verified!=1 || boundary.from_epoch!=session->epoch ||
     boundary.to_epoch<=boundary.from_epoch ||
     boundary.observed_battle_closed!=1u ||
     boundary.observed_controller_idle!=1u) return 0;
  /* Do NOT call public initializer: it rejects same-storage reinitialization
   * specifically to stop accidental clearing of a consumed request ledger. */
  memset(session,0,sizeof *session);
  session->epoch=boundary.to_epoch;
  session->initialized=1u;
  return 1;
}
