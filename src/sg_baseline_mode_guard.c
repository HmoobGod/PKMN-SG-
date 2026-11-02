#include "sg_baseline_mode_guard.h"
bool sg_baseline_normal_mode(uint32_t mode_flags)
{
    /* Reject special/unknown flags, even if a caller erroneously sets the
     * supported_mode allowlist boolean. This deliberately excludes partner,
     * multi, link, recorded, safari, tutorial, Frontier, etc. */
    return (mode_flags & ~SG_BASELINE_NORMAL_MASK) == 0;
}
