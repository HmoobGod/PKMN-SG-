"""Fail-closed consistency check for ONE original human-confirmed wild choice.

The original restriction validator ran as part of the game itself; this tool
never invokes it, submits a move, or certifies general legality/ownership.
"""
import argparse
import json
from pathlib import Path
from verify_live_context import verify as verify_live_context

ORDER = ('emit', 'reply_entry', 'completion', 'consumer_check',
         'native_validation_result', 'slot_commit', 'move_commit', 'target_commit')
PCS = (0x0806BD80,0x0806B370,0x0806261C,0x080E5E5C,
       0x08094330,0x0809435C,0x08094374,0x08094380)


def require(ok,msg):
    if not ok:raise ValueError(msg)


def verify(report, expected_request_sha256=None, expected_selected_move_ids=(325,157)):
    require(type(report) is dict,'bad root')
    require(report.get('schema')=='sg16266-native-human-legality-v1','unsupported trace schema')
    underlying=report.get('underlying_live_request')
    require(type(underlying) is dict,'missing original copy/owner-context evidence')
    if expected_request_sha256 is None:
        result=verify_live_context(underlying)
    else:
        result=verify_live_context(underlying,expected_request_sha256=expected_request_sha256)
    require(result['automatic_battle_acceptance']==0,'underlying fixture unauthorized')
    slot=report.get('selected_move_slot')
    require(type(slot) is int and slot in (0,1),'unsupported original manual move slot')
    chosen_move=expected_selected_move_ids[slot]
    payload=256+slot
    press_frame=14377 if slot==0 else 14375
    for flag,value in (
        ('original_user_input','LEFT then A' if slot==0 else 'A'),('manual_native_validation_accepted',True),
        ('original_native_emitter_untouched',True),('automatic_moves',0),
        ('automatic_battle_acceptance',0),('general_move_legality_certified',False),
        ('exclusive_player_ownership_certified',False),('other_encounters_certified',False),
        ('selected_move_slot',slot),('selected_target_position',1),
        ('selected_move_id',chosen_move),
        ('original_manual_menu_frame',14373)):
        require(type(report.get(flag)) is type(value) and report[flag]==value,
                f'unsupported or overstated outcome: {flag}')
    context=underlying['pending_context']
    require(context['player_own_moves'][slot]==chosen_move and
            context['player_request_moves'][slot]==chosen_move and
            context['player_own_pp'][slot]>0,'selected move mismatch/no PP')
    require(context['player_native_restricted_mask_negative_only'] & (1<<slot) == 0,
            'native negative cache excludes selected move')
    require(context['player_disabled_move']!=chosen_move,
            'selected move matches native Disable')
    require(not context['player_encore_timer'] or
            context['player_encored_move']==chosen_move,
            'native Encore excludes selected move')
    require(not context['player_repeat_blocked'] or
            context['player_last_move']!=chosen_move,
            'native repeat exclusion matches move')
    events=report.get('native_player_events')
    require(type(events) is list and len(events)==8,'incomplete original native trace')
    require([x.get('kind') for x in events]==list(ORDER),'original event order drift')
    for index,event in enumerate(events):
        require(type(event) is dict and event.get('original_pc')==hex(PCS[index]),
                'original instruction marker mismatch')
        require(type(event.get('frame')) is int and
                event['frame']==(press_frame if index<3 else press_frame+1),
                'original marker frame/order drift')
        require(type(event.get('pending_word')) is int and
                event['pending_word'] & 1 == (1 if index<2 else 0),
                'actor0 pending phase mismatch')
        actor_field=('emit_actor' if index==0 else 'reply_actor' if index==1 else
                     'completion_actor' if index==2 else 'consumer_actor')
        require(type(event.get(actor_field)) is int and event[actor_field]==0,
                'wrong/unknown actor at original instruction')
    require(events[0].get('subcmd')==10 and
            events[0].get('encoded_choice')==payload,'not original own move command10')
    require(events[1].get('direction')==1 and events[1].get('bytes')==6 and
            events[1].get('reply_header')==0x0A20 and
            events[1].get('reply_payload')==payload and
            events[1].get('reply_ewram_valid') is True,
            'original reply bytes do not match native emitter')
    require(events[4].get('original_native_result')==0,
            'original native restriction rejected proposed move')
    require(events[5].get('committed_move_slot')==slot,
            'original commit chose different move slot')
    require(events[6].get('committed_move_id')==chosen_move,
            'original native move commit mismatch')
    require(report.get('scope')==
       'one original human-confirmed wild single; no auto submission, no complete legality or owner certificate',
       'unsupported generalization of one fixture')
    return {'status':'PASS: one original MANUAL choice accepted by native validator',
            'original_manual_emitter_count':1,
            'original_native_accepted_manual_lifetimes':1,
            'original_slot_move_target_markers':3,
            'automatic_battle_acceptance':0,
            'owner_authorization_certificates':0,
            'general_legality_certificates':0}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('report',type=Path)
    args=p.parse_args()
    print(json.dumps(verify(json.loads(args.report.read_text())),indent=2))

if __name__=='__main__':main()