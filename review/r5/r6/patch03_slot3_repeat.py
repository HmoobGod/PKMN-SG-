"""Pure trace reducer: caller MUST first run exact-ROM store provenance audit.

Do not interpret same-slot samples as repeat selector executions.
"""
def evaluate(rows,provenance_passed=False):
 if type(provenance_passed) is not bool or not provenance_passed:raise ValueError('original CPU provenance not verified')
 if type(rows) is not list or len(rows)>10000:raise ValueError('bounded trace required')
 by_epoch={};last_frame=-1
 for row in rows:
  if type(row) is not dict:raise ValueError('invalid row')
  if row.get('event')!='slot_cpu_store':raise ValueError('CPU writes only')
  frame=row.get('frame');epoch=row.get('battle_epoch');slot=row.get('slot');pc=row.get('pc');owner=row.get('owner')
  if any(type(x) is not int for x in (frame,epoch,slot,owner)) or frame<=last_frame or frame<0 or epoch<=0 or slot not in range(4) or owner!=0 or pc!='0x0801862e':raise ValueError('invalid source or sequence')
  last_frame=frame;by_epoch.setdefault(epoch,[]).append(slot)
 repeated=sum(a==b==3 for seq in by_epoch.values() for a,b in zip(seq,seq[1:]))
 return {'authenticated_consecutive_slot3_candidates':repeated,'taunt_ineffectiveness_verified':False,'native_accepted':0,'production_authorized':False}
