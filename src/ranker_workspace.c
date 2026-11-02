#include "ranker_workspace.h"

typedef SG_WorkspaceChoice SG_RankedChoice;

static bool sg_workspace_observation_valid(const SG_View *v,
                                 const SG_PublicBattleObservation *o)
{
    if (!v || !o || v->phase != 2u || v->forced_switch || v->forced_struggle ||
        v->battle_token == 0u || v->turn_token == 0u || v->choice_token == 0u ||
        v->battle_token != o->battle_token || v->turn_token != o->turn_token ||
        v->choice_token != o->choice_token || v->actor != o->actor ||
        v->actor >= v->battler_count ||
        (v->battler_count != 2u && v->battler_count != 4u) ||
        (o->known_ally_hit_move_mask & 0xf0u) != 0u ||
        (o->known_partner_safe_move_mask & 0xf0u) != 0u ||
        (o->known_self_ko_move_mask & 0xf0u) != 0u ||
        (o->known_non_self_ko_move_mask & 0xf0u) != 0u ||
        (o->known_self_ko_move_mask & o->known_non_self_ko_move_mask) != 0u ||
        (o->known_ally_hit_move_mask & o->known_partner_safe_move_mask) != 0u)
        return false;
    if (!o->use_public_support_tactics) {
        if (o->known_self_heal_move_mask || o->known_self_setup_move_mask ||
            o->ready_self_setup_move_mask || o->known_own_screen_move_mask ||
            o->ready_own_screen_move_mask || o->known_foe_hazard_move_mask ||
            o->ready_foe_hazard_move_mask || o->known_weather_move_mask ||
            o->ready_weather_move_mask || o->known_terrain_move_mask ||
            o->ready_terrain_move_mask || o->known_self_guard_move_mask ||
            o->ready_self_guard_move_mask || o->known_foe_leech_move_mask ||
            o->ready_foe_leech_target_mask || o->known_foe_status_move_mask ||
            o->known_owned_ally_heal_move_mask ||
            o->verified_player_owned_ally_mask ||
            o->ready_owned_ally_heal_target_mask ||
            o->verified_owned_ally_context_mask ||
            o->verified_last_field_turn_attack_mask ||
            o->public_foe_condition_known_mask || o->public_foe_healthy_mask ||
            o->own_current_hp ||
            o->own_max_hp) return false;
    } else {
        const unsigned classified = o->known_self_heal_move_mask |
                                    o->known_self_setup_move_mask |
                                    o->known_own_screen_move_mask |
                                    o->known_foe_hazard_move_mask |
                                    o->known_weather_move_mask |
                                    o->known_terrain_move_mask |
                                    o->known_self_guard_move_mask |
                                    o->known_foe_leech_move_mask |
                                    o->known_foe_status_move_mask |
                                    o->known_owned_ally_heal_move_mask;
        const unsigned self_support = o->known_self_heal_move_mask |
                                      o->known_self_setup_move_mask |
                                      o->known_own_screen_move_mask |
                                      o->known_weather_move_mask |
                                      o->known_terrain_move_mask |
                                      o->known_self_guard_move_mask;
        if (!o->require_owned_move_identity_proof ||
            !o->require_non_self_ko_proof ||
            !o->own_max_hp || !o->own_current_hp ||
            o->own_current_hp > o->own_max_hp ||
            (classified & 0xf0u) != 0u ||
            (o->ready_self_setup_move_mask & 0xf0u) != 0u ||
            (o->ready_own_screen_move_mask & 0xf0u) != 0u ||
            (o->ready_foe_hazard_move_mask & 0xf0u) != 0u ||
            (o->ready_weather_move_mask & 0xf0u) != 0u ||
            (o->ready_terrain_move_mask & 0xf0u) != 0u ||
            (o->ready_self_guard_move_mask & 0xf0u) != 0u ||
            (o->ready_foe_leech_target_mask & 0xf0u) != 0u ||
            (o->known_owned_ally_heal_move_mask & 0xf0u) != 0u ||
            (o->verified_player_owned_ally_mask & 0xf0u) != 0u ||
            (o->verified_owned_ally_context_mask & 0xf0u) != 0u ||
            (o->verified_last_field_turn_attack_mask & 0xf0u) != 0u ||
            (o->verified_last_field_turn_attack_mask &&
             (!o->require_non_self_ko_proof ||
              !o->require_owned_move_identity_proof)) ||
            (o->verified_owned_ally_context_mask &&
             (v->battler_count != 4u || !o->require_partner_safe_proof ||
              !o->require_owned_move_identity_proof ||
              !o->require_non_self_ko_proof)) ||
            (o->ready_owned_ally_heal_target_mask & 0xf0u) != 0u ||
            (o->ready_owned_ally_heal_target_mask &
                ~o->verified_player_owned_ally_mask) != 0u ||
            (o->known_owned_ally_heal_move_mask &&
                v->battler_count != 4u) ||
            (o->verified_player_owned_ally_mask &&
                (!o->known_owned_ally_heal_move_mask ||
                 v->battler_count != 4u)) ||
            (o->public_foe_condition_known_mask & 0xf0u) != 0u ||
            (o->public_foe_healthy_mask & 0xf0u) != 0u ||
            (o->known_self_heal_move_mask & o->known_self_setup_move_mask) ||
            (o->known_own_screen_move_mask & (o->known_self_heal_move_mask |
                                             o->known_self_setup_move_mask)) ||
            (o->known_weather_move_mask & (o->known_self_heal_move_mask |
                o->known_self_setup_move_mask | o->known_own_screen_move_mask)) ||
            (o->known_terrain_move_mask & (o->known_self_heal_move_mask |
                o->known_self_setup_move_mask | o->known_own_screen_move_mask |
                o->known_weather_move_mask)) ||
            (o->known_self_guard_move_mask & (o->known_self_heal_move_mask |
                o->known_self_setup_move_mask | o->known_own_screen_move_mask |
                o->known_weather_move_mask | o->known_terrain_move_mask)) ||
            (o->known_owned_ally_heal_move_mask &
                (self_support | o->known_foe_status_move_mask |
                 o->known_foe_leech_move_mask |
                 o->known_foe_hazard_move_mask)) ||
            (o->known_foe_status_move_mask & self_support) ||
            (o->known_foe_leech_move_mask & (self_support |
                o->known_foe_status_move_mask | o->known_foe_hazard_move_mask)) ||
            (o->known_foe_hazard_move_mask & (self_support |
                                               o->known_foe_status_move_mask)) ||
            (o->public_foe_healthy_mask & ~o->public_foe_condition_known_mask) ||
            (o->ready_self_setup_move_mask & ~o->known_self_setup_move_mask) ||
            (o->ready_own_screen_move_mask & ~o->known_own_screen_move_mask) ||
            (o->ready_foe_hazard_move_mask & ~o->known_foe_hazard_move_mask) ||
            (o->ready_weather_move_mask & ~o->known_weather_move_mask) ||
            (o->ready_terrain_move_mask & ~o->known_terrain_move_mask) ||
            (o->ready_self_guard_move_mask & ~o->known_self_guard_move_mask) ||
            (o->ready_foe_leech_target_mask && !o->known_foe_leech_move_mask) ||
            (classified & ~o->known_non_self_ko_move_mask) ||
            (classified & o->known_self_ko_move_mask) ||
            ((self_support | o->known_owned_ally_heal_move_mask) &
                (o->known_partner_safe_move_mask |
                 o->known_ally_hit_move_mask)) ||
            ((o->known_foe_status_move_mask |
              o->known_foe_hazard_move_mask |
              o->known_foe_leech_move_mask) & o->known_ally_hit_move_mask))
            return false;
        for (unsigned t = 0u; t < 4u; ++t) {
            /* A partner's public position is not proof of player ownership.
             * Both the owner and current need must be positively verified. */
            if (o->verified_player_owned_ally_mask & (1u << t)) {
                if (t >= v->battler_count || t == v->actor ||
                    o->active[t].role != SG_PUBLIC_ALLY) return false;
            }
            if (o->verified_owned_ally_context_mask & (1u << t)) {
                if (t >= v->battler_count || t == v->actor ||
                    o->active[t].role != SG_PUBLIC_ALLY ||
                    o->active[t].visible_hp_band == SG_HP_BAR_UNOBSERVED)
                    return false;
            }
            if (o->ready_foe_leech_target_mask & (1u << t)) {
                if (t >= v->battler_count ||
                    o->active[t].role != SG_PUBLIC_FOE) return false;
            }
            if (!(o->public_foe_condition_known_mask & (1u << t))) continue;
            if (t >= v->battler_count ||
                o->active[t].role != SG_PUBLIC_FOE) return false;
        }
        for (unsigned m = 0u; m < 4u; ++m) {
            if (o->verified_last_field_turn_attack_mask & (1u << m)) {
                if (!o->moves[m].known_damaging_move ||
                    !(o->known_non_self_ko_move_mask & (1u << m)) ||
                    (o->known_self_ko_move_mask & (1u << m)) ||
                    !o->owned_move_identity[m] ||
                    o->owned_move_identity[m] != o->classified_move_identity[m])
                    return false;
            }
            if (!(classified & (1u << m))) continue;
            const SG_PublicMove *known = &o->moves[m];
            if (known->known_damaging_move ||
                o->owned_move_identity[m] == 0u ||
                o->owned_move_identity[m] != o->classified_move_identity[m])
                return false;
            if ((o->known_foe_status_move_mask |
                 o->known_foe_hazard_move_mask |
                 o->known_foe_leech_move_mask) & (1u << m)) {
                if (known->displayed_accuracy > 100u ||
                    (known->displayed_accuracy == 0u &&
                     !known->known_always_hits) ||
                    known->known_priority < -7 ||
                    known->known_priority > 7) return false;
            }
        }
    }
    if (o->require_owned_move_identity_proof) {
        for (unsigned m = 0u; m < 4u; ++m) {
            const unsigned bit = 1u << m;
            if (o->owned_move_identity[m] != o->classified_move_identity[m] ||
                ((o->known_partner_safe_move_mask | o->known_ally_hit_move_mask |
                  o->known_self_ko_move_mask | o->known_non_self_ko_move_mask) & bit &&
                 o->owned_move_identity[m] == 0u) ||
                (o->moves[m].known_damaging_move &&
                 o->owned_move_identity[m] == 0u))
                return false;
        }
    }
    if (o->use_public_type_heuristic && o->use_engine_type_effect_heuristic)
        return false;
    if (o->engine_type_effect_bound &&
        (!o->use_engine_type_effect_heuristic ||
         !o->require_owned_move_identity_proof)) return false;
    if (!o->use_engine_type_effect_heuristic) {
        if (o->engine_type_effect_bound || o->effect_known_move_mask ||
            o->effect_public_foe_mask) return false;
    } else if (!o->engine_type_effect_bound ||
               (o->effect_known_move_mask & 0xf0u) ||
               (o->effect_public_foe_mask & 0xf0u)) return false;
    for (unsigned m = 0; m < 4u; ++m) {
        const bool known_move = (o->effect_known_move_mask & (1u << m)) != 0u;
        if (known_move && (!o->owned_move_identity[m] ||
                           o->owned_move_identity[m] != o->classified_move_identity[m] ||
                           !o->moves[m].known_damaging_move)) return false;
        for (unsigned t = 0; t < 4u; ++t) {
            const bool known_foe = (o->effect_public_foe_mask & (1u << t)) != 0u;
            const unsigned eff = o->effect_quarters[m][t];
            if (!o->use_engine_type_effect_heuristic || !known_move || !known_foe) {
                if (eff != 0u) return false;
            } else if (t >= v->battler_count ||
                       o->active[t].role != SG_PUBLIC_FOE ||
                       (eff != 0u && eff != 1u && eff != 2u &&
                        eff != 4u && eff != 8u && eff != 16u)) return false;
        }
    }
    for (unsigned t = 0; t < 4u; ++t) {
        if ((o->effect_public_foe_mask & (1u << t)) &&
            (t >= v->battler_count || o->active[t].role != SG_PUBLIC_FOE))
            return false;
    }
    if (o->type_heuristic_bound && (!o->use_public_type_heuristic ||
        !o->require_owned_move_identity_proof)) return false;
    if (!o->use_public_type_heuristic) {
        if (o->public_foe_type_mask != 0u) return false;
        for (unsigned i = 0u; i < 4u; ++i)
            if (o->owned_move_type[i] || o->foe_type1[i] || o->foe_type2[i])
                return false;
    } else {
        if (o->public_foe_type_mask & 0xf0u) return false;
        for (unsigned i = 0u; i < 4u; ++i) {
            const bool typed = (o->public_foe_type_mask & (1u << i)) != 0u;
            if (o->owned_move_type[i] > SG_PUBLIC_TYPE_MAX ||
                o->foe_type1[i] > SG_PUBLIC_TYPE_MAX ||
                o->foe_type2[i] > SG_PUBLIC_TYPE_MAX ||
                (typed && (i >= v->battler_count ||
                           o->active[i].role != SG_PUBLIC_FOE ||
                           o->foe_type1[i] == SG_TYPE_UNKNOWN ||
                           o->foe_type1[i] == o->foe_type2[i])) ||
                (!typed && (o->foe_type1[i] || o->foe_type2[i])))
                return false;
        }
    }
    /* Reject a contradictory role map rather than guessing that active[0]
     * is the human player or that a specific bit identifies a side. */
    if (o->active[v->actor].role != SG_PUBLIC_SELF) return false;
    unsigned selves = 0u, foes = 0u;
    for (unsigned i = 0u; i < 4u; ++i) {
        if (o->active[i].role > SG_PUBLIC_FOE ||
            o->active[i].visible_hp_band > SG_HP_BAR_HIGH) return false;
        if (i >= v->battler_count) {
            if (o->active[i].role != SG_PUBLIC_UNKNOWN ||
                o->active[i].visible_hp_band != SG_HP_BAR_UNOBSERVED)
                return false;
        } else {
            selves += o->active[i].role == SG_PUBLIC_SELF;
            foes += o->active[i].role == SG_PUBLIC_FOE;
        }
    }
    if (selves != 1u || foes != v->battler_count / 2u) return false;
    /* Every active role must be definite and the other friendly actor in
     * doubles must be an ally, never silently treated as a second self. */
    for (unsigned i = 0u; i < v->battler_count; ++i)
        if (o->active[i].role == SG_PUBLIC_UNKNOWN) return false;
    /* Bad metadata on any known move is evidence of a broken adapter;
     * do not rank a different move from the same observation. */
    for (unsigned m = 0u; m < 4u; ++m) {
        const SG_PublicMove *move = &o->moves[m];
        if (!move->known_damaging_move) continue;
        if (move->displayed_base_power == 0u ||
            move->displayed_base_power > 999u ||
            move->displayed_accuracy > 100u ||
            (move->displayed_accuracy == 0u && !move->known_always_hits) ||
            move->known_priority < -7 || move->known_priority > 7)
            return false;
    }
    return true;
}

static int32_t sg_move_score(const SG_PublicMove *move,
                              const SG_PublicBattler *target,
                              int effectiveness_quarters)
{
    /* Entire score uses only the user's known move description and the
     * opponent's displayed HP BAR band. It cannot predict type/ability,
     * PP changes, exact damage, held items, or opponent intentions. */
    const int32_t accuracy = move->known_always_hits ? 100 : move->displayed_accuracy;
    int32_t score = ((int32_t)move->displayed_base_power * accuracy *
                      effectiveness_quarters) / 4;
    score += (int32_t)move->known_priority * 150;
    if (target->visible_hp_band == SG_HP_BAR_CRITICAL) score += 1200;
    else if (target->visible_hp_band == SG_HP_BAR_LOW) score += 800;
    else if (target->visible_hp_band == SG_HP_BAR_MID) score += 400;
    return score;
}

/* Keep the top 16 stable proposals even when all 16 damage/target pairs
 * are legal and self-support candidates are also available. This preserves
 * the existing fixed-size public API without a partial-output overflow. */
static void sg_insert_ranked(SG_RankedChoice sorted[SG_PUBLIC_MAX_CHOICES],
                             size_t *used, SG_RankedChoice item)
{
    size_t insert = *used;
    while (insert > 0u && sorted[insert - 1u].score < item.score)
        --insert;
    if (insert >= SG_PUBLIC_MAX_CHOICES) return;
    const size_t end = *used < SG_PUBLIC_MAX_CHOICES ? (*used)++ :
                                                          SG_PUBLIC_MAX_CHOICES - 1u;
    for (size_t i = end; i > insert; --i) sorted[i] = sorted[i - 1u];
    sorted[insert] = item;
}

static bool sg_workspace_overlap(uintptr_t a,size_t an,uintptr_t b,size_t bn) {
    return a<=b ? b-a<an : a-b<bn;
}
size_t sg_rank_public_damage_workspace(const SG_View *view,
    const SG_PublicBattleObservation *observation,
    SG_Proposal *out, size_t capacity, SG_RankWorkspace *workspace)
{
    if (!workspace || !view || !observation || !out || capacity < SG_PUBLIC_MAX_CHOICES ||
        !sg_workspace_observation_valid(view, observation)) return 0u;
    const uintptr_t w=(uintptr_t)workspace;
    if (sg_workspace_overlap(w,sizeof(*workspace),(uintptr_t)view,sizeof(*view)) ||
        sg_workspace_overlap(w,sizeof(*workspace),(uintptr_t)observation,sizeof(*observation)) ||
        sg_workspace_overlap(w,sizeof(*workspace),(uintptr_t)out,sizeof(*out)*SG_PUBLIC_MAX_CHOICES)) return 0u;
    SG_RankedChoice *ranked=workspace->ranked;
    size_t used = 0u;
    for (unsigned m = 0u; m < 4u; ++m) {
        if (!observation->moves[m].known_damaging_move) continue;
        /* In doubles, a foe-target choice can still splash an ally.
         * Publicly known partner-hitting moves are excluded regardless of
         * their engine-legal single-target mask or apparent damage score. */
        if ((observation->known_self_ko_move_mask & (1u << m)) != 0u ||
            (observation->require_non_self_ko_proof &&
             !(observation->known_non_self_ko_move_mask & (1u << m))))
            continue;
        if (view->battler_count == 4u &&
            ((observation->known_ally_hit_move_mask & (1u << m)) ||
             (observation->require_partner_safe_proof &&
              !(observation->known_partner_safe_move_mask & (1u << m)))))
            continue;
        for (unsigned t = 0u; t < view->battler_count; ++t) {
            if (observation->active[t].role != SG_PUBLIC_FOE) continue;
            SG_Proposal p = {0};
            p.battle_token = view->battle_token;
            p.turn_token = view->turn_token;
            p.choice_token = view->choice_token;
            p.actor = view->actor;
            p.action = SG_USE_MOVE;
            p.move_slot = (uint8_t)m;
            p.target = (uint8_t)t;
            if (!sg_validate(view, &p)) continue;
            int eff = 4;
            if (observation->use_engine_type_effect_heuristic &&
                (observation->effect_known_move_mask & (1u << m)) &&
                (observation->effect_public_foe_mask & (1u << t))) {
                eff = observation->effect_quarters[m][t];
                if (eff == 0) continue; /* Verified type-only immunity */
            }
            if (observation->use_public_type_heuristic &&
                observation->owned_move_type[m] &&
                (observation->public_foe_type_mask & (1u << t))) {
                eff = sg_public_type_effect_quarters(
                    observation->owned_move_type[m],
                    observation->foe_type1[t], observation->foe_type2[t]);
                if (eff <= 0) continue; /* Known type immunity: no attack */
            }
            int32_t score = sg_move_score(&observation->moves[m],
                                          &observation->active[t], eff);
            /* Doubles urgency: only when SAME-PLAYER ally ownership and its
             * publicly visible LOW/CRITICAL HP are positively established.
             * Prefer a known priority attack on a similarly vulnerable foe,
             * never to the detriment of legality, FF safety, type immunity
             * or stronger proven damage (bounded +450). No hidden reads. */
            if (view->battler_count == 4u &&
                observation->verified_owned_ally_context_mask &&
                observation->moves[m].known_priority > 0 &&
                (observation->active[t].visible_hp_band == SG_HP_BAR_LOW ||
                 observation->active[t].visible_hp_band == SG_HP_BAR_CRITICAL)) {
                for (unsigned a = 0u; a < view->battler_count; ++a) {
                    if (!(observation->verified_owned_ally_context_mask & (1u << a)))
                        continue;
                    if (observation->active[a].visible_hp_band == SG_HP_BAR_LOW ||
                        observation->active[a].visible_hp_band == SG_HP_BAR_CRITICAL)
                        score += 450;
                }
            }
            /* Limited timing incentive when current native rules positively
             * attest this exact attack benefits on the field's final live
             * turn. No new action, forecast, inferred damage or targeting. */
            if ((observation->verified_last_field_turn_attack_mask & (1u << m)) &&
                observation->active[t].visible_hp_band != SG_HP_BAR_HIGH &&
                observation->active[t].visible_hp_band != SG_HP_BAR_UNOBSERVED)
                score += 300;
            SG_RankedChoice item = {p, score};
            /* Stable score descending, capped at 16; never overflow. */
            sg_insert_ranked(ranked, &used, item);
        }
    }
    /* Entirely player-owned support decisions: healing does not need to
     * guess incoming damage or the opponent's intended action. Setup is
     * legal only with positive current-stage readiness supplied by the
     * adapter; it is not repeatedly spammed after the stat reaches its cap.
     * The native engine target mask still authorizes the SELF target. */
    if (observation->use_public_support_tactics) {
        /* Multiply before comparing: avoid truncating 40.5% to 40%. */
        const uint32_t scaled_hp =
            (uint32_t)observation->own_current_hp * 100u;
        const uint32_t scaled_max = observation->own_max_hp;
        for (unsigned m = 0u; m < 4u; ++m) {
            const unsigned bit = 1u << m;
            int32_t support_score = 0;
            if ((observation->known_self_heal_move_mask & bit) && scaled_hp <= 40u * scaled_max)
                support_score = 500000; /* urgent recovery over even strong attacks */
            else if ((observation->ready_self_setup_move_mask & bit) &&
                     scaled_hp >= 70u * scaled_max)
                support_score = 2500; /* prefer only to a very weak attack */
            else if ((observation->ready_own_screen_move_mask & bit) &&
                     scaled_hp >= 60u * scaled_max)
                support_score = 3500; /* known useful defensive side effect */
            else if ((observation->ready_weather_move_mask & bit) &&
                     scaled_hp >= 75u * scaled_max)
                support_score = 2300; /* guarded, lower priority field turn */
            else if ((observation->ready_terrain_move_mask & bit) &&
                     scaled_hp >= 75u * scaled_max)
                support_score = 2200; /* lower priority than useful attacks */
            else if ((observation->ready_self_guard_move_mask & bit) &&
                     scaled_hp >= 25u * scaled_max &&
                     scaled_hp <= 65u * scaled_max)
                support_score = 2900; /* confirmed worthwhile, never consecutive */
            if (!support_score) continue;
            SG_Proposal p = {0};
            p.battle_token = view->battle_token;
            p.turn_token = view->turn_token;
            p.choice_token = view->choice_token;
            p.actor = view->actor;
            p.action = SG_USE_MOVE;
            p.move_slot = (uint8_t)m;
            p.target = view->actor;
            if (!sg_validate(view, &p)) continue;
            SG_RankedChoice item = {p, support_score};
            sg_insert_ranked(ranked, &used, item);
        }
        /* 16060: A player's OWN healing move may target a player-owned
         * friendly active in doubles. Positive adapter evidence must attest
         * live ownership AND <=40% own-ally HP, plus this move's beneficial
         * effect. Never command the ally or select an NPC partner. */
        if (view->battler_count == 4u) {
            for (unsigned m = 0u; m < 4u; ++m) {
                if (!(observation->known_owned_ally_heal_move_mask & (1u << m)))
                    continue;
                for (unsigned t = 0u; t < view->battler_count; ++t) {
                    if (!(observation->ready_owned_ally_heal_target_mask & (1u << t)) ||
                        !(observation->verified_player_owned_ally_mask & (1u << t)) ||
                        observation->active[t].role != SG_PUBLIC_ALLY)
                        continue;
                    SG_Proposal p = {0};
                    p.battle_token = view->battle_token;
                    p.turn_token = view->turn_token;
                    p.choice_token = view->choice_token;
                    p.actor = view->actor;
                    p.action = SG_USE_MOVE;
                    p.move_slot = (uint8_t)m;
                    p.target = (uint8_t)t;
                    if (!sg_validate(view, &p)) continue;
                    SG_RankedChoice item = {p, 450000};
                    sg_insert_ranked(ranked, &used, item);
                }
            }
        }
        /* Opponent-side field hazards require positive live evidence that
         * their specific effect can gain a layer. The action is deferred
         * to the engine's legal targeting: an own-side or ally-only legal
         * mask cannot be reinterpreted as an opposing-side effect. */
        if (scaled_hp >= 65u * scaled_max) {
            for (unsigned m=0u; m<4u; ++m) {
                const unsigned bit=1u << m;
                if (!(observation->ready_foe_hazard_move_mask & bit)) continue;
                if (view->battler_count == 4u &&
                    !(observation->known_partner_safe_move_mask & bit)) continue;
                for (unsigned t=0u; t<view->battler_count; ++t) {
                    if (observation->active[t].role != SG_PUBLIC_FOE) continue;
                    SG_Proposal p={0};
                    p.battle_token=view->battle_token;
                    p.turn_token=view->turn_token;
                    p.choice_token=view->choice_token;
                    p.actor=view->actor;
                    p.action=SG_USE_MOVE;
                    p.move_slot=(uint8_t)m;
                    p.target=(uint8_t)t;
                    if (!sg_validate(view, &p)) continue;
                    const SG_PublicMove *move=&observation->moves[m];
                    const int32_t accuracy=move->known_always_hits ? 100 :
                                            (int32_t)move->displayed_accuracy;
                    SG_RankedChoice item={p, (3100 * accuracy) / 100};
                    sg_insert_ranked(ranked, &used, item);
                }
            }
        }
        /* Leech/seed needs a separate positive per-target public proof.
         * Missing native mechanics, type immunity, prior seeded state or
         * a foe-target legal mask -> no proposal. Never query hidden data. */
        if (scaled_hp >= 55u * scaled_max) {
            for (unsigned m = 0u; m < 4u; ++m) {
                const unsigned bit = 1u << m;
                if (!(observation->known_foe_leech_move_mask & bit)) continue;
                if (view->battler_count == 4u &&
                    !(observation->known_partner_safe_move_mask & bit)) continue;
                const SG_PublicMove *move = &observation->moves[m];
                const int32_t accuracy = move->known_always_hits ? 100 :
                                         (int32_t)move->displayed_accuracy;
                for (unsigned t = 0u; t < view->battler_count; ++t) {
                    if (!(observation->ready_foe_leech_target_mask & (1u << t)) ||
                        observation->active[t].role != SG_PUBLIC_FOE ||
                        (observation->active[t].visible_hp_band != SG_HP_BAR_MID &&
                         observation->active[t].visible_hp_band != SG_HP_BAR_HIGH))
                        continue;
                    SG_Proposal p = {0};
                    p.battle_token = view->battle_token;
                    p.turn_token = view->turn_token;
                    p.choice_token = view->choice_token;
                    p.actor = view->actor;
                    p.action = SG_USE_MOVE;
                    p.move_slot = (uint8_t)m;
                    p.target = (uint8_t)t;
                    if (!sg_validate(view, &p)) continue;
                    SG_RankedChoice item = {p, (3500 * accuracy) / 100};
                    sg_insert_ranked(ranked, &used, item);
                }
            }
        }
        /* Target an explicitly healthy, publicly observed FOE only. A
         * nonvolatile condition already present is not worth reapplying.
         * With the player below half HP, prefer recovery/attacks rather
         * than committing a low-impact status turn. */
        if (scaled_hp >= 50u * scaled_max) {
            for (unsigned m = 0u; m < 4u; ++m) {
                const unsigned bit = 1u << m;
                if (!(observation->known_foe_status_move_mask & bit)) continue;
                if (view->battler_count == 4u &&
                    !(observation->known_partner_safe_move_mask & bit)) continue;
                const SG_PublicMove *move = &observation->moves[m];
                const int32_t accuracy = move->known_always_hits ? 100 :
                                         (int32_t)move->displayed_accuracy;
                const int32_t score = (7000 * accuracy) / 100 +
                                      (int32_t)move->known_priority * 150;
                for (unsigned t = 0u; t < view->battler_count; ++t) {
                    if (observation->active[t].role != SG_PUBLIC_FOE ||
                        !(observation->public_foe_healthy_mask & (1u << t)) ||
                        (observation->active[t].visible_hp_band != SG_HP_BAR_MID &&
                         observation->active[t].visible_hp_band != SG_HP_BAR_HIGH))
                        continue;
                    SG_Proposal p = {0};
                    p.battle_token = view->battle_token;
                    p.turn_token = view->turn_token;
                    p.choice_token = view->choice_token;
                    p.actor = view->actor;
                    p.action = SG_USE_MOVE;
                    p.move_slot = (uint8_t)m;
                    p.target = (uint8_t)t;
                    if (!sg_validate(view, &p)) continue;
                    SG_RankedChoice item = {p, score};
                    sg_insert_ranked(ranked, &used, item);
                }
            }
        }
    }
    for (size_t i = 0u; i < used; ++i) out[i] = ranked[i].proposal;
    return used;
}

/* Fast diagnostic projection of the existing damage-only ranking.
 * Same observation validator, proposal gate, score helper and stable tie order.
 * The shared observation validator requires verified_owned_ally_context_mask
 * and verified_last_field_turn_attack_mask (and other support fields) to be zero
 * when support tactics is off; their urgency bonuses cannot apply here.
 * No full-list sorting or workspace. Tactical/type modes use the full API.
 */
size_t sg_rank_damage_best(const SG_View *v,
                          const SG_PublicBattleObservation *o,SG_Proposal *out)
{
    if (!v || !o || !out || !sg_workspace_observation_valid(v,o) ||
        o->use_public_support_tactics || o->use_public_type_heuristic ||
        o->use_engine_type_effect_heuristic)
        return 0;
    if (sg_workspace_overlap((uintptr_t)out,sizeof(*out),(uintptr_t)v,sizeof(*v)) ||
        sg_workspace_overlap((uintptr_t)out,sizeof(*out),(uintptr_t)o,sizeof(*o)))
        return 0;
    size_t count=0;
    int32_t best_score=0;
    SG_Proposal best={0};
    for(unsigned m=0;m<4;m++) {
        if(!o->moves[m].known_damaging_move ||
           (o->known_self_ko_move_mask & (1u<<m)) ||
           (o->require_non_self_ko_proof && !(o->known_non_self_ko_move_mask & (1u<<m))))
            continue;
        if(v->battler_count==4 &&
           ((o->known_ally_hit_move_mask & (1u<<m)) ||
            (o->require_partner_safe_proof && !(o->known_partner_safe_move_mask & (1u<<m)))))
            continue;
        for(unsigned t=0;t<v->battler_count;t++) {
            if(o->active[t].role!=SG_PUBLIC_FOE)continue;
            SG_Proposal p={0};
            p.battle_token=v->battle_token;p.turn_token=v->turn_token;
            p.choice_token=v->choice_token;p.actor=v->actor;
            p.action=SG_USE_MOVE;p.move_slot=m;p.target=t;
            if(!sg_validate(v,&p))continue;
            int32_t score=sg_move_score(&o->moves[m],&o->active[t],4);
            if(!count || score>best_score) {best=p;best_score=score;}
            count++;
        }
    }
    if(count)*out=best;
    return count;
}
