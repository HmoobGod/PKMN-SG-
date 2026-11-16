"""Source-only manual controller handoff model.

Does not call a ROM function. A defer signal alone is not a functioning UI.
"""
from dataclasses import dataclass
from enum import Enum
class State(Enum):
 AUTO='auto_candidate'
 DEFER='defer_requested'
 WAIT='await_original_menu'
 OPEN='original_menu_confirmed'
 HUMAN='human_input_confirmed'
 CLOSED='completed'
 ERROR='fail_closed'
@dataclass(frozen=True)
class Handoff:
 state:State=State.AUTO
 epoch:int=0
 owner:int=0
 native_accepted:bool=False

def advance(h,event,epoch,owner=0):
 if not isinstance(h,Handoff) or type(epoch) is not int or epoch<=0 or type(owner) is not int or owner!=0:return Handoff(State.ERROR)
 if h.state==State.ERROR:return h
 if h.state!=State.AUTO and (epoch!=h.epoch or owner!=h.owner):return Handoff(State.ERROR)
 next_state={
  (State.AUTO,'ineligible'):State.DEFER,
  (State.DEFER,'original_manual_requested'):State.WAIT,
  (State.WAIT,'original_menu_visible_and_controllable'):State.OPEN,
  (State.OPEN,'physical_human_input_confirmed'):State.HUMAN,
  (State.HUMAN,'original_engine_completed'):State.CLOSED,
 }.get((h.state,event),State.ERROR)
 return Handoff(next_state,epoch,owner,False)
