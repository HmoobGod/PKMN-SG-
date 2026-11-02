#ifndef SG_RANKER_WORKSPACE_H
#define SG_RANKER_WORKSPACE_H
#include "sg_public_move_ranker.h"
typedef struct { SG_Proposal proposal; int32_t score; } SG_WorkspaceChoice;
typedef struct { SG_WorkspaceChoice ranked[SG_PUBLIC_MAX_CHOICES]; } SG_RankWorkspace;
/* Caller-owned, exclusive, aligned scratch; no global storage or game allocation.
 * Result is a proposal under supplied masks, never native permission evidence. */
size_t sg_rank_public_damage_workspace(const SG_View *,const SG_PublicBattleObservation *,SG_Proposal *,size_t,SG_RankWorkspace *);
/* Restricted damage-only projection. Unsupported tactical/type modes fail closed.
   Returns full damage candidate count and writes only the first stable best. */
size_t sg_rank_damage_best(const SG_View *,const SG_PublicBattleObservation *,SG_Proposal *);

#endif
