"""Fail-closed response authorization; applies only to proposed player0 auto actions."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Proposal:
 battler:int
 action:int
 command:int
 engine_request_verified:bool
 lease_live:bool
 owner_is_player:bool
 wild_single:bool

def allow(p):
 if not isinstance(p,Proposal):return False
 if any(type(getattr(p,k)) is not bool for k in ('engine_request_verified','lease_live','owner_is_player','wild_single')):return False
 if any(type(getattr(p,k)) is not int for k in ('battler','action','command')):return False
 return bool(p.battler==0 and p.engine_request_verified and p.lease_live and p.owner_is_player and p.wild_single and ((p.command==17 and p.action==0) or (p.command==19 and p.action==10)))
NATIVE_SWITCH_SAFETY_CERTIFIED=False
