#ifndef SG_R7_SESSION_LIFECYCLE_H
#define SG_R7_SESSION_LIFECYCLE_H
/* Source-only, fail-closed lifecycle model; never hooks the real game.
 * This is NOT native engine authentication, manual-menu proof, or replay
 * protection against a malicious/faulty host capable of resetting memory. */
#include "engine_adapter.h"

#define R7_SESSION_REPLAY_CAP 64u

typedef struct {
  uint32_t epoch, request_id;
} R7ConsumedId;

typedef struct {
  uint32_t epoch;
  uint32_t count;
  R7ConsumedId consumed[R7_SESSION_REPLAY_CAP];
  R7FightTicket ticket;
  uint32_t pending_fight_request_id;
  uint8_t initialized, manual_locked, busy, reentrant;
} R7Session;

typedef struct {
  uint32_t from_epoch, to_epoch;
  uint8_t observed_battle_closed, observed_controller_idle;
} R7EpochBoundary;

typedef struct {
  void *ctx;
  /* Must return exactly 1 only when reading an independently verified,
   * original-engine battle boundary. Not yet wired to a ROM callback. */
  int (*read_verified_boundary)(void *ctx, R7EpochBoundary *out);
} R7BoundaryHost;

typedef struct {
  void *ctx;
  /* Must return exactly 1 only when the ORIGINAL manual controller
   * has displayed a controllable menu for the matching pending ticket.
   * Such an engine callback has NOT been identified or certified. */
  int (*verify_original_manual_takeover)(void *ctx, const R7FightTicket *ticket);
} R7ManualHost;

/* A new session is scoped to one engine epoch; no caller-reset or
 * recycled request ID may be presented as native authorization. */
int r7_session_init(R7Session *session, uint32_t first_epoch);
/* Wraps and re-checks the existing approved R7 adapter, maintaining a
 * bounded consumed-identity ledger. A full ledger defers, never evicts.
 * Interrupted Fight tickets lock the rest of the epoch. A mock request ID
 * must increase by exactly one between auto Fight and auto Move; this strict
 * ordering has NOT been authenticated in the uploaded exact ROM. */
R7Plan r7_session_plan(const R7Host *host, R7Lease *lease, R7Session *session);
/* On a verified manual takeover, retire a stuck ticket but LOCK the
 * remaining epoch against auto action, to prevent false resumed auto. */
int r7_session_manual_takeover(R7Session *session, const R7ManualHost *host);
/* Only a verified new, strictly greater engine epoch can clear the ledger,
 * retire its pending ticket, and release manual lock. No wall clock expiry. */
int r7_session_advance_epoch(R7Session *session, const R7BoundaryHost *host);
#endif
