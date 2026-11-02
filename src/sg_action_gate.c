#include "sg_action_gate.h"
#include "sg_baseline_mode_guard.h"
bool sg_validate(const SG_View *v, const SG_Proposal *p)
{
    if (!v || !p || v->controller != 1 || !v->supported_mode ||
        !sg_baseline_normal_mode(v->battle_mode_flags) ||
        v->engine_locked || v->irq_busy || p->actor != v->actor ||
        v->actor >= v->battler_count ||
        (v->battler_count != 2 && v->battler_count != 4) ||
        v->battle_token != p->battle_token || v->turn_token != p->turn_token ||
        v->choice_token != p->choice_token ||
        !v->battle_token || !v->turn_token || !v->choice_token)
        return false;
    /* Fail closed if the engine supplied malformed legality masks. Bits
     * beyond the four move slots, six party slots or active battlers are
     * never valid even if the selected slot itself would pass. */
    if ((v->permitted_move_mask & 0xf0u) != 0u ||
        (v->permitted_switch_mask & 0xc0u) != 0u)
        return false;
    const unsigned allowed_targets = (1u << v->battler_count) - 1u;
    for (unsigned i = 0; i < 4u; ++i)
        if ((v->permitted_targets[i] & ~allowed_targets) != 0u)
            return false;
    /* Action menu and final choice must never be conflated: in the baseline,
     * opening Fight is B_ACTION_USE_MOVE, whereas choosing a move happens in
     * a separate CONTROLLER_CHOOSEMOVE callback. Party likewise has its own
     * CONTROLLER_CHOOSEPOKEMON request after B_ACTION_SWITCH. */
    if (p->action == SG_ENTER_FIGHT) {
        if (v->phase != 1 || v->forced_switch || v->forced_struggle ||
            v->permitted_move_mask == 0u)
            return false;
        /* Do not open Fight if every engine-approved move has zero legal
         * targets. A populated target list for a DISABLED move does not
         * make the action menu usable. This is an authoritative mask check,
         * not an inference from enemy HP or hidden information. */
        bool has_legal_move_target = false;
        for (unsigned i = 0u; i < 4u; ++i) {
            if ((v->permitted_move_mask & (1u << i)) != 0u &&
                v->permitted_targets[i] != 0u) {
                has_legal_move_target = true;
                break;
            }
        }
        if (!has_legal_move_target) return false;
        return p->move_slot == 0 && p->target == 0 && p->switch_slot == 0;
    }
    if (p->action == SG_OPEN_PARTY) {
        if (v->phase != 1 || v->forced_switch || v->forced_struggle ||
            v->permitted_switch_mask == 0)
            return false;
        return p->move_slot == 0 && p->target == 0 && p->switch_slot == 0;
    }
    if (p->action == SG_SWITCH) {
        if (v->phase != 3 || v->forced_struggle || p->switch_slot >= 6 ||
            p->move_slot != 0 || p->target != 0) return false;
        return (v->permitted_switch_mask & (1u << p->switch_slot)) != 0;
    }
    if (p->action == SG_USE_MOVE) {
        if (v->phase != 2 || v->forced_switch || v->forced_struggle ||
            p->switch_slot != 0) return false;
        /* Do not synthesize a Struggle command: the engine owns it. */
        if (p->move_slot >= 4 || p->target >= v->battler_count) return false;
        if (!(v->permitted_move_mask & (1u << p->move_slot))) return false;
        return (v->permitted_targets[p->move_slot] & (1u << p->target)) != 0;
    }
    /* No item, ball, run, or unrecognized action emission. */
    return false;
}
