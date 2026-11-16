#include "session_lifecycle.h"
#include <string.h>
#include <stdint.h>

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

/* A denied request can already have handed control to the original menu.
 * Never continue an outstanding auto Fight ticket in that menu, even when
 * a later manually issued command 19 has a matching turn/slot/foe. */
static void quarantine(R7Session *s) {
  if(s && s->initialized==1u) {
    s->manual_locked=1u;
    s->ticket.pending=0u;
    s->pending_fight_request_id=0u;
  }
}
static R7Plan quarantine_deny(R7Session *s,R7Reason why) {
  quarantine(s);
  return deny(why);
}

int r7_session_init(R7Session *session, uint32_t first_epoch) {
  if (!session || !first_epoch || first_epoch==UINT32_MAX ||
      session->initialized==1u) return 0;
  memset(session,0,sizeof *session);
  session->epoch=first_epoch;
  session->initialized=1u;
  return 1;
}

static int seen_id(const R7Session *s,uint32_t epoch,uint32_t id) {
  for(unsigned i=0u;i<s->count;i++)
    if(s->consumed[i].epoch==epoch && s->consumed[i].request_id==id)
      return 1;
  return 0;
}

/* Re-check the original host on both adapter reads. A synthetic caller lease
 * with consumed=0 cannot hide a request already consumed in this session.
 * An outstanding Fight ticket authorizes *only* the immediate successor
 * command 19: a new ChooseAction or a skipped request ID is an interruption. */
static int scoped_read(void *ctx,R7Original *out) {
  R7Proxy *p=(R7Proxy *)ctx;
  if(p->real->read_original(p->real->ctx,out)!=1) return 0;
  if(p->reads==0u) {
    if(out->original_epoch!=p->session->epoch) {
      p->blocked=R7_STAGE_CONTINUITY_FAILED;
      return 0;
    }
    if(p->session->ticket.pending==1u &&
       (out->command!=19u ||
        p->session->pending_fight_request_id==0u ||
        p->session->pending_fight_request_id==UINT32_MAX ||
        out->request_id!=p->session->pending_fight_request_id+1u)) {
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
     !lease || !session) return quarantine_deny(session,R7_BAD_API);
  /* A nested planner request is never allowed to emit a second action. The
   * marker also aborts the outer request after its callback unwinds. */
  if(session->busy!=0u) {
    session->reentrant=1u;
    return quarantine_deny(session,R7_STAGE_CONTINUITY_FAILED);
  }
  if(session->initialized!=1u || !session->epoch ||
     session->manual_locked!=0u) return deny(R7_STAGE_CONTINUITY_FAILED);
  if(session->count>=R7_SESSION_REPLAY_CAP)
    return quarantine_deny(session,R7_BAD_LEASE);
  R7Lease trial_lease=*lease;
  R7FightTicket trial_ticket=session->ticket;
  R7Proxy proxy={0};
  proxy.real=host;
  proxy.session=session;
  R7Host scoped={&proxy,scoped_read,scoped_legality};
  session->busy=1u;
  R7Plan result=r7_plan(&scoped,&trial_lease,&trial_ticket);
  session->busy=0u;
  if(session->reentrant!=0u || session->manual_locked!=0u)
    return quarantine_deny(session,R7_STAGE_CONTINUITY_FAILED);
  if(proxy.blocked!=R7_REASON_NONE)
    return quarantine_deny(session,proxy.blocked);
  if(result.outcome==R7_DEFER) {
    /* Liveness concession: only no-ticket, non-corrupt lack-of-legal-move or
     * currently-unavailable legality may retry. Every other defer locks. */
    if(session->ticket.pending==1u ||
       (result.reason!=R7_NO_VALID_MOVE &&
        result.reason!=R7_NO_ENGINE_LEGALITY)) quarantine(session);
    return result;
  }
  if(result.outcome!=R7_FIGHT && result.outcome!=R7_MOVE)
    return quarantine_deny(session,R7_STAGE_CONTINUITY_FAILED);
  if(proxy.reads!=2u || trial_lease.consumed!=1u ||
     proxy.first.original_epoch!=session->epoch ||
     seen_id(session,proxy.first.original_epoch,proxy.first.request_id))
    return quarantine_deny(session,R7_BAD_LEASE);
  if(result.outcome==R7_FIGHT &&
     (session->ticket.pending!=0u || proxy.first.request_id==UINT32_MAX ||
      proxy.first.request_id==0u))
    return quarantine_deny(session,R7_STAGE_CONTINUITY_FAILED);
  if(result.outcome==R7_MOVE &&
     (session->ticket.pending!=1u ||
      session->pending_fight_request_id==0u ||
      session->pending_fight_request_id==UINT32_MAX ||
      proxy.first.request_id!=session->pending_fight_request_id+1u))
    return quarantine_deny(session,R7_STAGE_CONTINUITY_FAILED);
  session->consumed[session->count].epoch=proxy.first.original_epoch;
  session->consumed[session->count].request_id=proxy.first.request_id;
  session->count++;
  session->ticket=trial_ticket;
  session->pending_fight_request_id=result.outcome==R7_FIGHT ?
       proxy.first.request_id:0u;
  *lease=trial_lease;
  return result;
}

int r7_session_manual_takeover(R7Session *session,const R7ManualHost *host) {
  if(!session) return 0;
  if(session->busy!=0u) {
    session->reentrant=1u;
    quarantine(session);
    return 0;
  }
  if(session->initialized!=1u || session->manual_locked!=0u ||
     session->ticket.pending!=1u ||
     session->ticket.epoch!=session->epoch ||
     !host || !host->verify_original_manual_takeover) return 0;
  session->busy=1u;
  R7FightTicket ticket=session->ticket;
  int verified=host->verify_original_manual_takeover(host->ctx,&ticket);
  session->busy=0u;
  if(verified!=1 || session->reentrant!=0u || session->manual_locked!=0u)
    return 0;
  quarantine(session);
  return 1;
}

int r7_session_advance_epoch(R7Session *session,const R7BoundaryHost *host) {
  if(!session) return 0;
  if(session->busy!=0u) {
    session->reentrant=1u;
    quarantine(session);
    return 0;
  }
  if(session->initialized!=1u || !host ||
     !host->read_verified_boundary) return 0;
  R7EpochBoundary boundary={0};
  session->reentrant=0u;
  session->busy=1u;
  int verified=host->read_verified_boundary(host->ctx,&boundary);
  session->busy=0u;
  if(verified!=1 || session->reentrant!=0u ||
     boundary.from_epoch!=session->epoch ||
     boundary.to_epoch<=boundary.from_epoch ||
     boundary.to_epoch==UINT32_MAX ||
     boundary.observed_battle_closed!=1u ||
     boundary.observed_controller_idle!=1u) return 0;
  /* The ORIGINAL host must prove an epoch transition. An untrusted caller can
   * fake this, so this is never native authentication or manual acceptance. */
  memset(session,0,sizeof *session);
  session->epoch=boundary.to_epoch;
  session->initialized=1u;
  return 1;
}
