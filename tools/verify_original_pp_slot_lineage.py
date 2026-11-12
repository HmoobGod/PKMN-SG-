#!/usr/bin/env python3
"""Read-only exact-ROM original CPU PP-slot construction audit.

Original PP write provenance only. Never certifies player-command ownership,
move/target legality, host-free auto battle, or matches unrelated PP fixtures.
"""
import argparse
import hashlib
import json
from pathlib import Path

EXACT = '4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44'
CURRENT = '7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32'
ORDER = ('0x809e69a', '0x809e69e', '0x809e6b0', '0x809e6b4', '0x809e6b8')
EMITTER, COPIER, POST_A, COMPLETE = '0x806bd80', '0x806b370', '0x806b3c6', '0x806261c'
COMMIT = {'0x8094330', '0x809435c', '0x8094374', '0x8094380'}


def hx(e, key):
    value = e.get(key)
    if not isinstance(value, str) or not value.startswith('0x'):
        raise ValueError('missing hexadecimal CPU register ' + key)
    return int(value, 16)


def verify(data, host_log, rom=None):
    if not isinstance(data, dict) or data.get('rom_sha256') != EXACT:
        raise ValueError('exact custom-ROM identity metadata absent')
    if rom is not None:
        digest = hashlib.sha256(Path(rom).read_bytes()).hexdigest()
        if digest == CURRENT:
            raise ValueError('refuse protected Current ROM')
        if digest != EXACT:
            raise ValueError('wrong native original ROM image')
    events = data.get('original_cpu_events')
    if not isinstance(events, list) or not events:
        raise ValueError('empty original CPU event sequence')
    if not isinstance(host_log, str) or 'HOST_DIAGNOSTIC_BATTLE_NARRATION_ACK_NOT_UNATTENDED' not in host_log:
        raise ValueError('missing explicit host diagnostic input disclosure')
    observed = {'original_actor0_emit_entries': 0,
                'original_actor0_copy_entries': 0,
                'original_copy_A_postloop_candidate_hits': 0,
                'original_actor0_completion_pc_hits': 0,
                'original_validator_commit_pc_hits': 0}
    ready, current, last_t, pairs = 0, [], -1, []
    for e in events:
        if not isinstance(e, dict) or not isinstance(e.get('pc'), str) or not isinstance(e.get('t'), (int,float)):
            raise ValueError('invalid raw CPU event schema')
        if e['t'] <= last_t:
            raise ValueError('non-monotonic same-process GDB chronology')
        last_t = e['t']
        pc = e['pc']
        if e.get('main') != 2:
            raise ValueError('CPU event outside active original battle flag')
        if pc == EMITTER and hx(e,'r0') == 0 and hx(e,'r2') == 10:
            observed['original_actor0_emit_entries'] += 1
        if pc == COPIER and hx(e,'r0') == 0 and hx(e,'r1') == 1 and hx(e,'r3') == 6:
            observed['original_actor0_copy_entries'] += 1
        if pc == POST_A:
            observed['original_copy_A_postloop_candidate_hits'] += 1
        if pc == COMPLETE and hx(e,'r0') == 0:
            observed['original_actor0_completion_pc_hits'] += 1
        if pc in COMMIT:
            observed['original_validator_commit_pc_hits'] += 1
        if pc not in ORDER:
            continue
        if pc == ORDER[0]:
            if current:
                raise ValueError('interleaved/unclosed PP instruction chain')
            current = [e]
            continue
        if not current or pc != ORDER[len(current)]:
            raise ValueError('PP instruction order or starting CPU witness missing')
        if hx(e, 'r0') != hx(current[0], 'r0') or hx(e,'sp') != hx(current[0],'sp'):
            raise ValueError('PP chain actor or stack identity changed')
        current.append(e)
        if pc != ORDER[-1]:
            continue
        a,b,c,d,store = current
        actor = hx(a,'r0')
        if actor not in (0,1):
            raise ValueError('actor out of single-wild controller scope')
        slot = c.get('stack_slot_word')
        old = a.get('old_pp_byte')
        cost = b.get('requested_decrement')
        new = c.get('stack_new_pp_word')
        if type(slot) is not int or not 0 <= slot < 4:
            raise ValueError('invalid original selected PP slot')
        if type(old) is not int or type(cost) is not int or type(new) is not int or not (0 <= old <= 255 and 1 <= cost <= 255 and 0 <= new <= 255):
            raise ValueError('invalid original PP operand types/range')
        if b.get('effective_pp_before') != old or new != max(0,old-cost):
            raise ValueError('original PP source/decrement calculation mismatch')
        expected = hx(d, 'r3') + slot + 0x25
        if expected != hx(a,'r3') or expected != int(store.get('candidate_pp_address','-1'),16) or expected != hx(store,'r1')+0x25:
            raise ValueError('original per-actor/slot PP address mismatch')
        if hx(d,'r7') != slot or d.get('stack_new_pp_word') != new or store.get('candidate_new_pp') != new:
            raise ValueError('original PP stack output/slot mismatch')
        if hx(d,'r3') != hx(d,'r8') + actor*0x98:
            raise ValueError('original per-actor stride mismatch')
        verified = 'verified_pp_after_store' in store
        if verified:
            if (store.get('verified_pp_before_store'),store.get('verified_pp_after_store'),store.get('actual_instruction_before_store'),store.get('actual_strb_next_pc')) != (old,new,'0x809e6ba','0x809e6bc'):
                raise ValueError('original final STRB CPU step not verified')
            if int(store.get('verified_pp_pre_store_address','-1'),16) != expected:
                raise ValueError('final PP store address mismatch')
        pairs.append({'actor':actor,'slot':slot,'pp_address':hex(expected),'old_pp':old,'cost':cost,'computed_new_pp':new,
                     'original_cpu_store_single_step_verified':verified,
                     'first_pc_t':a['t'],'final_prestore_pc_t':store['t']})
        current=[]
    if not pairs:
        raise ValueError('no complete original CPU PP prestore chains')
    return {'classification':'ORIGINAL_ROM_PP_SLOT_CONSTRUCTION_RESEARCH_ONLY',
            'original_rom_identity':EXACT,'original_cpu_chains':len(pairs),
            'cpu_step_verified_pp_writes':sum(x['original_cpu_store_single_step_verified'] for x in pairs),
            'actor0_cpu_chains':sum(x['actor']==0 for x in pairs),
            'actor1_cpu_chains':sum(x['actor']==1 for x in pairs),
            'chains':pairs,'observed_original_pc_markers':observed,
            'host_battle_narration_acknowledgement':True,
            'disqualifies_unattended_native_test':True,
            'original_engine_owned_one_use_request_reply':'UNPROVEN',
            'original_move_target_dynamic_legality':'UNPROVEN',
            'original_copier_entry_not_completion':'NOT_EQUIVALENT',
            'historical_pp_unmatched_1':'UNCLASSIFIED','historical_pp_unmatched_2':'UNCLASSIFIED',
            'formal_native_auto_acceptance':'0/20','trailing_incomplete_pp_chain_events':len(current)}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('cpu_json')
    parser.add_argument('host_log')
    parser.add_argument('--rom',help='optional exact private ROM file for additional SHA pin')
    args=parser.parse_args()
    print(json.dumps(verify(json.loads(Path(args.cpu_json).read_text()), Path(args.host_log).read_text(),args.rom),indent=2))
