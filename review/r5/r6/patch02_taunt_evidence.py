"""Taunt redundancy gate. Repetition is not positive ineffectiveness evidence."""
from dataclasses import dataclass
from enum import Enum
class Decision(Enum):
 UNKNOWN='unknown_defer'
 BENEFICIAL='not_proven_redundant'
 REDUNDANT='verified_redundant'

@dataclass(frozen=True)
class TauntEvidence:
 player0: bool
 wild_single: bool
 original_target: int
 live_target: int
 selected_move: int
 taunt_move_id: int
 engine_status_checked: bool
 target_has_active_taunt: bool
 status_epoch_before: int
 status_epoch_after: int
 target_alive: bool


def classify(e):
 if not isinstance(e,TauntEvidence):return Decision.UNKNOWN
 if not all(type(getattr(e,k)) is bool for k in ('player0','wild_single','engine_status_checked','target_has_active_taunt','target_alive')):return Decision.UNKNOWN
 if not e.player0 or not e.wild_single or not e.target_alive or not e.engine_status_checked:return Decision.UNKNOWN
 for k in ('original_target','live_target','selected_move','taunt_move_id','status_epoch_before','status_epoch_after'):
  v=getattr(e,k)
  if type(v) is not int or v<0 or v>0xffffffff:return Decision.UNKNOWN
 if e.original_target!=e.live_target or not e.status_epoch_before or e.status_epoch_before!=e.status_epoch_after:return Decision.UNKNOWN
 if not e.taunt_move_id or not e.selected_move:return Decision.UNKNOWN
 if e.selected_move==e.taunt_move_id and e.target_has_active_taunt:return Decision.REDUNDANT
 return Decision.BENEFICIAL
NATIVE_CERTIFIED=False
