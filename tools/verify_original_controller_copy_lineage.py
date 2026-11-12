#!/usr/bin/env python3
"""Fail-closed ORIGINAL customized-ROM CPU copy/PP marker triage (NOT auto approval).

Checks single-logger STOP transcript parity, an actual six-byte original copier
entry and original shared epilogue byte parity, then original validator/commit
PCs and actor0 PP CPU store. Does NOT establish an engine-owned one-use request,
legal move/target, source-LAB execution or automatic control provenance.
No ROM/save read/write. Source data are recorder attestations, not anti-forgery.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

EXACT_ROM = '4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44'
PP = '0x809e6ba'
EMIT = '0x806bd80'
COPY_ENTRY = '0x806b370'
COPY_DONE = '0x806b3a6'
STAGES = ('0x8094330', '0x809435c', '0x8094374', '0x8094380')
MAIN_CLEAR = '0x808e336'
RUN_RE = re.compile(r'RUN_START (native-[a-f0-9]{32}) pid=([1-9]\d*) start=(\d+(?:\.\d+)?)\Z')
HEX64 = re.compile(r'[0-9a-f]{64}\Z')
KEY_RE = re.compile(r'KEY (x|Left|Right|Up|Down) (\d+(?:\.\d+)?)\Z')
POST_RE = re.compile(r'ORIGINAL_POST_HASH ([0-9a-f]{64}) ([0-9a-f]{64})\Z')


def require(cond, message):
    if not cond:
        raise ValueError(message)


def read_json(s):
    def no_nonfinite(t):
        raise ValueError('non-finite JSON field '+t)
    return json.loads(s, parse_constant=no_nonfinite)


def _finite(v):
    return type(v) in (int, float) and math.isfinite(v)


def _ewram(v):
    return type(v) is str and re.fullmatch(r'0x[0-9a-f]+', v) and 0x02000000 <= int(v, 16) <= 0x0203fffa


def audit(candidate, core, console):
    require(type(candidate) is dict and type(core) is dict and type(console) is str,
            'original capture inputs required')
    require(candidate.get('rom_sha256') == core.get('rom_sha256') == EXACT_ROM,
            'recorded exact modified-ROM hash mismatch')
    require(type(candidate.get('save_sha256')) is str and candidate.get('save_sha256') == core.get('save_sha256') and
            HEX64.fullmatch(candidate['save_sha256']), 'capture save identity mismatch')
    run_id = candidate.get('run_id')
    require(type(run_id) is str and re.fullmatch(r'native-[a-f0-9]{32}',run_id),
            'instrumented run identifier missing')
    ce, pe = candidate.get('candidate_cpu_events'), core.get('original_cpu_events')
    require(type(ce) is list and type(pe) is list and bool(ce) and bool(pe) and
            len(ce) <= 5000 and len(pe) <= 5000, 'missing/unbounded original CPU events')
    for name, rows in (('candidate',ce),('core',pe)):
        prev = -1
        for row in rows:
            require(type(row) is dict and _finite(row.get('t')) and row['t'] > prev and
                    type(row.get('pc')) is str and row.get('after_pc') is not None,
                    'non-monotonic or invalid '+name+' original CPU event')
            prev = row['t']
    # No host command is silently treated as harmless. This captures input *logs*,
    # not a keyboard hardware attestation or a screenshot/video proof.
    markers, logged_c, logged_p, post_hashes, event_counts = [], [], [], [], []
    keys, movement, last_key = [], False, -1
    for line in console.splitlines():
        if RUN_RE.fullmatch(line):markers.append(line)
        elif line == 'GDB S02':pass
        elif line.startswith('COPY_CANDIDATE_STOP '):logged_c.append(read_json(line[len('COPY_CANDIDATE_STOP '):]))
        elif line.startswith('STOP '):logged_p.append(read_json(line[5:]))
        elif line.startswith('KEY '):
            m=KEY_RE.fullmatch(line)
            require(m is not None, 'unrecognized host key')
            key,t=m.group(1),float(m.group(2))
            require(math.isfinite(t) and t>last_key,'host key time invalid')
            last_key=t
            if key in ('Left','Right','Up','Down'):movement=True
            else:require(not movement,'host battle confirm after movement')
            keys.append(key)
        elif (m:=POST_RE.fullmatch(line)) is not None:post_hashes.append(m.groups())
        elif line.startswith('EVENTS ') or line.startswith('COPY_CANDIDATES '):
            k,num=line.split();require(num.isdecimal(), 'invalid event counter')
            event_counts.append((k,int(num)))
        elif line in ('GDB_READ_REGS_BEGIN',) or line.startswith((
            'BP ','EXTRA_BP ','SNAP ','GDB_BREAK_PACKET ', 'GDB_READ_REGS_END ',
            'GDB_STEP_BEGIN ','GDB_STEP_END ','RECEIPT_NOT_VALIDATED ')):
            pass  # Only declared diagnostic markers from the original recorder.
        else:raise ValueError('unknown host console command')
    require(len(markers)==1, 'multiple or absent instrumented run markers')
    require(RUN_RE.fullmatch(markers[0]).group(1)==run_id, 'run ID disagrees with original marker')
    require(movement and 'x' in keys, 'missing original menu/movement key provenance')
    require(logged_c == ce and logged_p == pe, 'raw original GDB STOP transcript mismatch')
    require(sorted(event_counts)==sorted([('COPY_CANDIDATES',len(ce)),('EVENTS',len(pe))]),
            'original GDB event counts disagree')
    require(post_hashes==[(EXACT_ROM,candidate['save_sha256'])],
            'post-run original ROM/save hash attestation mismatch')

    # The original CPU should have *executed* the six-byte loop before it
    # reached the 0x806B3A6 shared return; entry alone is not completion.
    pairs=[]
    for idx,entry in enumerate(ce):
        if not (entry['pc']==COPY_ENTRY and entry.get('r0')=='0x0' and
                entry.get('r1')=='0x1' and entry.get('r3')=='0x6' and
                entry.get('candidate_actor0_reply_copy_entry') is True and
                _ewram(entry.get('source_ptr')) and
                type(entry.get('source6_sha256')) is str and HEX64.fullmatch(entry['source6_sha256'])):
            continue
        for nxt in ce[idx+1:idx+4]:
            if nxt['pc']==COPY_ENTRY:break  # another copier invocation supersedes this one
            if (nxt['pc']==COPY_DONE and nxt.get('candidate_six_byte_copy_epilogue') is True and
                    nxt.get('r1')=='0x6' and nxt.get('r2')=='0x6' and
                    nxt.get('r4')==entry['source_ptr'] and _ewram(nxt.get('copy_destination')) and
                    nxt.get('copy_source')==entry['source_ptr'] and
                    nxt.get('source6_sha256')==entry['source6_sha256'] and
                    nxt.get('destination6_sha256')==entry['source6_sha256'] and
                    nxt.get('bytes_equal_at_epilogue') is True and
                    nxt.get('after_pc')=='0x806b3a8' and
                    0<nxt['t']-entry['t']<3):
                pairs.append((entry,nxt));break
    require(bool(pairs),'no original CPU-completed matching player0 six-byte response copy')

    # Candidate *temporal* chain: emitter -> completed original copy ->
    # validator + commit markers -> player PP -> clear. It does not assert
    # that there was only one issued request or that any move was legal.
    chains=[]
    for entry,done in pairs:
        emissions=[e for e in ce if e['pc']==EMIT and e.get('r0')=='0x0' and e.get('r2')=='0xa' and
                   done['t']-4<e['t']<entry['t']]
        if not emissions:continue
        cursor=done['t'];commits=[]
        for stage in STAGES:
            matched=next((e for e in ce if e['pc']==stage and cursor<e['t']<done['t']+20),None)
            if matched is None:break
            commits.append(matched);cursor=matched['t']
        if len(commits)!=len(STAGES):continue
        pp=next((e for e in pe if e['pc']==PP and e.get('r0')=='0x0' and e.get('after_pc')=='0x809e6bc' and
                 type(e.get('before')) is int and type(e.get('after')) is int and
                 e['before']-1==e['after'] and cursor<e['t']<done['t']+45),None)
        if pp is None:continue
        clear=next((e for e in pe if e['pc']==MAIN_CLEAR and
                    (e.get('before'),e.get('after'),e.get('store_addr'))==(2,0,'0x3005a0d') and
                    pp['t']<e['t']),None)
        if clear is None:continue
        chains.append({'emitter_t':emissions[-1]['t'],'copy_entry_t':entry['t'],
                       'copy_complete_t':done['t'],'copy_source':entry['source_ptr'],
                       'copy_destination':done['copy_destination'],'copied_6_bytes_sha256':done['source6_sha256'],
                       'commit_pc_times':{pc:ev['t'] for pc,ev in zip(STAGES,commits)},
                       'actor0_pp_t':pp['t'],'actor0_pp_addr':pp.get('pp_addr'),
                       'actor0_pp_before':pp['before'],'actor0_pp_after':pp['after'],
                       'original_main_clear_t':clear['t']})
    require(bool(chains),'no ordered same-run actor0 copier/commit/PP/clear marker sequence')
    chains.sort(key=lambda x:x['copy_entry_t'])
    # This is the strongest marker chain, NOT a lease/epoch ID correlation.
    return {'classification':'ORIGINAL_EXACT_ROM_ORDERED_PLAYER0_CONTROLLER_COPY_PP_CANDIDATE_ONLY',
            'run_id':run_id,'original_cpu_console_attested':True,'candidate_cpu_count':len(ce),
            'original_terminal_cpu_count':len(pe),'player0_6_byte_copies':len(pairs),
            'ordered_candidate_chains':chains,
            'one_use_engine_request_ownership':'NOT_PROVEN',
            'legal_move_and_target':'NOT_PROVEN', 'source_lab_auto_execution':'NOT_PROVEN',
            'continuous_unattended_battle_acceptance':'NOT_PROVEN',
            'host_battle_key_after_movement_in_recorded_console':False,
            'original_session_pid_proof':'RECORDER_MARKER_ATTESTED_ONLY',
            'strict_two_terminal_cycles_verifier':'NOT_GRADED_BY_THIS_TOOL',
            'historical_unmatched_pp_1':'UNCLASSIFIED','historical_unmatched_pp_2':'UNCLASSIFIED',
            'formal_native_gameplay_acceptance':'0/20','production_promotion':'0%'}


if __name__=='__main__':
    arg=argparse.ArgumentParser()
    arg.add_argument('original_candidate_json');arg.add_argument('original_core_json');arg.add_argument('--console',required=True)
    args=arg.parse_args()
    report=audit(read_json(Path(args.original_candidate_json).read_text()),
                 read_json(Path(args.original_core_json).read_text()),Path(args.console).read_text())
    print(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
