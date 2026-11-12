#!/usr/bin/env python3
"""Verify *recorded* exact-ROM CPU terminal-chain evidence, without guest writes.

Three explicitly different modes: v3-basic, v4-branch, v5-full. Only v5-full
requires the actual loaded state word and terminal gate. The original outcome
semantics, automatic engine ownership and production 20/20 remain NOT proven.

A legacy archive may be rewrapped from its original CPU JSON and a matching
complete GDB console using --normalize-legacy. This adds a *post-hoc* run ID;
it does not claim that the older capture script recorded an OS process ID.
The console and its STOP rows must match exactly; unknown host commands fail.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

EXACT_ROM_SHA256 = '4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44'
PP = '0x809e6ba'
FIRST_GATE = '0x808e31a'
STATE_LOAD = '0x808e370'
TERMINAL_GATE = '0x808e374'
MAIN_CLEAR = '0x808e336'
MODES = {
    'v3-basic': (PP, FIRST_GATE, MAIN_CLEAR),
    'v4-branch': (PP, FIRST_GATE, TERMINAL_GATE, MAIN_CLEAR),
    'v5-full': (PP, FIRST_GATE, STATE_LOAD, TERMINAL_GATE, MAIN_CLEAR),
}
SHA256_RE = re.compile(r'[0-9a-f]{64}\Z')
KEY_RE = re.compile(r'KEY (x|Left|Right|Up|Down) (\d+(?:\.\d+)?)\Z')
BP_RE = re.compile(r'BP (0x[0-9a-f]+) OK\Z')
SNAP_RE = re.compile(r'SNAP (title|continue_loaded|finished|movement_\d+|stop_\d+)\Z')
ALLOWED_BP_ADDRESSES = frozenset({
    '0x808e31a', '0x808e322', '0x808e336', '0x808e370',
    '0x808e372', '0x808e374', '0x809e6ba',
})
# SNAP is restricted to existing recorder screenshot names. It MUST NOT load,
# create, or restore an emulator savestate. Exact capture scripts remain a
# separate dependency; allowlisted names alone cannot prove screenshot-only behavior.
EVENTS_RE = re.compile(r'EVENTS (\d+)\Z')
POST_HASH_RE = re.compile(r'ORIGINAL_POST_HASH ([0-9a-f]{64}) ([0-9a-f]{64})\Z')
RUN_START_RE = re.compile(
    r'RUN_START ([a-zA-Z0-9:_-]{8,120}) pid=([1-9][0-9]{0,9}) start=([0-9]+(?:\.[0-9]+)?)\Z'
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def _decode_json(s):
    # Refuse Python's permissive NaN, Infinity and -Infinity extensions.
    def invalid(token):
        raise ValueError('non-finite JSON constant '+token)
    return json.loads(s, parse_constant=invalid)


def _strip_run_id(event):
    return {key: value for key, value in event.items() if key != 'run_id'}


def parse_console(console, events, run):
    require(type(console) is str and bool(console), 'mandatory GDB console log missing')
    lines = console.splitlines()
    require(bool(lines), 'empty host console')
    require(type(run) is dict, 'capture run metadata missing')
    run_id = run.get('run_id')
    require(type(run_id) is str and len(run_id) >= 8, 'run ID missing')
    marker = run.get('start_marker')
    require(type(marker) is str and marker == lines[0], 'run start marker mismatch')
    if marker != 'GDB S02':
        parsed = RUN_START_RE.fullmatch(marker)
        require(parsed is not None and parsed.group(1) == run_id,
                'unexpected native run start marker')
        require(type(run.get('pid')) is int and run['pid'] > 0 and
                str(run['pid']) == parsed.group(2), 'instrumented PID marker mismatch')
        started = run.get('started_epoch')
        require(type(started) in (int, float) and math.isfinite(started) and
                started > 0 and float(parsed.group(3)) == started,
                'instrumented start epoch mismatch')
    require(console.count(marker+'\n') <= 1, 'multiple run start markers')
    require(hashlib.sha256(console.encode('utf-8')).hexdigest() == run.get('console_sha256'),
            'recorded GDB console SHA mismatch')

    stop_rows, event_counts, post_hashes = [], [], []
    movement_seen = False
    key_time = -1.0
    seen_marker_count = 0
    for i, line in enumerate(lines):
        if line == marker:
            require(i == 0, 'second GDB run marker')
            seen_marker_count += 1
        elif line == 'GDB S02' or RUN_START_RE.fullmatch(line):
            raise ValueError('second GDB run marker')
        elif (match := BP_RE.fullmatch(line)) is not None:
            require(match.group(1) in ALLOWED_BP_ADDRESSES, 'unknown debugger breakpoint address')
        elif SNAP_RE.fullmatch(line) is not None:
            pass  # Allowlisted screenshot labels ONLY; not savestate operations.
        elif line.startswith('KEY '):
            match = KEY_RE.fullmatch(line)
            require(match is not None, 'unrecognized host key/command')
            name, time_text = match.groups()
            t = float(time_text)
            require(math.isfinite(t) and t > key_time, 'bad host key chronology')
            key_time = t
            if name in ('Left', 'Right', 'Up', 'Down'):
                movement_seen = True
            else:
                require(not movement_seen, 'host battle action may contaminate witness')
        elif line.startswith('STOP '):
            row = _decode_json(line[5:])
            require(type(row) is dict, 'invalid GDB STOP object')
            stop_rows.append(row)
        elif (match := EVENTS_RE.fullmatch(line)) is not None:
            event_counts.append(int(match.group(1)))
        elif (match := POST_HASH_RE.fullmatch(line)) is not None:
            post_hashes.append(match.groups())
        else:
            raise ValueError('unknown host console line or possible unreported command')
    require(seen_marker_count == 1, 'not exactly one start marker')
    require(movement_seen, 'no original movement inputs documented')
    require(len(event_counts) == 1 and event_counts[0] == len(events), 'console event count mismatch')
    require(len(post_hashes) == 1 and post_hashes[0][0] == EXACT_ROM_SHA256,
            'console original ROM post-hash mismatch')
    initial_save = run.get('initial_save_sha256')
    # Legacy archive uses capture.save_sha256; new recorder must carry both.
    if run.get('provenance') == 'INSTRUMENTED_RUN':
        require(type(initial_save) is str and SHA256_RE.fullmatch(initial_save) is not None,
                'instrumented initial save SHA missing')
    else:
        initial_save = run.get('capture_save_sha256')
    require(type(initial_save) is str and SHA256_RE.fullmatch(initial_save) is not None,
            'initial save SHA attestation missing')
    require(post_hashes[0][1] == initial_save, 'post-save hash differs from initial save')
    require(len(stop_rows) == len(events), 'console STOP count mismatch')
    for index, (logged, recorded) in enumerate(zip(stop_rows, events)):
        require(logged == _strip_run_id(recorded), 'CPU STOP mismatch to raw console at index '+str(index))
    return {'console_rows_checked': len(stop_rows), 'console_sha256': run['console_sha256'],
            'host_input_checked': True, 'post_rom_sha256': post_hashes[0][0],
            'post_save_unchanged': True,
            'post_save_hash_basis': 'RECORDED_GDB_POST_HASH_MATCHES_RECORDED_INITIAL_SAVE',
            'snap_names_allowlisted': True, 'breakpoint_addresses_allowlisted': True}


def normalize_legacy_archive(capture, console):
    """Attach archive-derived IDs without changing any original STOP CPU fields.

    IDs are derived after the emulator ran; NOT instrumented process IDs. They
    allow cross-log splices to be detected by original STOP JSON comparison.
    """
    require(type(capture) is dict and type(capture.get('original_cpu_events')) is list,
            'invalid legacy archive JSON')
    require('run' not in capture, 'not an unnormalized legacy capture')
    require(all(type(e) is dict and 'run_id' not in e for e in capture['original_cpu_events']),
            'legacy capture already includes event IDs')
    require(type(console) is str and console.startswith('GDB S02\n'),
            'legacy source needs original GDB start marker')
    digest = hashlib.sha256(console.encode('utf-8')).hexdigest()
    run_id = 'legacy:'+digest
    out = dict(capture)
    out['run'] = {'run_id': run_id, 'start_marker':'GDB S02', 'console_sha256':digest,
                  'provenance':'LEGACY_POSTHOC_IMPORT', 'process_id_observed':False,
                  'capture_save_sha256': capture.get('save_sha256')}
    out['original_cpu_events'] = [dict(e, run_id=run_id) for e in capture['original_cpu_events']]
    return out


def verify_capture(capture, console, mode='v5-full'):
    require(type(capture) is dict, 'capture must be a JSON object')
    require(mode in MODES, 'unsupported verification mode')
    require(capture.get('rom_sha256') == EXACT_ROM_SHA256, 'recorded exact modified-ROM hash missing')
    events = capture.get('original_cpu_events')
    require(type(events) is list and bool(events), 'empty original CPU event log')
    run = capture.get('run')
    require(type(run) is dict and type(run.get('run_id')) is str, 'run ID missing')
    require(run.get('provenance') in ('LEGACY_POSTHOC_IMPORT','INSTRUMENTED_RUN'),
            'unknown run provenance')
    require(type(run.get('process_id_observed')) is bool, 'process observation flag missing')
    if run['provenance'] == 'LEGACY_POSTHOC_IMPORT':
        require(run['process_id_observed'] is False, 'legacy import cannot prove OS process ID')
        require(run['run_id'] == 'legacy:'+run.get('console_sha256',''),
                'legacy run ID must be derived from console digest')
    else:
        require(run['process_id_observed'] is True and
                type(run.get('pid')) is int and run['pid'] > 0 and
                type(run.get('started_epoch')) in (int, float) and
                math.isfinite(run['started_epoch']) and run['started_epoch'] > 0 and
                run.get('start_marker') ==
                'RUN_START '+run['run_id']+' pid='+str(run['pid'])+
                ' start='+str(run['started_epoch']),
                'instrumented run needs matching observed RUN_START pid/start marker')
        require(run.get('initial_save_sha256') == capture.get('save_sha256'),
                'instrumented initial save SHA disagrees with capture')
    require(all(type(e) is dict and e.get('run_id') == run['run_id'] for e in events),
            'mixed-process or missing per-event run IDs')
    # Legacy parser also binds captured save identity to console post-run hash.
    if run['provenance'] == 'LEGACY_POSTHOC_IMPORT':
        require(run.get('capture_save_sha256') == capture.get('save_sha256'),
                'legacy capture save SHA metadata mismatch')
    proof = parse_console(console, events, run)

    episodes, current = [], []
    previous_time = -1.0
    stages = MODES[mode]
    rank = {pc:i for i,pc in enumerate(stages)}
    for e in events:
        pc = e.get('pc')
        require(pc in rank, 'unexpected CPU event in '+mode)
        t = e.get('t')
        require(type(t) in (int,float) and math.isfinite(t) and t > previous_time,
                'non-finite, boolean or non-monotonic CPU chronology')
        previous_time = t
        require(type(e.get('main')) is int and e.get('main') == 2,
                'CPU event not scoped to original battle Main state')
        require(not current or rank[pc] >= rank[current[-1]['pc']],
                'original CPU chain ORDER violated')
        if pc != PP:
            require(not any(old.get('pc') == pc for old in current),
                    'duplicated required CPU gate in episode')
        if pc == PP:
            require(e.get('r0') in ('0x0','0x1') and e.get('after_pc') == '0x809e6bc',
                    'PP CPU ownership/step mismatch')
            require(type(e.get('before')) is int and type(e.get('after')) is int and
                    0 <= e['after'] < e['before'] <= 255 and e['before'] - e['after'] == 1,
                    'PP is not one-byte decrement witness')
            addr = e.get('pp_addr')
            require(type(addr) is str and re.fullmatch(r'0x[0-9a-f]+',addr) and
                    0x02000000 <= int(addr,16) < 0x02040000,
                    'PP RAM address scope mismatch')
        elif pc == FIRST_GATE:
            require(e.get('Z') == 1 and e.get('branch_observed_taken') is True and
                    e.get('after_pc') == '0x808e364', 'first taken branch CPU witness missing')
        elif pc == STATE_LOAD:
            require((e.get('r5'),e.get('state_word'),e.get('after_r3'),e.get('after_pc')) ==
                    ('0x2001ab4','0x4','0x4','0x808e372'), 'state-load CPU RAM witness mismatch')
        elif pc == TERMINAL_GATE:
            require(e.get('Z') == 1 and e.get('branch_observed_taken') is True and
                    e.get('after_pc') == '0x808e324', 'terminal taken branch CPU witness missing')
            if mode == 'v5-full':
                require((e.get('r5'),e.get('state_word'),e.get('r3'),e.get('r4')) ==
                        ('0x2001ab4','0x4','0x4','0x2'), 'terminal gate state word/mask mismatch')
                require((int(e['r3'],16) & int(e['r4'],16)) == 0,
                        'terminal gate TST flags mismatch')
        elif pc == MAIN_CLEAR:
            require((e.get('store_addr'),e.get('before'),e.get('after'),e.get('after_pc'),e.get('r2')) ==
                    ('0x3005a0d',2,0,'0x808e338','0x0'), 'original Main byte-clear store mismatch')
        current.append(e)
        if pc == MAIN_CLEAR:
            require(all(any(x['pc']==expected for x in current) for expected in stages),
                    'missing mandatory original CPU stage')
            pp = [x for x in current if x['pc'] == PP]
            actor_pp_addresses = {actor: {x['pp_addr'] for x in pp if x['r0']==actor} for actor in ('0x0','0x1')}
            require(all(actor_pp_addresses.values()), 'missing player and foe PP CPU witnesses')
            require(actor_pp_addresses['0x0'].isdisjoint(actor_pp_addresses['0x1']),
                    'player/foe PP addresses overlap in one episode')
            episodes.append({
                'first_pp_t':pp[0]['t'], 'clear_t':e['t'],
                'player_pp_writes':sum(x['r0']=='0x0' for x in pp),
                'foe_pp_writes':sum(x['r0']=='0x1' for x in pp),
                'first_gate_taken':True,
                'terminal_gate_taken':TERMINAL_GATE in stages,
                'state_word_0x02001AB4':'0x4' if STATE_LOAD in stages else 'NOT_OBSERVED',
            })
            current = []
    require(len(episodes) >= 2, 'needs at least two complete CPU episodes in one console')
    return {
        'classification':'ORIGINAL_EXACT_ROM_ARCHIVED_CPU_CHAIN_RESEARCH_ONLY',
        'mode':mode,
        'required_stages':list(stages),
        'complete_cpu_episodes':len(episodes),
        'episodes':episodes,
        'trailing_incomplete_events':len(current),
        'run_id':run['run_id'],
        'run_provenance':run['provenance'],
        # The marker remains self-reported; this is *marker-attested*, not
        # external OS process verification.
        'same_emulator_process_log':run['process_id_observed'] and proof['host_input_checked'],
        'process_identity_level':('CAPTURE_MARKER_ATTESTED_PID_AND_START' if
                                  run['process_id_observed'] else 'LEGACY_POSTHOC_ONLY'),
        'archive_single_console_consistent':bool(proof['host_input_checked']),
        'host_input_checked':proof['host_input_checked'],
        'post_save_unchanged':proof['post_save_unchanged'],
        'post_save_hash_basis':proof['post_save_hash_basis'],
        'snap_names_allowlisted':proof['snap_names_allowlisted'],
        'breakpoint_addresses_allowlisted':proof['breakpoint_addresses_allowlisted'],
        'original_rom_identity':'RECORDED_HASH_FIELD_PLUS_GDB_POST_HASH; RAW_ROM_HASH_NOT_VERIFIED_BY_THIS_TOOL',
        'outcome_semantics':'UNCLASSIFIED',
        'engine_request_ownership':'NOT_PROVEN',
        'source_lab_auto_execution':'NOT_PROVEN',
        'host_directional_inputs_during_battle':'NOT_EXCLUDED',
        'fixed_status_labels':{
            'historical_unmatched_pp_1':'UNCLASSIFIED',
            'historical_unmatched_pp_2':'UNCLASSIFIED',
            'formal_native_acceptance':'0/20',
            'label_source':'CONSTANT_NOT_RUNTIME_INFERRED',
        },
    }


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('cpu_events_json')
    parser.add_argument('--console',required=True,help='required full original GDB/host console log')
    parser.add_argument('--mode',choices=tuple(MODES),default='v5-full')
    parser.add_argument('--normalize-legacy',action='store_true',help='post-hoc import; does not prove OS process ID')
    args=parser.parse_args()
    raw_capture=_decode_json(Path(args.cpu_events_json).read_text())
    console=Path(args.console).read_text()
    capture=normalize_legacy_archive(raw_capture,console) if args.normalize_legacy else raw_capture
    print(json.dumps(verify_capture(capture,console,args.mode),indent=2,allow_nan=False))
