#include "player0_fail_closed_guard.h"
#include <stddef.h>

static struct sg_guard_output manual(enum sg_guard_reason reason) {
  struct sg_guard_output out = {SG_DEFER_TO_ORIGINAL_MANUAL, reason, SG_NO_SLOT, SG_NO_ACTION, 1u, 0u};
  return out;
}

struct sg_guard_output sg_guard_evaluate(const struct sg_guard_input *in) {
  if (in == NULL) return manual(SG_GUARD_UNSUPPORTED_OWNER);
  /* Do not borrow an enemy, NPC partner, double, or second player controller. */
  if (in->battler != SG_BATTLER_PLAYER0 || in->player_owned != 1u)
    return manual(SG_GUARD_UNSUPPORTED_OWNER);
  if (in->wild_single != 1u || in->partner_present != 0u ||
      in->doubles_or_multi != 0u || in->auto_enabled != 1u ||
      in->foe_is_live_enemy != 1u)
    return manual(SG_GUARD_UNSUPPORTED_BATTLE);
  if (in->command != SG_COMMAND_CHOOSE_ACTION && in->command != SG_COMMAND_CHOOSE_MOVE)
    return manual(SG_GUARD_UNSUPPORTED_COMMAND);
  /* These are demands on an eventual game adapter, not evidence of an actual
   * original-engine lease. Absent or drifting evidence MUST defer. */
  if (in->engine_command_authenticated != 1u || in->owner_lease_unconsumed != 1u ||
      in->request_id_before == 0u || in->request_id_before != in->request_id_after ||
      in->turn_before != in->turn_after ||
      in->owner_party_before != in->owner_party_after ||
      in->foe_party_before != in->foe_party_after ||
      in->resources_before == 0u || in->resources_before != in->resources_after ||
      in->controller_flags_before != in->controller_flags_after ||
      in->current_buffer_matches_original != 1u || in->original_menu_payload_matches != 1u)
    return manual(SG_GUARD_STALE_REQUEST);
  if (in->move_limitations_evaluated != 1u || in->target_helpers_evaluated != 1u)
    return manual(SG_GUARD_MISSING_ENGINE_LEGALITY);
  if (((in->legal_move_mask | in->verified_foe_target_mask | in->known_ineffective_mask) & 0xf0u) != 0u)
    return manual(SG_GUARD_MISSING_ENGINE_LEGALITY);
  int selected = -1;
  unsigned best_priority = 0u;
  for (unsigned i=0;i<SG_MAX_MOVES;i++) {
    unsigned bit=1u<<i;
    if (in->moves[i] == 0u || in->moves[i] == UINT16_MAX || in->pp[i] == 0u ||
        !(in->legal_move_mask & bit) || !(in->verified_foe_target_mask & bit) ||
        (in->known_ineffective_mask & bit)) continue;
    if (selected < 0 || in->relative_priority[i] > best_priority) {
      selected = (int)i;
      best_priority = in->relative_priority[i];
    }
  }
  if (selected < 0) return manual(SG_GUARD_NO_ELIGIBLE_MOVE);
  struct sg_guard_output out = {
    in->command == SG_COMMAND_CHOOSE_ACTION ? SG_PROPOSE_FIGHT : SG_PROPOSE_MOVE,
    SG_GUARD_OK, (unsigned)selected,
    in->command == SG_COMMAND_CHOOSE_ACTION ? SG_ACTION_FIGHT : SG_ACTION_MOVE,
    0u, 0u
  };
  return out;
}
