"""Engine-backed legality adapter contract. No estimation from PP or type alone."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Move:
 move_id:int
 pp:int
 limitation_checked:bool
 limitation_mask_pass:bool
 target_checked:bool
 target_is_foe:bool
 current_turn_checked:bool

def eligible(move):
 if not isinstance(move,Move):return False
 if any(type(getattr(move,k)) is not bool for k in ('limitation_checked','limitation_mask_pass','target_checked','target_is_foe','current_turn_checked')):return False
 if type(move.move_id) is not int or not 1<=move.move_id<65535 or type(move.pp) is not int or not 1<=move.pp<=99:return False
 return all((move.limitation_checked,move.limitation_mask_pass,move.target_checked,move.target_is_foe,move.current_turn_checked))

def select(moves,priorities):
 if not isinstance(moves,(tuple,list)) or len(moves)!=4 or not isinstance(priorities,(tuple,list)) or len(priorities)!=4:return None
 if any(type(p) is not int or not 0<=p<=255 for p in priorities):return None
 legal=[i for i,x in enumerate(moves) if eligible(x)]
 if not legal:return None
 return max(legal,key=lambda i:(priorities[i],-i))
NATIVE_CERTIFIED=False
