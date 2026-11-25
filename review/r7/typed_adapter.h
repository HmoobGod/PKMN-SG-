#ifndef SG_R7_TYPED_ADAPTER_H
#define SG_R7_TYPED_ADAPTER_H
#include "engine_adapter.h"
#include "ranker_workspace.h"

/* Composition of the existing source-only controller and scorer. A real
 * engine adapter must independently prove both callbacks and their freshness.
 * This interface cannot issue native actions or certify gameplay. */
typedef struct {
    R7Host engine;
    int (*read_rank_observation)(void *ctx, const R7Original *pinned,
                                 SG_PublicBattleObservation *out);
} R7TypedHost;
R7Plan r7_plan_typed(const R7TypedHost *, R7Lease *, R7FightTicket *);
#endif
