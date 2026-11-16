#ifndef SG_R7_LIFECYCLE_ADAPTER_H
#define SG_R7_LIFECYCLE_ADAPTER_H
/* Source-only, non-native stateful wrapper for r7_plan. NEVER emits a game
 * response. The caller must preserve this object across requests, and only
 * real original-engine evidence can justify rearming an epoch. */
#include "engine_adapter.h"

#define R7_LIFECYCLE_SEEN_CAP 64u

typedef enum {
  R7_LC_OK=0, R7_LC_BAD_API, R7_LC_BAD_READ, R7_LC_BAD_ORIGINAL,
  R7_LC_DUPLICATE, R7_LC_QUARANTINED, R7_LC_EPOCH_ADVANCE,
  R7_LC_LEDGER_FULL, R7_LC_ADAPTER_DEFER
} R7LifecycleReason;

typedef struct {
  uint32_t epoch;
  uint32_t seen_ids[R7_LIFECYCLE_SEEN_CAP];
  uint8_t seen_count, initialized, quarantined;
  R7FightTicket ticket;
} R7Lifecycle;

typedef struct {
  R7Plan plan;
  R7LifecycleReason lifecycle_reason;
} R7LifecycleResult;

typedef struct {
  uint32_t previous_epoch, new_epoch;
  uint8_t previous_battle_finished_verified;
  uint8_t original_controller_rearmed_verified;
  uint8_t original_response_queue_empty_verified;
} R7RecoveryEvidence;

void r7_lifecycle_init(R7Lifecycle *state);
/* Makes a sourced, two-read, mock-engine proposal. Does not issue a guest
 * response. Repeated IDs in an epoch are rejected even with fresh leases. */
R7LifecycleResult r7_lifecycle_plan(const R7Host *host,R7Lifecycle *state);
/* Fail-closed abandonment: disables automation; requires a separate native
 * manual-menu proof to claim human control was actually restored. */
int r7_lifecycle_abandon(R7Lifecycle *state);
/* Only a NEW epoch with independently host-reported outcome/controller/queue
 * evidence may rearm after quarantine. Host booleans are NOT native proof. */
int r7_lifecycle_rearm(const R7Host *host,R7Lifecycle *state,
                       const R7RecoveryEvidence *proof);
#endif
