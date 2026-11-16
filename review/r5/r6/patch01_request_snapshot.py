"""Source-only owner/epoch snapshot validator; never reads guest memory itself.

The adapter must collect immutable bytes BEFORE and AFTER target helpers. No hash
can substitute for complete byte comparison. A positive result is not native proof.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Snapshot:
    battler: int
    command: int
    is_player_owned: bool
    is_wild_single: bool
    partner_present: bool
    turn: int
    owner_party: int
    foe_party: int
    resources: int
    controller_flags: int
    request_epoch: int
    action_header: bytes
    move_menu_payload: bytes
    consumed: bool = False


def eligible(before, after):
    if not isinstance(before,Snapshot) or not isinstance(after,Snapshot):return False
    a=before
    ints=(a.battler,a.command,a.turn,a.owner_party,a.foe_party,a.resources,a.controller_flags,a.request_epoch)
    if any(type(x) is not int or x<0 or x>0xffffffff for x in ints):return False
    if any(type(getattr(s,k)) is not bool for s in (before,after) for k in ('is_player_owned','is_wild_single','partner_present','consumed')):return False
    if a.battler!=0 or a.command not in (17,19) or not a.is_player_owned or not a.is_wild_single or a.partner_present:return False
    if not a.resources or not a.request_epoch or a.consumed or after.consumed:return False
    if type(a.action_header) is not bytes or len(a.action_header)!=4:return False
    if type(a.move_menu_payload) is not bytes or len(a.move_menu_payload)!=12:return False
    return a==after

NATIVE_CERTIFIED=False
PRODUCTION_AUTHORIZED=False
