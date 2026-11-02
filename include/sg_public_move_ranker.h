#ifndef SG_PUBLIC_MOVE_RANKER_H
#define SG_PUBLIC_MOVE_RANKER_H
#include "sg_action_gate.h"
#include "sg_public_types.h"
#include <stddef.h>

/* Source-only, public-information heuristic. No engine wiring or ROM patch.
 * A trusted native adapter must derive these observations from the PLAYER'S
 * known moves and actually visible active-battler information, never from
 * the opposing party, private abilities/items, exact hidden HP, or AI data.
 * In particular, legality is provided separately by the engine-owned SG_View.
 */
#define SG_PUBLIC_MAX_CHOICES 16u

typedef enum {
    SG_PUBLIC_UNKNOWN = 0,
    SG_PUBLIC_SELF = 1,
    SG_PUBLIC_ALLY = 2,
    SG_PUBLIC_FOE = 3
} SG_PublicRole;

typedef enum {
    SG_HP_BAR_UNOBSERVED = 0,
    SG_HP_BAR_CRITICAL = 1, /* UI-visible coarse estimate only */
    SG_HP_BAR_LOW = 2,
    SG_HP_BAR_MID = 3,
    SG_HP_BAR_HIGH = 4
} SG_PublicHpBand;

typedef struct {
    bool known_damaging_move; /* false for unknown or status-only moves */
    uint16_t displayed_base_power; /* own known move; 1..999, not a damage prediction */
    uint8_t displayed_accuracy;   /* 1..100; 0 only with known_always_hits */
    bool known_always_hits;
    int8_t known_priority;        /* own move metadata, -7..+7 */
} SG_PublicMove;

typedef struct {
    /* Source-only ABI: keep bounded public enum values in a byte each.
     * The host adapter MUST compile against this exact source header;
     * there is no preexisting native ROM ABI or save serialization here.
     * Compact active-battler observations also bound ARM locked stack use. */
    uint8_t role; /* SG_PublicRole: positive visible active-side identity */
    uint8_t visible_hp_band; /* SG_PublicHpBand; UNKNOWN is safe */
} SG_PublicBattler;

typedef struct {
    uint32_t battle_token, turn_token, choice_token;
    uint8_t actor;
    /* Own known move targeting only. A bit means this move is publicly
     * known to hit a friendly PARTNER as well as a selected opponent, e.g.
     * an ally-hitting spread move in doubles. Do not infer this from the
     * opponent's secret state or an engine single-target legality mask.
     * Zero is backwards-compatible UNKNOWN, not proof of no friendly fire;
     * the native adapter must deliberately populate it before relying on
     * this protection. Bits 4..7 are invalid. */
    uint8_t known_ally_hit_move_mask;
    /* Optional stricter doubles policy for a future trusted native adapter.
     * A bit in known_partner_safe_move_mask is POSITIVE evidence from the
     * PLAYER'S OWN MOVE TARGETING DATA that selecting a foe cannot hit the
     * friendly partner. Zero means unclassified, NOT safe. When strict is
     * true in doubles, only proven-safe moves may be automatically chosen;
     * incomplete metadata causes a no-action/manual fallback, never a guess.
     * A move cannot be simultaneously marked safe and partner-hitting.
     * Legacy callers remain non-strict until native provenance is audited. */
    uint8_t known_partner_safe_move_mask;
    /* Own-known move metadata: a bit identifies a move that explicitly
     * KOs its USER on execution (e.g. Self-Destruct/Explosion/Memento).
     * This is distinct from recoil, low-HP moves or an ally-hitting spread
     * move. Exclude these from both singles and doubles automatic choices.
     * The engine adapter must derive it from the player's known move data,
     * NOT hidden opponent information. Zero is UNKNOWN, not an attestation
     * that every move is safe. Bits 4..7 are invalid. */
    uint8_t known_self_ko_move_mask;
    /* Positive classification from the PLAYER'S OWN MOVE DATA that this
     * slot does NOT KO its user. Unknown is not a safety certification.
     * The two self-KO masks must be disjoint, and reserved bits invalid.
     * Native strict route must enable this proof for EVERY move phase,
     * including singles. This never draws from opponent information. */
    uint8_t known_non_self_ko_move_mask;
    bool require_non_self_ko_proof : 1;
    bool require_partner_safe_proof : 1;
    /* Opt-in own-Pokemon support tactics. All positive bits classify the
     * PLAYER'S OWN non-damaging move ID, not an opponent's moves or intent.
     * A heal is considered only at <= 40% own HP; a self setup only when
     * own HP >= 70% and the native adapter positively attests that at least
     * one of its own affected stat stages can still be usefully raised.
     * Unclassified moves remain under the legacy fallback policy. */
    bool use_public_support_tactics : 1;
    uint8_t known_self_heal_move_mask;
    uint8_t known_self_setup_move_mask;
    uint8_t ready_self_setup_move_mask;
    /* Opt-in own-side defensive screen. Classification is bound to the
     * player's current known move, NOT an arbitrary non-damaging effect.
     * Ready only with positive live native proof that the associated screen
     * is not already active and its defensive effect can benefit this side.
     * A future adapter must validate that targeting SELF selects own side.
     * Cannot screen-spam once native readiness becomes false. */
    uint8_t known_own_screen_move_mask;
    uint8_t ready_own_screen_move_mask;
    /* Positive owner-move classification for an entry hazard applied to the
     * opponent's side. A ready bit is permitted only after verified live
     * evidence this particular hazard still has an unsaturated layer slot;
     * UNKNOWN must be false. No hidden opponent reserve information used. */
    uint8_t known_foe_hazard_move_mask;
    uint8_t ready_foe_hazard_move_mask;
    /* WEATHER / TERRAIN are opt-in, ID-bound PLAYER-owned field tactics.
     * Positive readiness MUST attest (a) the specific desired field effect
     * is not already operating, (b) it actually benefits the player's own
     * active side, and (c) the field can lawfully be established now using
     * the player's present move. Unknown duration, effect or modded rules
     * must leave readiness false. Weather and terrain use distinct masks;
     * no opposing secrets, engine type guesswork or native effect IDs here.
     * Only SELF target proposals are made; the engine must attest that SELF
     * legally selects that field-setting move. */
    uint8_t known_weather_move_mask;
    uint8_t ready_weather_move_mask;
    uint8_t known_terrain_move_mask;
    uint8_t ready_terrain_move_mask;
    /* Own protect-style single-turn guard: native readiness MUST certify
     * that this specific move is not repeated after the actor's prior use,
     * has a positive present tactical payoff, and protects only the player
     * (not an ally or foe). Unknown history, mechanics or usefulness = false.
     * This is NOT a promise of immunity versus unknown enemy abilities. */
    uint8_t known_self_guard_move_mask;
    uint8_t ready_self_guard_move_mask;
    /* Opponent-side leech/seed effect: native adaptation MUST attest both
     * the exact current move identity AND the publicly observed foe is
     * unseeded, currently seedable under known type/rule constraints, and
     * that no uncertain history/side effect is being assumed. The ready
     * target bit represents a currently VERIFIED legal FOE, not hidden
     * party state. The two masks are independently live-recaptured. */
    uint8_t known_foe_leech_move_mask;
    uint8_t ready_foe_leech_target_mask;
    /* 16060: Only a PLAYER-OWNED active ally can receive a healing move.
     * These independent role/ownership and currently-needed recovery proofs
     * are provided by a trusted adapter using the player's own ally HP and
     * party ownership, not by inspecting NPC-party controller state. A zero
     * bit means UNKNOWN/NOT READY. Target must remain engine-legal and the
     * player must be the controller of the ACTING Pokemon. No party-side
     * switching or native Ally Action is synthesized here. */
    uint8_t known_owned_ally_heal_move_mask;
    uint8_t verified_player_owned_ally_mask;
    uint8_t ready_owned_ally_heal_target_mask;
    /* 16070: Separate opt-in doubles context, never inferred from an NPC
     * partner merely occupying the ally slot. A trusted native adapter must
     * positively attest that the visible low-HP ally is owned by the SAME
     * player. A single position bit enables a bounded urgency tie-bias for
     * a low-HP public foe; it does not select or command that ally, predict
     * enemy turns, or assume exact damage. Zero disables this scoring. */
    uint8_t verified_owned_ally_context_mask;
    /* 16072: Opt-in, last-live-turn FAVORABLE FIELD attack timing. A trusted
     * native adapter must verify that the exact active weather/terrain effect
     * has precisely one usable action turn remaining, and that each marked
     * PLAYER-owned attack specifically benefits from that effect under
     * current game rules. It is NOT based on a fixed Gen-IV duration guess.
     * Never infer opponent intent, partner control or hidden attributes.
     * Missing provenance => zero; locked recapture must match this mask. */
    uint8_t verified_last_field_turn_attack_mask;
    /* Publicly observed, nonvolatile status only. Foe status proposals are
     * permitted ONLY when visibility attests the foe is currently healthy.
     * No inference from a hidden party, ability, item or exact damage.
     * PLAYER move metadata must positively classify the move as foe-status. */
    uint8_t known_foe_status_move_mask;
    uint8_t public_foe_condition_known_mask;
    uint8_t public_foe_healthy_mask;
    uint16_t own_current_hp, own_max_hp;
    SG_PublicMove moves[4];
    SG_PublicBattler active[4];
    /* Optional per-slot identity proof from the PLAYER'S four owned moves.
     * IDs are opaque NONZERO engine move IDs; zero means empty/unresolved.
     * The classifier must echo the IDs it actually classified, not merely
     * attach mask bits by slot. A locked recapture must reproduce both
     * arrays. Never derive IDs from an opponent's moves. */
    uint16_t owned_move_identity[4];
    uint16_t classified_move_identity[4];
    bool require_owned_move_identity_proof;
    /* Optional PUBLIC Gen-IV type heuristic. Zero/disabled is the historic
     * behavior and never reads hidden opponent data. The native adapter
     * must independently verify its own move types and the opponents' FULL
     * PUBLIC species/form typing against the experimental game's type chart.
     * Unknown/uncertain typing must remain zero and score neutrally.
     * Bits in public_foe_type_mask attest full typing for explicit FOE roles;
     * fields for allies/self/absent battlers MUST stay zero. */
    bool use_public_type_heuristic;
    bool type_heuristic_bound; /* bound to the verified player move IDs */
    uint8_t owned_move_type[4];
    uint8_t public_foe_type_mask;
    uint8_t foe_type1[4], foe_type2[4];
    /* Alternative to the fixed Gen-IV chart, for mods with different type
     * tables (e.g., Fairy, Stellar or configurable Steel resistances).
     * The future native adapter MUST calculate these multipliers from the
     * exact game's VERIFIED type-only chart and publicly established FULL
     * foe typing, not hidden abilities/items or exact hidden HP. Values are
     * quarter-units: 0,1,2,4,8,16; absent matrix entries MUST be zero.
     * Masks identify positively classified PLAYER moves and public FOES.
     * This mode is mutually exclusive with the reference Gen-IV heuristic,
     * disabled by default and bound to exact player-owned move IDs. */
    bool use_engine_type_effect_heuristic;
    bool engine_type_effect_bound;
    uint8_t effect_known_move_mask, effect_public_foe_mask;
    uint8_t effect_quarters[4][4]; /* [own move slot][public active foe] */
} SG_PublicBattleObservation;

/* On any invalid or mismatched observation, returns zero WITHOUT changing
 * output. Candidate generation intentionally handles MOVE SELECTION ONLY;
 * action-menu, forced party, status, and native Struggle remain engine-owned.
 * Capacity >= 16 required to avoid partial ranked lists; output may not
 * overlap view or observation. The result is only a prioritized PROPOSAL;
 * each proposal is still subject to sg_validate and locked live recapture. */
bool sg_public_observation_valid(const SG_View *view,
    const SG_PublicBattleObservation *observation);
/* Conservative fallback: when no public damaging candidate is selectable,
 * select only a target explicitly identified as a FOE by the player-visible
 * observation. The engine legal mask must separately authorize the move and
 * target. Never emit a generic engine-mask fallback to SELF or ALLY.
 * The move could be a status move; its effects are not guessed. Returns
 * true only on a fully validated proposal and otherwise leaves out intact. */
bool sg_first_public_foe_mask_fallback(const SG_View *view,
    const SG_PublicBattleObservation *observation, SG_Proposal *out);

size_t sg_rank_public_damage(const SG_View *view,
    const SG_PublicBattleObservation *observation,
    SG_Proposal *out, size_t capacity);
#endif
