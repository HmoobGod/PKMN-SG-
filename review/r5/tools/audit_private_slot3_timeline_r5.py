#!/usr/bin/env python3
"""Private host/offline only. Summarize real R4-authenticated move-slot writes.

Do not ship private CPU event files, PP snapshots or ROM data with this program.
This audit observes store provenance, not original legality/selection scoring.
"""
import argparse
import json
from pathlib import Path
from audit_private_original_cursor_writer import audit


def evaluate(rows):
    report=audit(rows,rom_ok=True)
    # A same-address store is not credible if the pointer or an intervening
    # slot/target value changed without a corresponding observed CPU store.
    ptr=0; slot=target=None; last_frame=-1
    for row in rows:
        kind=row.get('event')
        if kind not in ('cursor_store','cursor_sample_change'):
            continue
        frame=row.get('f')
        if type(frame) is not int or frame<last_frame:
            raise ValueError('nonmonotonic live original CPU and sample timeline')
        last_frame=frame
        if kind=='cursor_sample_change':
            expected=(f'0x{ptr:08x}', slot, target)
            observed=(row.get('ptr'),row.get('slot'),row.get('target'))
            if expected!=observed:
                raise ValueError('sample drift from observed original CPU writes')
            continue
        ckind=row['kind']
        before=(row['slot_before'],row['target_before'])
        after=(row['slot_after'],row['target_after'])
        if ckind=='pointer':
            after_ptr=int(row['ptr_after'],16)
            if ptr==0 and after_ptr!=0:
                if before!=(-1,-1):
                    raise ValueError('bad init cursor state')
                ptr=after_ptr;slot,target=after
            elif ptr!=0 and after_ptr==0:
                if before!=(slot,target) or after!=(-1,-1):
                    raise ValueError('bad clear cursor state')
                ptr=0;slot=target=None
            else:
                raise ValueError('unexpected pointer ownership transition')
            continue
        if ptr==0 or before!=(slot,target):
            raise ValueError('unattributed drift between original CPU stores')
        slot,target=after
    if ptr!=0:
        raise ValueError('incomplete pointer lifecycle')
    store=[r for r in rows if r.get('event')=='cursor_store' and r.get('kind')=='slot']
    selected=[r['slot_after'] for r in store]
    return {
        'schema':'sg-private-slot3-selector-r5-unverified',
        'original_player0_slot_writes':len(selected),
        'slot3_direct_cpu_writes':selected.count(3),
        'consecutive_slot3_cpu_writes':sum(a==3 and b==3 for a,b in zip(selected,selected[1:])),
        'slot3_then_different_slot':sum(a==3 and b!=3 for a,b in zip(selected,selected[1:])),
        'observed_written_slots':selected,
        'full_underlying_pointer_and_opcode_audit_passed':report['private_cpu_store_rows_schema_and_source_valid'],
        'taunt_repetition_cause_certified':False,
        'dynamic_move_target_legality_certified':False,
        'original_manual_fallback_certified':False,
        'no_forced_switch_certified':False,
        'formal_native_acceptance':0,
        'production_authorized':False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-cursor-log',required=True,type=Path)
    args=p.parse_args()
    rows=[json.loads(x) for x in args.private_cursor_log.read_text().splitlines()]
    print(json.dumps(evaluate(rows),sort_keys=True,indent=2))
if __name__=='__main__':main()
