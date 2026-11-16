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


def from_r5_authenticated_cursor_trace(original_rows, r5_report, battle_epoch):
    """Adapt *already R5-audited* exact-ROM cursor_store rows, not arbitrary samples.

    The caller must first invoke R5 audit_private_slot3_timeline_r5.evaluate()
    on the identical raw rows; no authentication is created by this reducer.
    The R5 adapter only counts CPU slot stores, not UI cursor samples.
    """
    if (type(original_rows) is not list or type(r5_report) is not dict
            or type(battle_epoch) is not int or battle_epoch<=0):
        raise ValueError('invalid audited R5 input')
    if (r5_report.get('full_underlying_pointer_and_opcode_audit_passed') is not True
            or type(r5_report.get('original_player0_slot_writes')) is not int
            or type(r5_report.get('observed_written_slots')) is not list
            or r5_report.get('formal_native_acceptance')!=0):
        raise ValueError('missing R5 provenance report')
    original_slots=[];out=[]
    for row in original_rows:
        if type(row) is not dict:raise ValueError('bad R5 row')
        if row.get('event')!='cursor_store' or row.get('kind')!='slot':continue
        if type(row.get('f')) is not int or type(row.get('slot_after')) is not int:
            raise ValueError('untyped R5 cursor store')
        if row.get('pc')!='0x0801862e':raise ValueError('wrong original slot writer PC')
        slot=row['slot_after']
        original_slots.append(slot)
        out.append({'event':'slot_cpu_store','frame':row['f'],
                    'battle_epoch':battle_epoch,'slot':slot,'pc':row['pc'],'owner':0})
    if (len(out)!=r5_report['original_player0_slot_writes']
            or original_slots!=r5_report['observed_written_slots']):
        raise ValueError('unmatched R5 writer count/slots')
    # Empty traces never prove automatic move behavior.
    if not out:raise ValueError('no source-verified slot stores')
    evaluate(out,provenance_passed=True)
    return out
