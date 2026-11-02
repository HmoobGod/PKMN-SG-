#ifndef SG_ACTION_GATE_H
#define SG_ACTION_GATE_H
#include <stdint.h>
#include <stdbool.h>
/* Host-side reference gate, NOT integrated into the game. Masks must originate in
   the live engine; this module does not infer legality from visible HP or cursors. */
typedef enum {SG_NONE=0, SG_USE_MOVE=1, SG_SWITCH=2, SG_ITEM=3, SG_RUN=4, SG_ENTER_FIGHT=5, SG_OPEN_PARTY=6} SG_Action;
typedef struct {
    uint32_t battle_token, turn_token, choice_token;
    uint32_t battle_mode_flags;
    uint8_t controller, phase, actor, battler_count;
    uint8_t permitted_move_mask, permitted_switch_mask;
    uint8_t permitted_targets[4]; /* engine-derived per move; bit per battler */
    bool supported_mode; /* authoritative engine allowlist, not "flags == 0" */
    bool engine_locked, irq_busy, forced_struggle, forced_switch;
} SG_View;
typedef struct {
    uint32_t battle_token, turn_token, choice_token;
    SG_Action action;
    uint8_t actor; /* selected battler; must equal the live player-controller actor */
    uint8_t move_slot, target, switch_slot;
} SG_Proposal;
/* Controller value 1 matches BATTLE_CONTROLLER_PLAYER in the supplied
   baseline soulgold-master; experimental native mapping is NOT verified.
   Phase 1=action menu, 2=move selection, 3=party slot selection.
   These labels do not claim to be engine-native phase enum values.
   SG_ENTER_FIGHT and SG_OPEN_PARTY return action-menu choices only,
   SG_USE_MOVE returns a specific move/target, SG_SWITCH chooses a party slot.
   The engine must independently establish legality of opening the party
   and selecting each party slot (and must handle forced Struggle).
   supported_mode MUST be true only after an engine-side allowlist excludes
   link, recorded, NPC-partner, safari, tutorial, and special controllers.
   battle_mode_flags records the raw value, including ordinary trainer/doubles. */
bool sg_validate(const SG_View *v, const SG_Proposal *p);
#endif
