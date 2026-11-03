"""Verify a bounded read-only trace of ORIGINAL non-link buffer-A copier instruction PCs.

Strictly observational: validates a recorder, not source authenticity, ownership,
move legality, emulator correctness or permission to submit any battle command.
No private bytes or ROM code are embedded in this source.
"""
import argparse
import hashlib
import json
from pathlib import Path

ENTRY = 0x0806B370
STORE = 0x0806B3BE
POST = 0x0806B3C6
EWRAM_START, EWRAM_END = 0x02000000, 0x02040000
ROM_SHA = '6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de'
SAVE_SHA = '8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
STATE_SHA = '0dbcb91a26a3825357f14c18800708a28ef371db57e8fe907ecfbb9dc2c1c7ef'
BRIDGE_SHA = 'defd52e255c64153c61b2ce7b02de0b79ea8a1c83bd3993b7b79c46f34de8013'
RUNTIME_SHA = '0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'

class IncompleteTrace(ValueError):
    pass

def require(ok, msg):
    if not ok:
        raise IncompleteTrace(msg)

def address(value, label):
    require(type(value) is int and EWRAM_START <= value < EWRAM_END, f'invalid {label}')
    return value

def within(a, count):
    return EWRAM_START <= a and EWRAM_START <= a+count <= EWRAM_END

def validate_trace(report):
    require(isinstance(report, dict), 'report must be object')
    pins = report.get('hashes')
    require(isinstance(pins, dict), 'missing identity pins')
    for key, value in [('rom',ROM_SHA),('save',SAVE_SHA),('state',STATE_SHA),
                       ('bridge',BRIDGE_SHA),('runtime',RUNTIME_SHA)]:
        require(pins.get(key) == value, f'wrong {key} identity')
    require(report.get('observer_only') is True and report.get('auto_dispatch') is False,
            'instrumentation mode not read-only')
    attempts = report.get('attempts')
    require(isinstance(attempts,list) and 0 < len(attempts) <= 64, 'invalid attempts')
    valid = 0
    last_hit = 0
    for ordinal, attempt in enumerate(attempts):
        require(isinstance(attempt,dict), f'attempt {ordinal}: not an object')
        entry, stores, post = attempt.get('entry'), attempt.get('stores'), attempt.get('post')
        require(isinstance(entry,dict) and isinstance(stores,list) and isinstance(post,dict),
                f'attempt {ordinal}: incomplete original path')
        require(entry.get('pc') == ENTRY and post.get('pc') == POST, f'attempt {ordinal}: PC mismatch')
        require(type(entry.get('hit')) is int and entry['hit'] > last_hit,
                f'attempt {ordinal}: duplicate or out-of-order original entry')
        last_hit = entry['hit']
        require(entry.get('frame') == post.get('frame'),f'attempt {ordinal}: frame changed')
        # Private recorder is pinned to the original, actor-0 single fixture.
        require(entry.get('actor') == 0 and entry.get('direction') == 0 and entry.get('count') == 44,
                f'attempt {ordinal}: unsupported actor/direction/length')
        require(entry.get('link_flag') is False, f'attempt {ordinal}: link path')
        source = address(entry.get('source'), 'source')
        dest = address(entry.get('destination'), 'destination')
        require(within(source,44) and within(dest,44) and
                (source+44 <= dest or dest+44 <= source),
                f'attempt {ordinal}: invalid or overlapping buffers')
        require(entry.get('sp') is not None and type(entry.get('sp')) is int
                and 0x03000010 <= entry['sp'] <= 0x03008000 and entry['sp'] % 4 == 0,
                f'attempt {ordinal}: entry SP invalid')
        require(type(entry.get('lr')) is int and (entry['lr'] & 1) == 1,
                f'attempt {ordinal}: missing Thumb LR')
        payload = entry.get('source_bytes_hex')
        require(isinstance(payload,str) and len(payload) == 88 and
                all(c in '0123456789abcdef' for c in payload),
                f'attempt {ordinal}: source bytes unavailable')
        raw = bytes.fromhex(payload)
        require(raw[0] == 19,f'attempt {ordinal}: not move request')
        require(len(stores) == 44, f'attempt {ordinal}: incomplete store PCs')
        for i, store in enumerate(stores):
            require(isinstance(store,dict) and type(store.get('hit')) is int
                    and store['hit'] > last_hit,
                    f'attempt {ordinal}: store order not observed')
            last_hit = store['hit']
            require(isinstance(store,dict) and store.get('pc') == STORE and
                    store.get('frame') == entry['frame'] and store.get('index') == i and
                    store.get('dest') == dest and store.get('source') == source and
                    store.get('value') == raw[i] and store.get('sp') == entry['sp']-8 and
                    store.get('lr') == entry['lr'],
                    f'attempt {ordinal}: changed/out-of-order native store PC {i}')
        require(type(post.get('hit')) is int and post['hit'] > last_hit,
                f'attempt {ordinal}: post-loop order not observed')
        last_hit = post['hit']
        require(post.get('sp') == entry['sp']-8 and post.get('lr') == entry['lr'] and
                post.get('dest') == dest and post.get('source') == source and
                post.get('copied') == 44 and post.get('count') == 44,
                f'attempt {ordinal}: post-loop registers invalid')
        require(post.get('source_bytes_hex') == payload and post.get('dest_bytes_hex') == payload,
                f'attempt {ordinal}: actual post-copy memory mismatches entry source')
        # Do not infer ownership just because a copy completed.
        valid += 1
    require(report.get('reported_pairs') == valid, 'reported count mismatch')
    require(report.get('player_ownership_proven') is False and
            report.get('move_target_authorized') is False,
            'copy evidence cannot certify ownership or move legality')
    return {'complete_instruction_path_pairs':valid,
            'player_authorization_certificates':0,'automatic_moves_authorized':0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('report',type=Path)
    a=p.parse_args()
    result=validate_trace(json.loads(a.report.read_text()))
    print('PASS offline path consistency:',result)

if __name__=='__main__':
    main()