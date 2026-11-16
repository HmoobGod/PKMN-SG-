#include "engine_adapter.h"
#include <string.h>

static R7Plan fail(R7Reason why) {
  R7Plan p={R7_DEFER,why,R7_NO_ACTION,R7_NO_SLOT,1u,0u,0u,0u,0u};
  return p;
}
static int exact_bool(uint8_t x) {return x==0u || x==1u;}
/* Source-layout check for CONTROLLER_CHOOSEMOVE: header[4], then
 * ChooseMoveStruct.moves[4] (little-endian u16), currentPp[4] (u8).
 * These offsets are a SOURCE-ONLY ABI hypothesis until independently
 * authenticated in the exact original ROM. Reject, never guess, on drift. */
static int payload_matches_move_data(const R7Original *s) {
  unsigned i;
  if (s->command!=19u) return 1;
  /* No truncated ChooseMove prefix may authorize a move. Requiring the
   * complete source-side command length binds the entire buffer snapshot,
   * including its opaque trailing fields, through the legality callback. */
  if (s->payload_length!=R7_CHOOSEMOVE_TOTAL_BYTES) return 0;
  /* Original header: command, isDoubleBattle, NoPpNumber, reserved zero.
   * Only the conservative single/no-PP-suppression form is auto eligible;
   * other forms must defer to the ORIGINAL manual controller. */
  if (s->original_header[1]!=(uint8_t)s->doubles ||
      s->original_header[1]!=0u || s->original_header[2]!=0u ||
      s->original_header[3]!=0u) return 0;
  for (i=0u;i<4u;i++) {
    unsigned offset=4u+2u*i;
    uint16_t move=(uint16_t)((uint16_t)s->original_payload[offset] |
       ((uint16_t)s->original_payload[offset+1u]<<8));
    if (move!=s->moves[i] || s->original_payload[12u+i]!=s->pp[i])
      return 0;
  }
  return 1;
}
static int valid_original(const R7Original *s) {
  if (!s || !s->request_id || !s->original_epoch || !s->resources ||
      s->payload_length<4u || s->payload_length>R7_PAYLOAD_CAP) return 0;
  if (s->battler!=0u || (s->command!=17u && s->command!=19u)) return 0;
  if (!exact_bool(s->player_owned) || !exact_bool(s->wild_single) ||
      !exact_bool(s->doubles) || !exact_bool(s->partner) ||
      !exact_bool(s->auto_enabled) || !exact_bool(s->foe_live)) return 0;
  if (s->player_owned!=1u || s->wild_single!=1u || s->doubles!=0u ||
      s->partner!=0u || s->auto_enabled!=1u || s->foe_live!=1u) return 0;
  if (s->original_header[0]!=(uint8_t)s->command ||
      memcmp(s->original_header,s->original_payload,4)!=0 ||
      !payload_matches_move_data(s)) return 0;
  return 1;
}
static int equal_original(const R7Original *a,const R7Original *b) {
  /* Compare each declared field. Do not compare struct padding bytes. */
  return a->original_epoch==b->original_epoch && a->request_id==b->request_id &&
    a->command==b->command && a->battler==b->battler &&
    a->owner_party==b->owner_party && a->foe_party==b->foe_party &&
    a->turn==b->turn && a->resources==b->resources && a->flags==b->flags &&
    a->player_owned==b->player_owned && a->wild_single==b->wild_single &&
    a->doubles==b->doubles && a->partner==b->partner &&
    a->auto_enabled==b->auto_enabled && a->foe_live==b->foe_live &&
    a->payload_length==b->payload_length &&
    memcmp(a->original_header,b->original_header,sizeof a->original_header)==0 &&
    memcmp(a->original_payload,b->original_payload,a->payload_length)==0 &&
    memcmp(a->moves,b->moves,sizeof a->moves)==0 &&
    memcmp(a->pp,b->pp,sizeof a->pp)==0;
}
static int valid_legality(const R7Original *before,const R7Legal *legal) {
  if (!legal || legal->original_epoch!=before->original_epoch ||
      legal->request_id!=before->request_id || legal->turn!=before->turn ||
      legal->move_limitations_verified!=1u || legal->target_helpers_verified!=1u ||
      legal->ineffectiveness_verified!=1u) return 0;
  if (((legal->move_legal_mask|legal->verified_foe_target_mask|
        legal->known_ineffective_mask)&0xf0u)!=0u) return 0;
  return 1;
}

R7Plan r7_plan(const R7Host *host,R7Lease *lease,R7FightTicket *ticket) {
  if (!host || !lease || !ticket || !host->read_original ||
      !host->read_engine_legality) return fail(R7_BAD_API);
  R7Original before={0},after={0};R7Legal legal={0};
  if (host->read_original(host->ctx,&before)!=1) return fail(R7_BAD_ENGINE_READ);
  if (!valid_original(&before)) return fail(R7_UNSUPPORTED_SCOPE);
  if (lease->consumed!=0u || lease->epoch!=before.original_epoch ||
      lease->request_id!=before.request_id) return fail(R7_BAD_LEASE);
  if (host->read_engine_legality(host->ctx,&before,&legal)!=1 ||
      !valid_legality(&before,&legal)) return fail(R7_NO_ENGINE_LEGALITY);
  if (host->read_original(host->ctx,&after)!=1 || !equal_original(&before,&after))
    return fail(R7_ORIGINAL_REQUEST_CHANGED);

  struct sg_guard_input g={0};
  g.battler=before.battler;g.command=before.command;
  g.player_owned=before.player_owned;g.wild_single=before.wild_single;
  g.partner_present=before.partner;g.doubles_or_multi=before.doubles;
  g.auto_enabled=before.auto_enabled;g.foe_is_live_enemy=before.foe_live;
  g.engine_command_authenticated=1u;g.owner_lease_unconsumed=1u;
  g.request_id_before=before.request_id;g.request_id_after=after.request_id;
  g.turn_before=before.turn;g.turn_after=after.turn;
  g.owner_party_before=before.owner_party;g.owner_party_after=after.owner_party;
  g.foe_party_before=before.foe_party;g.foe_party_after=after.foe_party;
  g.resources_before=before.resources;g.resources_after=after.resources;
  g.controller_flags_before=before.flags;g.controller_flags_after=after.flags;
  g.current_buffer_matches_original=1u;g.original_menu_payload_matches=1u;
  g.move_limitations_evaluated=legal.move_limitations_verified;
  g.target_helpers_evaluated=legal.target_helpers_verified;
  g.legal_move_mask=legal.move_legal_mask;
  g.verified_foe_target_mask=legal.verified_foe_target_mask;
  g.known_ineffective_mask=legal.known_ineffective_mask;
  memcpy(g.moves,before.moves,sizeof g.moves);
  memcpy(g.pp,before.pp,sizeof g.pp);
  memcpy(g.relative_priority,legal.priorities,sizeof g.relative_priority);
  struct sg_guard_output outcome=sg_guard_evaluate(&g);
  if (outcome.outcome==SG_DEFER_TO_ORIGINAL_MANUAL || outcome.slot>=4u)
    return fail(R7_NO_VALID_MOVE);
  unsigned s=outcome.slot;
  if (before.command==17u) {
    if (ticket->pending!=0u) return fail(R7_STAGE_CONTINUITY_FAILED);
    /* No response is emitted; the caller may issue Fight only after all
     * original-engine authorizations are independently proven. */
    R7FightTicket next={before.original_epoch,before.turn,before.owner_party,
       before.foe_party,before.moves[s],(uint8_t)s,1u};
    *ticket=next;
  } else {
    if (ticket->pending!=1u || ticket->epoch!=before.original_epoch ||
        ticket->turn!=before.turn || ticket->owner_party!=before.owner_party ||
        ticket->foe_party!=before.foe_party || ticket->slot!=s ||
        ticket->planned_move!=before.moves[s])
      return fail(R7_STAGE_CONTINUITY_FAILED);
    ticket->pending=0u;
  }
  lease->consumed=1u;
  R7Plan p={before.command==17u?R7_FIGHT:R7_MOVE,R7_REASON_NONE,
     before.command==17u?0u:10u,s,0u,0u,0u,0u,0u};
  return p;
}
