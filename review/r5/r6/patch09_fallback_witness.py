"""Offline manual UI witness auditor. Synthetic positives never imply native acceptance."""
def inspect(rows):
 if type(rows) is not list or len(rows)>10000:raise ValueError('bounded rows required')
 required=('ineligible','defer','original_menu_visible','human_input','manual_response')
 seq=[];epoch=None;last_step=-1
 for r in rows:
  if type(r) is not dict:raise ValueError('invalid row')
  step=r.get('step');kind=r.get('event');owner=r.get('owner');e=r.get('epoch')
  if any(type(x) is not int for x in (step,owner,e)) or step<=last_step or owner!=0 or e<=0 or kind not in (*required,'auto_response','switch_response','enemy_event'):raise ValueError('invalid witness chronology')
  if epoch is None:epoch=e
  if e!=epoch:raise ValueError('epoch drift')
  last_step=step
  if kind in ('auto_response','switch_response'):return {'manual_fallback_candidate_UNVERIFIED':False,'native_accepted':0}
  if kind!='enemy_event':seq.append(kind)
 return {'manual_fallback_candidate_UNVERIFIED':tuple(seq)==required,'native_accepted':0,'manual_fallback_certified':False}
