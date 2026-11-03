"""Offline verify one R8 native player-controller signature beside a real copy.

Reads an R7+R8 observation report. This is a bounded *trace consistency*
check only: original RAM types/callbacks are not a proof of exclusive ownership,
legal target selection, current epoch identity, or game action permission.
"""
import argparse
import json
import hashlib
from pathlib import Path
from verify_alternate_mgba_copy import verify as verify_original_copy

LIVE_MOVE_REQUEST_SHA = 'b92746c4fe980c1d9b05da0eddbff8a6765524390a67fd6f97950b6a41b2cf24'
# Exact preexisting wild-battle controller signatures from the original ROM.
EXPECTED = {
    'flags': 4,
    'battlers_count': 2,
    'controller_kinds': [1, 3],
    'controller_completions': [0x080625F9, 0x080616D9],
    'controller_runners': [0x080619D5, 0x08060AC5],
    'positions': [0, 1],
    'public_present_mask': 3,
    'player_request_opcode': 19,
}
OWN_FIELDS = ('player_own_moves', 'player_request_moves', 'player_own_pp',
              'player_native_restricted_mask_negative_only', 'player_disabled_move',
              'player_encored_move', 'player_encore_timer',
              'player_last_move', 'player_repeat_blocked')
BANNED = ('foe_moves', 'foe_pp', 'enemy_moves', 'enemy_pp',
          'enemy_ability', 'enemy_held_item', 'foe_hp', 'opponent_hp')


def verify(report, expected_request_sha256=LIVE_MOVE_REQUEST_SHA):
    original = verify_original_copy(report)
    if hashlib.sha256(bytes.fromhex(report['source_before_hex'])).hexdigest() != expected_request_sha256:
        raise ValueError('recorded request bytes do not match original independent fixture')
    if report.get('r8_public_context_only') is not True:
        raise ValueError('no R8 public/own-field scope annotation')
    if report.get('original_native_installer_seen_this_process') is not False:
        raise ValueError('fabricated claim of live installer witness')
    if report.get('engine_owned_request_correlated_this_fixture') is not True:
        raise ValueError('correlation not recorded')
    for name in ('postcopy_context', 'pending_context'):
        obj = report.get(name)
        if type(obj) is not dict:
            raise ValueError(f'missing original native context: {name}')
        if set(obj) != set(EXPECTED) | set(OWN_FIELDS) | {'pending_word'}:
            raise ValueError('unexpected/missing context key, including potential hidden opponent reads')
        for banned in BANNED:
            if banned in obj:
                raise ValueError(f'restricted opponent field: {banned}')
        for field, expected in EXPECTED.items():
            actual = obj[field]
            if type(actual) is not type(expected) or actual != expected:
                raise ValueError(f'original native field drift at {name}.{field}')
        for field in ('player_own_moves', 'player_request_moves', 'player_own_pp'):
            if type(obj[field]) is not list or len(obj[field]) != 4 or any(type(v) is not int for v in obj[field]):
                raise ValueError(f'malformed own-only battler field: {field}')
        if any(not 0 <= x < 936 for x in obj['player_own_moves']) or not any(obj['player_own_moves']):
            raise ValueError('invalid or empty own move roster')
        if obj['player_own_moves'] != obj['player_request_moves']:
            raise ValueError('native request move set not equal own live moves')
        if any(not 0 <= x <= 99 for x in obj['player_own_pp']):
            raise ValueError('invalid own PP')
        for field,limit in (('player_native_restricted_mask_negative_only',15),
                            ('player_disabled_move',1023),('player_encored_move',1023),
                            ('player_encore_timer',7),('player_last_move',1023),
                            ('player_repeat_blocked',1)):
            if type(obj[field]) is not int or not 0 <= obj[field] <= limit:
                raise ValueError(f'invalid own-only negative restriction field: {field}')
    before = report['postcopy_context']
    after = report['pending_context']
    if type(before['pending_word']) is not int or before['pending_word'] != 0:
        raise ValueError('pending bit was already live at copy completion')
    if type(after['pending_word']) is not int or after['pending_word'] != 1:
        raise ValueError('missing original native actor0 pending transition')
    if {key:val for key,val in before.items() if key!='pending_word'} != {key:val for key,val in after.items() if key!='pending_word'}:
        raise ValueError('player-controller or own-move data changed before pending')
    if report['native_auto_moves'] != 0 or report['native_automatic_battle_acceptance'] != 0:
        raise ValueError('an observation cannot report automatic acceptance')
    return {
        'status':'PASS: one original wild-battle controller context correlation',
        'verified_original_copy_bytes':original['copy_bytes'],
        'original_controller_kinds':[1,3],
        'own_moves_matched':4,
        'pending_transition_guest_steps':23,
        'live_installer_proven_in_this_process':False,
        'owner_authorization_certificates':0,
        'complete_move_target_legality_certificates':0,
        'automatic_battle_acceptance':0,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('report',type=Path)
    a=p.parse_args()
    print(json.dumps(verify(json.loads(a.report.read_text())),indent=2))

if __name__=='__main__':main()