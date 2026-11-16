#ifndef SG_PLAYER0_FAIL_CLOSED_GUARD_H
#define SG_PLAYER0_FAIL_CLOSED_GUARD_H
/* Public, source-only reference gate. It never calls the game or writes guest memory.
 * Requires an independent, engine-backed adapter before any playable integration. */
#include <stdint.h>
#define SG_MAX_MOVES 4u
#define SG_COMMAND_CHOOSE_ACTION 17u
#define SG_COMMAND_CHOOSE_MOVE 19u
#define SG_BATTLER_PLAYER0 0u
#define SG_ACTION_FIGHT 0u
#define SG_ACTION_MOVE 10u
#define SG_NO_ACTION UINT32_MAX
#define SG_NO_SLOT UINT32_MAX

enum sg_guard_outcome { SG_DEFER_TO_ORIGINAL_MANUAL=0, SG_PROPOSE_FIGHT=1, SG_PROPOSE_MOVE=2 };
enum sg_guard_reason {
  SG_GUARD_OK=0, SG_GUARD_UNSUPPORTED_OWNER, SG_GUARD_UNSUPPORTED_BATTLE,
  SG_GUARD_UNSUPPORTED_COMMAND, SG_GUARD_STALE_REQUEST,
  SG_GUARD_MISSING_ENGINE_LEGALITY, SG_GUARD_NO_ELIGIBLE_MOVE
};
struct sg_guard_input {
  uint32_t battler, command;
  uint32_t player_owned, wild_single, partner_present, doubles_or_multi;
  uint32_t auto_enabled, engine_command_authenticated, owner_lease_unconsumed, foe_is_live_enemy;
  uint32_t request_id_before, request_id_after;
  uint32_t turn_before, turn_after;
  uint32_t owner_party_before, owner_party_after, foe_party_before, foe_party_after;
  uint32_t resources_before, resources_after;
  uint32_t controller_flags_before, controller_flags_after;
  uint32_t current_buffer_matches_original, original_menu_payload_matches;
  uint32_t move_limitations_evaluated, target_helpers_evaluated;
  uint8_t legal_move_mask, verified_foe_target_mask, known_ineffective_mask;
  uint16_t moves[SG_MAX_MOVES];
  uint8_t pp[SG_MAX_MOVES], relative_priority[SG_MAX_MOVES];
};
struct sg_guard_output {
  enum sg_guard_outcome outcome;
  enum sg_guard_reason reason;
  unsigned slot;
  unsigned action; /* only FIGHT or MOVE; no SWITCH or ITEM output exists */
  unsigned requires_verified_manual_controller; /* true for every defer */
  unsigned native_accepted; /* always zero: cannot attest runtime from this module */
};
struct sg_guard_output sg_guard_evaluate(const struct sg_guard_input *in);
#endif
