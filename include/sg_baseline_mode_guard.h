#ifndef SG_BASELINE_MODE_GUARD_H
#define SG_BASELINE_MODE_GUARD_H
#include <stdbool.h>
#include <stdint.h>
/* Supplied baseline constants ONLY. Do not treat this as an authoritative
 * experimental-15970 mode map. Nonstandard modes fail closed. */
#define SG_BASELINE_BATTLE_DOUBLE (UINT32_C(1) << 0)
#define SG_BASELINE_BATTLE_MASTER (UINT32_C(1) << 2)
#define SG_BASELINE_BATTLE_TRAINER (UINT32_C(1) << 3)
#define SG_BASELINE_NORMAL_MASK (SG_BASELINE_BATTLE_DOUBLE | SG_BASELINE_BATTLE_MASTER | SG_BASELINE_BATTLE_TRAINER)
/* Defense in depth: engine-owned supported_mode must ALSO be true. */
bool sg_baseline_normal_mode(uint32_t mode_flags);
#endif
