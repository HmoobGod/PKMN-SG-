"""Offline consistency verifier for a *single* natural wild controller+request trace.
Not ROM-internal player ownership, generic move legality or action authority.
No game file or private memory is read; supplied JSON is not trusted as provenance.
"""
import argparse
import json
from pathlib import Path
ROM_SHA='6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de'
SAVE_SHA='8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
HOST_SHA='fef5effac26b13f53afe88511990fdf3049184402ca50faf9325d4daed7869c7'
PRESTATE_SHA='4157e7c910d9a55a1f19484c4a2daf6eae9707d52ecff3083b9adff3d08d9085'

def require(p,reason):
 if not p:raise ValueError(reason)

def verify(pre,run):
 require(isinstance(pre,dict) and isinstance(run,dict),'expected JSON objects')
 require(pre.get('schema')=='sg16266-cold-save-precontroller-v1','preconstructor schema')
 require(run.get('schema')=='sg16266-r11-fresh-wild-installer-copy-v1','replay schema')
 for doc in (pre,run):
  require(doc.get('original_rom_sha256')==ROM_SHA and doc.get('original_save_sha256')==SAVE_SHA,'private input hashes')
 require(pre.get('loadable_host_sha256')==HOST_SHA,'host identity')
 state_sha=pre.get('private_prewild_state_sha256')
 require(isinstance(state_sha,str) and len(state_sha)==64 and state_sha!='0'*64 and all(x in '0123456789abcdef' for x in state_sha) and pre.get('private_prewild_state_bytes')==397312,'state digest/length consistency only')
 require(run.get('preconstructor_state_sha256')==state_sha,'replay state identity')
 ctor=pre.get('before_controller')
 require(isinstance(ctor,dict),'missing constructor')
 require(ctor.get('frame')==run.get('preconstructor_frame') and isinstance(ctor.get('frame'),int) and ctor['frame']>0,'constructor frame')
 require(ctor.get('original_guest_pc')=='0x806ad46','engine constructor entry')
 require(ctor.get('battle_flags')==4 and ctor.get('battlers')==2,'normal wild ONLY; roamers and partners excluded')
 require(ctor.get('kinds')==[0,0] and ctor.get('player_runner')=='0x806a34d' and ctor.get('opponent_runner')=='0x806a34d','must begin before assignments')
 route=pre.get('route')
 require(isinstance(route,list) and 1<=len(route)<=8,'movement route bounded')
 require(route[-1].get('reason')==2 and route[-1].get('pc')=='0x806ad46' and route[-1].get('flags')=='0x4' and route[-1].get('count')==2 and route[-1].get('kinds')==[0,0],'original normal wild must be last route event')
 for event in route:
  require(event.get('button') in (16,32,64,128) and event.get('reason') in (1,2),'only movement allowed')
 require(route[-1].get('end_frame')==ctor['frame'],'route terminated at constructor')
 require(pre.get('installed_player_certified_general') is False and pre.get('native_auto_acceptance')==0 and pre.get('opponent_ai_modified') is False,'prohibited approval/AI modification')
 windows=run.get('trace_windows')
 require(isinstance(windows,list) and 1<=len(windows)<=18,'bounded replay windows')
 require(windows[0][3]==ctor['frame'],'replay begins before native installer')
 for i,w in enumerate(windows):
  require(isinstance(w,list) and len(w)==7,'native trace window schema')
  j,key,state,start,end,player,foe=w
  require(j==i and key in (0,1) and state in (1,2) and isinstance(start,int) and isinstance(end,int) and 0<=end-start<=90,'window index/key/state/time')
  require(player in (0,1) and foe in (0,1),'installer count per window')
  if i:require(start==windows[i-1][4],'contiguous native execution')
  if i<len(windows)-1:require(state==1,'no early successful request')
 require(windows[-1][2]==2 and sum(x[5] for x in windows)==sum(x[6] for x in windows)==1,'both native installers exactly once, then move request')
 require(run.get('installer_player_executions')==1 and run.get('installer_foe_executions')==1,'installer summary')
 require(run.get('copy_frame')==windows[-1][4] and run.get('pending_set_frame')==run.get('copy_frame'),'copy/pending frame')
 require(run.get('copy_stores')==44 and run.get('pending_set_steps')==23,'exact native A-loop and pending witness')
 digest=run.get('copy_source_sha256')
 require(isinstance(digest,str) and len(digest)==64 and all(x in '0123456789abcdef' for x in digest),'request checksum shape')
 moves=run.get('player_own_move_ids');request=run.get('player_request_move_ids');pp=run.get('player_own_pp')
 require(isinstance(moves,list) and len(moves)==4 and moves==request and isinstance(pp,list) and len(pp)==4,'own and request moves must match')
 require(all(type(x) is int and 0<x<936 for x in moves) and all(type(x) is int and x>=0 for x in pp) and any(pp),'valid own moves/PP shapes')
 require(run.get('auto_submissions')==0 and run.get('automatic_battle_acceptance')==0 and run.get('native_hook_modified') is False and run.get('general_owner_authority') is False and run.get('complete_legality_certified') is False,'cannot claim auto, ownership or legality')
 forbidden={'foe_moves','opponent_hp','opponent_ability','opponent_item','auto_move_payload','engine_action_authority'}
 require(not any(k in d for d in (pre,run) for k in forbidden),'disallowed hidden foe/authorization contents')
 return {'normal_wild_constructor':1,'player_installer':1,'opponent_installer':1,'original_completed_copy_stores':44,'pending_transition_steps':23,'in_rom_auto_acceptance':0}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--pre-report',required=True,type=Path)
 p.add_argument('--request-report',required=True,type=Path)
 a=p.parse_args()
 print('PASS offline natural wild original engine order',verify(json.loads(a.pre_report.read_text()),json.loads(a.request_report.read_text())))