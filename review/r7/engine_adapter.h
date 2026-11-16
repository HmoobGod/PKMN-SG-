#ifndef SG_R7_ENGINE_ADAPTER_H
#define SG_R7_ENGINE_ADAPTER_H
/* Source-only adapter contract. NEVER issues a game command or writes guest RAM.
 * All callbacks are future engine-integration requirements, NOT native evidence. */
#include <stdint.h>
#include "../r5/source-first/player0_fail_closed_guard.h"

/* BtlController_EmitChooseMove: 4-byte header + sizeof(ChooseMoveStruct).
 * A source-side working hypothesis (36-byte struct) pending exact-ROM ABI
 * authentication; NEVER claim native evidence from this constant alone. */
#define R7_CHOOSEMOVE_TOTAL_BYTES 40u
#define R7_PAYLOAD_CAP R7_CHOOSEMOVE_TOTAL_BYTES
#define R7_NO_ACTION UINT32_MAX
#define R7_NO_SLOT UINT32_MAX

typedef struct {
  uint32_t original_epoch, request_id, command, battler;
  uint32_t owner_party, foe_party, turn, resources, flags;
  uint8_t player_owned, wild_single, doubles, partner, auto_enabled, foe_live;
  uint8_t original_header[4];
  uint8_t original_payload[R7_PAYLOAD_CAP];
  uint8_t payload_length;
  uint16_t moves[4];
  uint8_t pp[4];
} R7Original;

typedef struct {
  uint32_t original_epoch, request_id, turn;
  uint8_t move_limitations_verified, target_helpers_verified, ineffectiveness_verified;
  uint8_t move_legal_mask, verified_foe_target_mask, known_ineffective_mask;
  uint8_t priorities[4];
} R7Legal;

typedef struct {
  uint32_t epoch, request_id;
  uint8_t consumed;
} R7Lease;

typedef struct {
  uint32_t epoch, turn, owner_party, foe_party;
  uint16_t planned_move;
  uint8_t slot, pending;
} R7FightTicket;

typedef struct {
  void *ctx;
  /* Return 1 only with complete, unmodified original engine buffers.
   * A host that fabricates snapshots cannot earn native certification here. */
  int (*read_original)(void *ctx, R7Original *out);
  /* Must invoke original move limitations / target helpers for the pinned request. */
  int (*read_engine_legality)(void *ctx, const R7Original *pinned, R7Legal *out);
} R7Host;

typedef enum { R7_DEFER=0, R7_FIGHT=1, R7_MOVE=2 } R7Outcome;
typedef enum {
  R7_REASON_NONE=0, R7_BAD_API, R7_BAD_ENGINE_READ, R7_UNSUPPORTED_SCOPE,
  R7_BAD_LEASE, R7_NO_ENGINE_LEGALITY, R7_ORIGINAL_REQUEST_CHANGED,
  R7_NO_VALID_MOVE, R7_STAGE_CONTINUITY_FAILED
} R7Reason;
typedef struct {
  R7Outcome outcome;
  R7Reason reason;
  uint32_t action, slot;
  uint8_t manual_defer_requested;
  uint8_t native_move_accepted, native_manual_fallback_accepted;
  uint8_t no_forced_switch_certified, production_authorized;
} R7Plan;

/* The bridge never calls BtlController_EmitTwoReturnValues or an original menu.
 * A native installer must separately verify the real request, route manual
 * deferral to the ORIGINAL controllable menu, and prove no auto Switch path. */
R7Plan r7_plan(const R7Host *host, R7Lease *lease, R7FightTicket *ticket);
#endif
