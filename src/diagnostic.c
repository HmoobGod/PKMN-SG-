#include "snapshot.h"
#include "ranker_workspace.h"
#define R8(a) (*(volatile const uint8_t *)(uintptr_t)(a))
#define R16(a) (*(volatile const uint16_t *)(uintptr_t)(a))
struct result {uint32_t status,bytes,pointer,count,actor,slot,target,move,power,accuracy,policy,freed;};
struct scratch {SG_View v;SG_PublicBattleObservation o;SG_Proposal p;};
/* LAB ONLY: speculative candidate masks and local correlation tokens.
   Never engine legality, owner authority, or live action authorization. */
uint32_t sg_run_diagnostic(uint32_t actor,struct result *r) {
 *r=(struct result){.status=1,.actor=actor,.policy=1};
 struct sg_diagnostic_snapshot observed;
 if(sg_capture_diagnostic(actor,&observed))return r->status=2;
 /* Snapshot eligibility once; capture failure must not choose fallback based
    on which output fields happened to be assigned before it failed.
    This is only manual-preview eligibility, never automatic authority. */
 const uint32_t eligible=actor==0 && observed.battle_type_flags==4 &&
     observed.count==2 && observed.present_mask==3;
 typedef void *(*alloc_fn)(uint32_t,uint32_t);
 typedef void (*free_fn)(void *);
 struct scratch *s=((alloc_fn)(uintptr_t)0x081b20c5)(sizeof(*s),0);
 r->bytes=sizeof(*s);r->pointer=(uintptr_t)s;
 if(!s)return r->status=eligible?5:3;
 *s=(struct scratch){0};
 SG_View *v=&s->v;SG_PublicBattleObservation *o=&s->o;
 v->battle_token=o->battle_token=1;v->turn_token=o->turn_token=1;v->choice_token=o->choice_token=1;
 v->controller=1;v->phase=2;v->actor=o->actor=actor;v->battler_count=observed.count;v->supported_mode=true;
 uint8_t foes=0;uint8_t side=observed.position&1;
 for(unsigned i=0;i<observed.count;i++) {
  bool enemy=(R8(0x02001b58+i)&1)!=side;
  o->active[i].role=i==actor?SG_PUBLIC_SELF:enemy?SG_PUBLIC_FOE:SG_PUBLIC_ALLY;
  if(enemy && (observed.present_mask&(1u<<i)))foes|=1u<<i;
 }
 for(unsigned m=0;m<4;m++) {
  uint32_t id=observed.moves[m];
  if(!id || id>=936 || id!=observed.buffer_moves[m] || !observed.pp[m])continue;
  /* Match the native negative Disable predicate; no extra engine call.
     Zero moves were already excluded above. Do not call this full legality. */
  /* Cached native restrictions only exclude; a clear bit is not permission. */
  if(observed.native_restricted_mask&(1u<<m))continue;
  if(id==observed.disabled_move)continue;
  /* Native Encore: timer active restricts every move except its stored ID.
     An expired timer ignores a stale ID; this never establishes permission. */
  if(observed.encore_timer && id!=observed.encored_move)continue;
  /* Native repeat-move exclusion: own flag plus own recorded last ID. */
  if(observed.repeat_blocked && id==observed.last_move)continue;
  /* Metadata extraction from original ROM table; provisional diagnostic adapter.
     Struct bit layout corroborated with historical move.h, not action approval. */
  uint32_t entry=0x0877cc6c+72*id;uint16_t packed=R16(entry+10),target=R16(entry+12);
  /* Original manual menu reads entry+12 >>7 as target mode. Only the
     two observed opponent modes are mapped here; everything else excluded.
     In wild singles both map to the sole opposing position. Still no authority. */
  uint32_t target_mode=target>>7;
  if(target_mode!=1 && target_mode!=6)continue;
  uint32_t power=packed>>7,accuracy=target&127,category=(packed>>5)&3;
  if(!power || accuracy>100 || category>1)continue;
  o->moves[m]=(SG_PublicMove){.known_damaging_move=true,.displayed_base_power=power,.displayed_accuracy=accuracy,.known_always_hits=accuracy==0};
  v->permitted_move_mask|=1u<<m;v->permitted_targets[m]=foes;
 }
 r->count=sg_rank_damage_best(v,o,&s->p);
 if(r->count) {SG_Proposal *p=&s->p;r->slot=p->move_slot;r->target=p->target;r->move=observed.moves[p->move_slot];r->power=o->moves[p->move_slot].displayed_base_power;r->accuracy=o->moves[p->move_slot].displayed_accuracy;}
 /* Exactly one release of the successfully allocated local pointer. */
 ((free_fn)(uintptr_t)0x081b2185)(s);r->freed=1;
 /* ASSIST PREVIEW, not automatic action authority. Only ordinary single
    player slot0; a human must confirm using the existing manual handler.
    No command buffer, selected auto slot, target, or save-option writes. */
 if (eligible && r->count && r->slot<4 && r->target==1 &&
     r->move==observed.moves[r->slot] && observed.pp[r->slot]) {
  /* Recheck local recommendation inputs after scratch lifetime ends.
     No persisting token or permission claim; no call to a restriction helper. */
  uint32_t check=sg_capture_diagnostic(actor,&observed);
  /* A replaced/completed request belongs to the native dispatcher. Do not
     install a manual chooser for a request that is no longer current. */
  if(check==7)return r->status=0;
  if (!check &&
      observed.battle_type_flags==4 && observed.count==2 && observed.present_mask==3 &&
      observed.moves[r->slot]==r->move && observed.buffer_moves[r->slot]==r->move &&
      observed.pp[r->slot] && !(observed.native_restricted_mask&(1u<<r->slot)) && observed.disabled_move!=r->move &&
      (!observed.encore_timer || observed.encored_move==r->move) &&
      (!observed.repeat_blocked || observed.last_move!=r->move)) {
   *(volatile uint8_t *)(uintptr_t)0x02001e54=(uint8_t)r->slot;
   return r->status=4; /* wrapper opens manual chooser; no emitter call */
  }
 }
 /* Eligible no-result previews remain manual, without moving the cursor. */
 if (eligible)return r->status=5;
 return r->status=0;
}
