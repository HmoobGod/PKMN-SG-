#include "sg_public_types.h"
#define T(x) (UINT32_C(1) << SG_TYPE_##x)
typedef struct { uint32_t strong, weak, immune; } SG_TypeRow;
/* Gen-IV chart deliberately retains Steel resistance to Ghost/Dark and
 * has no Fairy type. Indexed by our OWN stable semantic enums, never a
 * cast of engine-native type constants. */
static const SG_TypeRow chart[18] = {
    [SG_TYPE_NORMAL]   = {0, T(ROCK)|T(STEEL), T(GHOST)},
    [SG_TYPE_FIRE]     = {T(GRASS)|T(ICE)|T(BUG)|T(STEEL), T(FIRE)|T(WATER)|T(ROCK)|T(DRAGON), 0},
    [SG_TYPE_WATER]    = {T(FIRE)|T(GROUND)|T(ROCK), T(WATER)|T(GRASS)|T(DRAGON), 0},
    [SG_TYPE_ELECTRIC] = {T(WATER)|T(FLYING), T(ELECTRIC)|T(GRASS)|T(DRAGON), T(GROUND)},
    [SG_TYPE_GRASS]    = {T(WATER)|T(GROUND)|T(ROCK), T(FIRE)|T(GRASS)|T(POISON)|T(FLYING)|T(BUG)|T(DRAGON)|T(STEEL), 0},
    [SG_TYPE_ICE]      = {T(GRASS)|T(GROUND)|T(FLYING)|T(DRAGON), T(FIRE)|T(WATER)|T(ICE)|T(STEEL), 0},
    [SG_TYPE_FIGHTING] = {T(NORMAL)|T(ICE)|T(ROCK)|T(DARK)|T(STEEL), T(POISON)|T(FLYING)|T(PSYCHIC)|T(BUG), T(GHOST)},
    [SG_TYPE_POISON]   = {T(GRASS), T(POISON)|T(GROUND)|T(ROCK)|T(GHOST), T(STEEL)},
    [SG_TYPE_GROUND]   = {T(FIRE)|T(ELECTRIC)|T(POISON)|T(ROCK)|T(STEEL), T(GRASS)|T(BUG), T(FLYING)},
    [SG_TYPE_FLYING]   = {T(GRASS)|T(FIGHTING)|T(BUG), T(ELECTRIC)|T(ROCK)|T(STEEL), 0},
    [SG_TYPE_PSYCHIC]  = {T(FIGHTING)|T(POISON), T(PSYCHIC)|T(STEEL), T(DARK)},
    [SG_TYPE_BUG]      = {T(GRASS)|T(PSYCHIC)|T(DARK), T(FIRE)|T(FIGHTING)|T(POISON)|T(FLYING)|T(GHOST)|T(STEEL), 0},
    [SG_TYPE_ROCK]     = {T(FIRE)|T(ICE)|T(FLYING)|T(BUG), T(FIGHTING)|T(GROUND)|T(STEEL), 0},
    [SG_TYPE_GHOST]    = {T(PSYCHIC)|T(GHOST), T(DARK)|T(STEEL), T(NORMAL)},
    [SG_TYPE_DRAGON]   = {T(DRAGON), T(STEEL), 0},
    [SG_TYPE_DARK]     = {T(PSYCHIC)|T(GHOST), T(FIGHTING)|T(DARK)|T(STEEL), 0},
    [SG_TYPE_STEEL]    = {T(ICE)|T(ROCK), T(FIRE)|T(WATER)|T(ELECTRIC)|T(STEEL), 0}
};
#undef T
static int against_one(uint8_t attack, uint8_t defender)
{
    const uint32_t bit = UINT32_C(1) << defender;
    const SG_TypeRow *r = &chart[attack];
    if (r->immune & bit) return 0;
    if (r->strong & bit) return 8;
    if (r->weak & bit) return 2;
    return 4;
}
int sg_public_type_effect_quarters(uint8_t attack,
                                   uint8_t defense1, uint8_t defense2)
{
    if (!attack || attack > SG_PUBLIC_TYPE_MAX || !defense1 ||
        defense1 > SG_PUBLIC_TYPE_MAX || defense2 > SG_PUBLIC_TYPE_MAX ||
        defense1 == defense2) return -1;
    const int primary = against_one(attack, defense1);
    return defense2 ? (primary * against_one(attack, defense2)) / 4 : primary;
}
