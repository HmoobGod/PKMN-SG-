"""Offline normalized-event correlation, synthetic tests only.

Caller must first prove original opcode/address provenance and game-context
continuity. This function deliberately cannot certify actual PP execution.
"""
from dataclasses import dataclass
@dataclass(frozen=True)
class Event:
 step:int
 epoch:int
 owner:int
 kind:str
 slot:int
 before:int=0
 after:int=0
 proven_opcode:bool=False

def candidates(events):
 if type(events) is not list or not 1<=len(events)<=10000:raise ValueError('bounded normalized events required')
 prev=-1;groups={}
 for e in events:
  if not isinstance(e,Event) or any(type(x) is not int for x in (e.step,e.epoch,e.owner,e.slot,e.before,e.after)) or type(e.proven_opcode) is not bool:raise ValueError('invalid event types')
  if e.step<=prev or e.epoch<=0 or e.owner not in (0,1) or not 0<=e.slot<=3 or e.kind not in ('fight','move','pp','manual','switch','other'):raise ValueError('invalid event')
  prev=e.step;groups.setdefault(e.epoch,[]).append(e)
 found=[]
 for epoch,group in groups.items():
  player=[e for e in group if e.owner==0]
  if any(e.kind in ('manual','switch','other') for e in player):continue
  fight=[e for e in player if e.kind=='fight']
  move=[e for e in player if e.kind=='move']
  pp=[e for e in player if e.kind=='pp']
  if not (len(fight)==len(move)==len(pp)==1):continue
  f,m,p=fight[0],move[0],pp[0]
  if not (f.step<m.step<p.step and m.slot==p.slot and p.before==p.after+1 and p.before>0 and p.proven_opcode):continue
  found.append({'epoch':epoch,'slot':m.slot,'candidate_UNVERIFIED':True})
 return {'candidates':found,'native_accepted':0,'engine_request_owned_verified':False,'legality_verified':False,'manual_fallback_verified':False}
