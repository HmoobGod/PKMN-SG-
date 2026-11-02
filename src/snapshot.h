#ifndef SG_DIAGNOSTIC_SNAPSHOT_H
#define SG_DIAGNOSTIC_SNAPSHOT_H
#include <stdint.h>
/* Diagnostic observation only. Success is NOT action/owner authorization.
   Caller supplies aligned, writable output storage. No game hook installed. */
struct sg_diagnostic_snapshot {
 uint32_t actor,count,kind,completion,run,slot,position,permission_state;
 uint16_t moves[4],buffer_moves[4];
 uint8_t pp[4];
 /* Native own-battler +0x6C bits11..20. This is a negative restriction,
    never complete permission. Native nonzero-ID equality is the predicate. */
 uint16_t disabled_move;
 uint16_t reserved;
 uint32_t battle_type_flags;
 /* Public participation only; excludes native skipped/absent battlers.
    Not target legality and never reads hidden foe HP or moves. */
 uint32_t present_mask;
 /* Own native Encore fields: negative move restriction only. */
 uint16_t encored_move;
 uint8_t encore_timer,reserved2;
 /* Native own repeat-move exclusion, not complete permission. */
 uint16_t last_move;
 uint8_t repeat_blocked,reserved3;
 uint32_t native_restricted_mask;
};
_Static_assert(sizeof(struct sg_diagnostic_snapshot)==76,"snapshot layout");
/* 0 success; 1 actor outside sampled scope; 2 count; 3 EWRAM pointers;4 null output;5 observed controller class excluded;6 unsupported diagnostic context;7 no pending move-choice request. */
uint32_t sg_capture_diagnostic(uint32_t actor,struct sg_diagnostic_snapshot *out);
#endif
