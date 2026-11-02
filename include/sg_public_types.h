#ifndef SG_PUBLIC_TYPES_H
#define SG_PUBLIC_TYPES_H
#include <stdint.h>
/* Reference GENERATION-IV 17-type table, NOT native engine enum values.
 * The adapter may opt into this only after independently checking that the
 * experimental game's type chart and the player's public typing agree.
 * Abilities, held items, field effects, immunities other than type and
 * opponent hidden state are intentionally NOT predicted here. */
typedef enum {
    SG_TYPE_UNKNOWN=0, SG_TYPE_NORMAL, SG_TYPE_FIRE, SG_TYPE_WATER,
    SG_TYPE_ELECTRIC, SG_TYPE_GRASS, SG_TYPE_ICE, SG_TYPE_FIGHTING,
    SG_TYPE_POISON, SG_TYPE_GROUND, SG_TYPE_FLYING, SG_TYPE_PSYCHIC,
    SG_TYPE_BUG, SG_TYPE_ROCK, SG_TYPE_GHOST, SG_TYPE_DRAGON,
    SG_TYPE_DARK, SG_TYPE_STEEL
} SG_PublicType;
#define SG_PUBLIC_TYPE_MAX ((uint8_t)SG_TYPE_STEEL)
/* Return quarter-scale multiplier: 0,1,2,4,8,16 for 0,1/4,1/2,1,2,4x.
 * Defending type2 UNKNOWN means a confirmed mono-type, not a guessed second
 * type. -1 for unsupported/unresolved attack or first defending type.
 * This must never be interpreted as actual damage or as engine legality. */
int sg_public_type_effect_quarters(uint8_t attack,
                                   uint8_t defense1, uint8_t defense2);
#endif
