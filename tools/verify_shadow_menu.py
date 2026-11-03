"""Fail-closed R10 host-only Smart AI recommendation -> original menu correlation.

This tool validates internal records only, not game action permission or emulator
integrity. An automated HOST button press is not ROM-integrated Smart AI.
"""
import argparse
import json
from pathlib import Path
from verify_live_context import verify as verify_parent

PCS=(0x0806BD80,0x0806B370,0x0806261C,0x080E5E5C,0x08094330,0x0809435C,0x08094374,0x08094380)
KINDS=('emit','reply_entry','completion','consumer_check','native_validation_result','slot_commit','move_commit','target_commit')
MOVES=(325,157)
SCOPE='one disposable host-selected original move menu input in pinned wild single; no in-ROM automatic action authority'
def require(cond,msg):
    if not cond:raise ValueError(msg)

def verify(report, expected_moves=(325,157,92,269), expected_pp=(20,9,10,20), **parent_opts):
    require(type(report) is dict and report.get('schema')=='sg16266-host-shadow-menu-v1','unsupported host shadow schema')
    require(report.get('scope')==SCOPE,'unsupported shadow scope claim')
    parent=report.get('underlying_live_request')
    require(type(parent) is dict,'missing original native request witness')
    result=verify_parent(parent,**parent_opts)
    require(result.get('automatic_battle_acceptance')==0,'underlying record claims actual auto')
    slot=report.get('selected_move_slot')
    require(type(slot) is int and slot in (0,1),'slot not in recorded R9 accepted fixture')
    move=expected_moves[slot]; payload=256+slot; press=14377 if slot==0 else 14375
    proposal=report.get('shadow_proposal')
    require(type(proposal) is dict,'missing own-move ranker recommendation')
    mask=proposal.get('tested_manual_fixture_mask')
    require(type(mask) is int and mask in (1,3),'unsupported manual acceptance mask')
    require((mask,slot) in ((1,0),(3,1)),'shadow policy did not choose expected move')
    for key,value in [('slot',slot),('target',1),('move_id',move),('candidate_count',1 if mask==1 else 2),
        ('selected_by','original isolated SG public ranker, HOST-ONLY'),
        ('engine_action_authority',False),('original_game_ai_enabled',False)]:
        require(type(proposal.get(key)) is type(value) and proposal[key]==value,f'shadow metadata drift {key}')
    for key,value in [
        ('original_manual_menu_frame',14373),('host_menu_buttons','LEFT then A' if slot==0 else 'A'),
        ('selected_move_slot',slot),('selected_move_id',move),('selected_target_position',1),
        ('original_native_validation_accepted',True),('original_native_emitter_untouched',True),
        ('host_scripted_menu_move_choices',1),('in_rom_auto_moves',0),
        ('automatic_battle_acceptance',0),('general_move_legality_certified',False),
        ('exclusive_player_ownership_certified',False),('other_encounters_certified',False)]:
        require(type(report.get(key)) is type(value) and report[key]==value,f'unsupported outcome {key}')
    ctx=parent['pending_context']
    require(ctx['flags']==4 and ctx['battlers_count']==2 and ctx['controller_kinds']==[1,3] and
            ctx['public_present_mask']==3 and ctx['positions']==[0,1], 'not pinned wild player menu')
    require(ctx['player_own_moves']==list(expected_moves) and ctx['player_request_moves']==list(expected_moves)
            and ctx['player_own_pp']==list(expected_pp), 'unmatched own moves/PP')
    require(ctx['player_native_restricted_mask_negative_only']==0 and ctx['player_disabled_move']==0
            and ctx['player_encore_timer']==0 and ctx['player_repeat_blocked']==0, 'own negative restrictions changed')
    events=report.get('native_player_events')
    require(type(events) is list and len(events)==8 and [e.get('kind') for e in events if type(e) is dict]==list(KINDS),
        'original consumer/command chronology mismatch')
    for i,e in enumerate(events):
        require(type(e) is dict and e.get('original_pc')==hex(PCS[i]),'wrong native PC')
        require(type(e.get('frame')) is int and e['frame']==(press if i<3 else press+1),
                'wrong original frame')
        require(type(e.get('pending_word')) is int and e['pending_word']&1==(1 if i<2 else 0),'wrong pending phase')
        actor='emit_actor' if i==0 else 'reply_actor' if i==1 else 'completion_actor' if i==2 else 'consumer_actor'
        require(type(e.get(actor)) is int and e[actor]==0,'not actor0')
    require(events[0].get('subcmd')==10 and events[0].get('encoded_choice')==payload,'wrong native command')
    require(events[1].get('direction')==1 and events[1].get('bytes')==6 and
        events[1].get('reply_header')==0xA20 and events[1].get('reply_payload')==payload and
        events[1].get('reply_ewram_valid') is True,'original buffer-B response mismatch')
    require(events[4].get('original_native_result')==0,'native restriction was rejected')
    require(events[5].get('committed_move_slot')==slot and events[6].get('committed_move_id')==move,
            'native move commit contradicts host choice')
    return dict(status='PASS: scripted HOST menu input accepted in this wild fixture',
        host_selected_accepted_actions=1, native_in_rom_auto_actions=0, native_auto_acceptance=0,
        owner_certificate=0, general_move_target_certificates=0)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('report',type=Path);a=p.parse_args()
    print(json.dumps(verify(json.loads(a.report.read_text())),indent=2))