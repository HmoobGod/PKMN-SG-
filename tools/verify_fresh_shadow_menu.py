"""Offline consistency validation for a host-only Smart AI menu trial in a
freshly constructed ordinary wild battle. A passing JSON report is NEVER an
in-ROM player authorization, general legality certificate or actual autoplay.
"""
import argparse
import json
from pathlib import Path
from verify_fresh_wild_request import verify as verify_fresh

ROM='6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de'
SAVE='8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
HOST='4304688a0b44007cca23c9e887af17c44530fd602ee3d1e57a232da397bec769'
MOVES=[325,157,92,269]
PP=[20,10,10,20]
ORIGINAL_PCS=[0x806bd80,0x806b370,0x806261c,0x80e5e5c,0x8094330,0x809435c,0x8094374,0x8094380]
KINDS=['emit','reply_entry','completion','consumer_check','native_validation_result','slot_commit','move_commit','target_commit']
FORBIDDEN={'foe_moves','opponent_hp','opponent_pp','opponent_ability','opponent_item','engine_action_authority','permission_certificate','native_auto_move'}

def need(ok,why):
 if not ok:raise ValueError(why)

def verify(pre,r11,record):
 verify_fresh(pre,r11)
 need(type(record) is dict,'new report must be object')
 need(record.get('schema')=='sg16266-r12-fresh-wild-host-shadow-v1','schema')
 need(record.get('original_rom_sha256')==ROM and record.get('original_save_sha256')==SAVE and
      record.get('original_host_sha256')==HOST,'private input identities')
 need(record.get('preconstructor_state_sha256')==pre['private_prewild_state_sha256'],'state lifetime identity')
 need(record.get('original_installer_player_executions')==record.get('original_installer_foe_executions')==1,'original installer path')
 need(record.get('original_copy_frame')==r11['copy_frame'] and record.get('original_copy_stores')==44
      and record.get('original_copy_source_sha256')==r11['copy_source_sha256'],'original completed copy matches')
 need(record.get('original_pending_set_after_steps')==23 and record.get('original_pending_set_frame')==r11['copy_frame'],'original pending signal')
 menu=record.get('original_menu_frame')
 need(type(menu) is int and menu>r11['copy_frame'] and menu-r11['copy_frame']<=12,'original menu frame must follow same request')
 need(record.get('original_menu_pending_word')==3,'wild two-battler pending word at menu')
 need(record.get('original_player_move_ids')==record.get('original_player_request_moves')==r11['player_own_move_ids']==MOVES,'player move identity')
 need(record.get('original_player_pp')==r11['player_own_pp']==PP,'original own PP')
 restrictions=record.get('original_player_negative_restrictions')
 need(type(restrictions) is dict and set(restrictions)=={'negative_mask','disabled_move','encored_move','encore_timer','repeat_blocked','last_move'},'own-only negative restrictions fields')
 need(all(type(v) is int and v==0 for v in restrictions.values()),'only exact zero negative restriction fixture supported')
 mask=record.get('historical_manual_test_mask')
 need(type(mask) is int and mask in (1,3),'historical test-only mask')
 need(record.get('selected_by')=='unchanged original isolated C Smart AI ranker compiled HOST only','ranker source scope')
 p=record.get('ranker_proposal')
 need(type(p) is dict and set(p)=={'slot','move_id','target','candidate_count'},'host proposal exact scope')
 slot=1 if mask==3 else 0
 need(p.get('slot')==slot and p.get('move_id')==MOVES[slot] and p.get('target')==1
      and p.get('candidate_count')==(2 if mask==3 else 1),'exact ranker recommendation for this fixture')
 ev=record.get('original_native_events')
 need(type(ev) is list and len(ev)==8 and all(type(x) is dict for x in ev),'exact original native event count')
 need([x.get('kind') for x in ev]==KINDS and [x.get('pc') for x in ev]==[hex(pc) for pc in ORIGINAL_PCS],'original native consumer sequence')
 need(all(type(x) is dict and x.get('actor')==0 for x in ev),'only actor0 original events')
 need(all(type(x.get('frame')) is int and type(x.get('pending')) is int for x in ev),'native frame/pending integers')
 emitted_frame=ev[0]['frame'];commit_frame=ev[3]['frame']
 need(menu<emitted_frame<=menu+5 and commit_frame==emitted_frame+1,'native event frame chronology')
 need(all(x['frame']==emitted_frame for x in ev[:3]) and all(x['frame']==commit_frame for x in ev[3:]),'native event same-step grouping')
 need(ev[0].get('subcmd')==10 and ev[0].get('payload')==256+slot and ev[0].get('pending')&1==1,'native original emitter')
 need(ev[1].get('direction')==1 and ev[1].get('size')==6 and ev[1].get('valid') is True and
      ev[1].get('reply_header')==0x0A20 and ev[1].get('reply_payload')==256+slot,'native reply payload')
 need(ev[1].get('pending')&1==1 and all(x.get('pending')&1==0 for x in ev[2:]),'native completion/pending chronology')
 need(ev[4].get('native_result')==0 and ev[5].get('slot')==slot and ev[6].get('move_id')==MOVES[slot],'original native accepted move and commits')
 need(record.get('native_restriction_result_accepted') is True and record.get('host_scripted_original_menu_choices')==1,'host-only success')
 for f in ('in_rom_auto_submissions','in_rom_auto_acceptance'):
  need(record.get(f)==0,'cannot inflate in-ROM auto acceptance')
 for f in ('complete_move_legality','complete_target_legality','general_exclusive_player_ownership_certified','actor1_AI_modified','auto_items_or_capture'):
  need(record.get(f) is False,'cannot claim broader permission/AI modification')
 need(not any(k in doc for doc in (pre,r11,record) for k in FORBIDDEN),'no hidden opponent or forged action authorization fields')
 need(set(record)=={'schema','scope','original_rom_sha256','original_save_sha256','original_host_sha256',
    'preconstructor_state_sha256','original_installer_player_executions','original_installer_foe_executions',
    'original_copy_frame','original_copy_stores','original_copy_source_sha256','original_pending_set_after_steps',
    'original_pending_set_frame','original_menu_frame','original_menu_pending_word','original_player_move_ids',
    'original_player_request_moves','original_player_pp','original_player_negative_restrictions',
    'historical_manual_test_mask','selected_by','ranker_proposal','original_native_events',
    'native_restriction_result_accepted','host_scripted_original_menu_choices',
    'in_rom_auto_submissions','in_rom_auto_acceptance','complete_move_legality','complete_target_legality',
    'general_exclusive_player_ownership_certified','actor1_AI_modified','auto_items_or_capture'},'unexpected fields')
 return {'fresh_original_controller_assignments':2,'original_completed_copy':44,
         'host_scorer_move_accepted':slot,'original_native_validation':0,
         'native_in_rom_auto_acceptance':0,'gameplay_ROM_unchanged':True}


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for key in ('pre_report','request_report','shadow_report'):
  ap.add_argument('--'+key.replace('_','-'),type=Path,required=True)
 a=ap.parse_args()
 data=[json.loads(getattr(a,x).read_text()) for x in ('pre_report','request_report','shadow_report')]
 print('PASS R12 offline fresh-wild host-only scorer/engine chronology',verify(*data))

if __name__=='__main__':main()