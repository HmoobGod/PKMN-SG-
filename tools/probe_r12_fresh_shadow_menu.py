"""Observe the original first player move request after FRESH wild engine installers.
No native submissions or game memory writes, original ROM/save cloned; single private
preconstructor state created from normal cold-save emulation on same host.
"""
import ctypes as C,hashlib,json,shutil,tempfile,subprocess
from pathlib import Path
import argparse,re
from probe_shadow_menu import host_as_loadable_shared_object,sha,HOST_SHA,ROM_SHA,SAVE_SHA
ROOT=Path(__file__).resolve().parent
# Request replay pins each state to its explicit private preconstructor receipt.
# No JSON receipt by itself supplies original engine ownership authority.
class Request(C.Structure):
 _fields_=[(x,C.c_uint32) for x in ('result','start_frame','end_frame','player_installer','foe_installer','copy_frame','actor','source','length','flags','count','kind0','kind1','completion0','completion1','pending','request_opcode')]+[('steps',C.c_uint64)]
class Proof(C.Structure):
 _fields_=[(name,C.c_uint32) for name in ('state','error','begin_frame','end_frame','entry_frame','post_frame','source','dest','actor','direction','length','entry_sp','entry_lr','post_sp','post_lr','stores','pending_entry','pending_post','opcode_post','total_steps','tag')]+[(name,C.c_uint8*44) for name in ('source_before','source_after','dest_after','store_values')]+[('store_indices',C.c_uint32*44)]
def run(host, rom, save, state, pre_report, output, cc='cc',accepted_mask=3):
 for p,digest in ((host,HOST_SHA),(rom,ROM_SHA),(save,SAVE_SHA)):
  if sha(p)!=digest:raise ValueError('private input SHA mismatch: '+str(p))
 if output.exists():raise FileExistsError('refuse to overwrite private evidence')
 pre=json.loads(pre_report.read_text())
 state_digest=sha(state)
 if (pre.get('private_prewild_state_sha256')!=state_digest or
     state.stat().st_size!=397312 or state.read_bytes()[:4]!=bytes.fromhex('07000001') or
     pre.get('before_controller',{}).get('battle_flags')!=4 or
     pre.get('before_controller',{}).get('kinds')!=[0,0] or
     pre.get('before_controller',{}).get('original_guest_pc')!='0x806ad46'):
  raise ValueError('untrusted precontroller witness')
 with tempfile.TemporaryDirectory() as td:
  tmp=Path(td);shutil.copyfile(rom,tmp/'game.gba');shutil.copyfile(save,tmp/'game.sav');shutil.copyfile(state,tmp/'state.ss')
  host_as_loadable_shared_object(host,tmp/'host.so')
  m=C.CDLL(str(tmp/'host.so'));m.mCoreCreate.argtypes=[C.c_int];m.mCoreCreate.restype=C.c_void_p
  m.mCoreLoadFile.argtypes=[C.c_void_p,C.c_char_p];m.mCoreLoadFile.restype=C.c_bool
  m.mCoreLoadSaveFile.argtypes=[C.c_void_p,C.c_char_p,C.c_bool];m.mCoreLoadSaveFile.restype=C.c_bool
  m.mCoreLoadStateNamed.argtypes=[C.c_void_p,C.c_void_p,C.c_int];m.mCoreLoadStateNamed.restype=C.c_bool
  m.mCoreInitConfig.argtypes=[C.c_void_p,C.c_char_p];m.VFileOpen.argtypes=[C.c_char_p,C.c_int];m.VFileOpen.restype=C.c_void_p
  core=m.mCoreCreate(0)
  def met(off,ret,*types):return C.CFUNCTYPE(ret,C.c_void_p,*types)(C.c_void_p.from_address(core+off).value)
  met(0x12f0,None)(core);m.mCoreInitConfig(core,None)
  if not m.mCoreLoadFile(core,str(tmp/'game.gba').encode()) or not m.mCoreLoadSaveFile(core,str(tmp/'game.sav').encode(),False):
   raise RuntimeError('disposable ROM/save load failed')
  met(0x13d0,None)(core);vf=m.VFileOpen(str(tmp/'state.ss').encode(),0)
  if not vf or not m.mCoreLoadStateNamed(core,vf,0):raise RuntimeError('exact private precontroller state could not load')
  regs=(C.c_uint32*16).from_address(C.c_void_p.from_address(core).value)
  if regs[15]!=0x0806ad48:raise ValueError('precontroller state did not load at expected original constructor PC')
  frame=met(0x1428,C.c_uint32);setkeys=met(0x1408,None,C.c_uint32)
  read8=met(0x1488,C.c_uint32,C.c_uint32,C.c_int);read16=met(0x1490,C.c_uint32,C.c_uint32,C.c_int);read32=met(0x1498,C.c_uint32,C.c_uint32,C.c_int)
  step=met(0x13e8,None)
  subprocess.run([cc,'-std=c11','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-pedantic',str(ROOT/'wait_original_player.c'),'-o',str(tmp/'wait.so')],check=True)
  w=C.CDLL(str(tmp/'wait.so'));w.sg_wait_player_copy.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(Request)]
  # After each bounded original-engine interval, press A to dismiss narration,
  # but STOP at the first actor0 opcode19 copy BEFORE the move menu opens.
  inst0=inst1=0;windows=[]
  for j in range(18):
   button=(1 if j>0 and j%2==0 else 0)
   setkeys(core,button)
   result=Request();w.sg_wait_player_copy(core,regs,90 if not button else 2,15000000,C.byref(result))
   setkeys(core,0)
   inst0+=result.player_installer;inst1+=result.foe_installer
   windows.append((j,button,result.result,result.start_frame,result.end_frame,result.player_installer,result.foe_installer))
   print('WINDOW',windows[-1],flush=True)
   if result.result==2:
    if inst0!=1 or inst1!=1:raise AssertionError(f'original installer count {inst0},{inst1}')
    print('MATCH 44 PLAYER REQUEST',frame(core),'source',hex(result.source),'pending',result.pending,flush=True)
    break
   if result.result==3:raise AssertionError('unexpected non-wild player request')
   if result.result!=1:raise RuntimeError('budget exceeded')
  else:raise RuntimeError('no player move request after bounded ordinary UI')
  # Run exact original copy byte stores read-only, using existing pinned R7 observer.
  subprocess.run(['cc','-std=c11','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',str(ROOT/'alternate_mgba_capture_player_copy.c'),'-o',str(tmp/'cap.so')],check=True)
  cap=C.CDLL(str(tmp/'cap.so'));cap.sg_capture_player_request.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(Proof)]
  proof=Proof();cap.sg_capture_player_request(core,regs,4,2000000,C.byref(proof))
  print('COPY',proof.state,proof.error,proof.stores,frame(core),flush=True)
  if not(proof.state==2 and proof.error==0 and proof.stores==44 and bytes(proof.source_before)==bytes(proof.dest_after) and bytes(proof.store_values)==bytes(proof.source_before)):
   raise RuntimeError('completed natural copy not witnessed')
  if proof.pending_post!=0:raise AssertionError('pending bit already set at native completed-copy boundary')
  for i in range(4000):
   if read32(core,0x02001d2c,0)&1:break
   step(core)
  else:raise AssertionError('no pending signal for natural request')
  own=0x02001ecc
  moves=[read16(core,own+12+2*i,0) for i in range(4)]
  req=[read16(core,proof.dest+4+2*i,0) for i in range(4)]
  pp=[read8(core,own+37+i,0) for i in range(4)]
  print('PENDING',i,'frame',frame(core),'flags',hex(read32(core,0x02001ab4,0)),'kind',read8(core,0x030001a4,0),read8(core,0x030001a5,0),'moves',moves,'request',req,'pp',pp,flush=True)
  if moves!=req or read32(core,0x02001ab4,0)!=4:raise AssertionError('original own move/request data or wild mode drift')
  # R12: Continue original fresh-wild engine into its normal player move menu.
  subprocess.run([cc,'-std=c11','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',str(ROOT/'alternate_mgba_trace_frames.c'),'-o',str(tmp/'trace.so')],check=True)
  tracer=C.CDLL(str(tmp/'trace.so'));tracer.sg_until_pc.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32];tracer.sg_until_pc.restype=C.c_uint32
  reach=tracer.sg_until_pc(core,regs,0x0806449e,12000000)
  print('MOVE MENU',reach,'frame',frame(core),'PC',hex(regs[15]),'pending',read32(core,0x02001d2c,0),flush=True)
  if not reach:raise RuntimeError('fresh original move menu not observed')
  if read32(core,0x02001ab4,0)!=4 or read8(core,0x02001ab8,0)!=2:
   raise AssertionError('not the original supported wild mode at menu')
  if [read8(core,0x030001a4+x,0) for x in range(2)]!=[1,3] or [read8(core,0x02001b58+x,0) for x in range(2)]!=[0,1]:
   raise AssertionError('native controller or positions changed at menu')
  if [read32(core,0x03002e48+4*x,0) for x in range(2)]!=[0x080625f9,0x080616d9]:
   raise AssertionError('native controller completion callbacks changed')
  pending=read32(core,0x02001d2c,0)
  if not(pending&1) or (pending&~3):raise AssertionError('not pending for actor0 or unexpected pending actor')
  if read8(core,proof.dest,0)!=19 or [read16(core,proof.dest+4+2*x,0) for x in range(4)]!=moves:
   raise AssertionError('move request replaced or changed')
  native_cache=read32(core,0x02001d24,0)
  if not(0x02000000<=native_cache<=0x02040000-0x39d) or native_cache&3:
   raise AssertionError('invalid original negative restriction cache pointer')
  restricted_mask=read8(core,native_cache+0x39c,0)
  packed=read32(core,own+0x6c,0)
  restrictions={'negative_mask':restricted_mask,'disabled_move':(packed>>11)&1023,
    'encored_move':(packed>>21)&1023,'encore_timer':(read32(core,own+0x74,0)>>15)&7,
    'repeat_blocked':read8(core,own+0x58,0)>>7,
    'last_move':read16(core,0x02001df8,0)}
  if restrictions['negative_mask']!=0 or restrictions['disabled_move']!=0 or restrictions['encore_timer']!=0 or restrictions['repeat_blocked']!=0:
   raise AssertionError(f'historical test-only mask not supported by new live restrictions: {restrictions}')
  if pp!=[20,10,10,20] or moves!=[325,157,92,269]:raise AssertionError('unknown move/PP fixture')
  # The test only considers previously R9 manual-accepted slot0 and slot1;
  # this historical mask is NOT a fresh engine permission certificate.
  mask=int(accepted_mask)
  if mask not in (1,3):raise ValueError('unsupported host-only historical mask')
  md=[];rb=rom.read_bytes()
  for id,remain in zip(moves,pp):
   e=0x0877cc6c-0x08000000+72*id
   pa=int.from_bytes(rb[e+10:e+12],'little');tb=int.from_bytes(rb[e+12:e+14],'little')
   md.extend(map(str,(id,remain,pa>>7,tb&127,tb>>7)))
  root=ROOT.parent
  scorer=tmp/'sg_shadow_ranker'
  subprocess.run([cc,'-std=c11','-O2','-Wall','-Wextra','-Werror','-pedantic',
    '-I'+str(root/'include'),'-I'+str(root/'src'),str(ROOT/'shadow_ranker.c'),
    str(root/'src'/'ranker_workspace.c'),str(root/'src'/'sg_action_gate.c'),
    str(root/'src'/'sg_baseline_mode_guard.c'),str(root/'src'/'sg_public_types.c'),
    '-o',str(scorer)],check=True)
  scored=subprocess.run([str(scorer),str(mask),*md],text=True,capture_output=True,check=True)
  mat=re.fullmatch(r'SHADOW_ONLY slot=([01]) target=1 candidates=([12]); NO ENGINE PERMISSION\n',scored.stdout)
  if not mat:raise ValueError('unrecognized original isolated C scorer output')
  chosen=int(mat.group(1));candidate_count=int(mat.group(2))
  print('FRESH HOST RANKER',scored.stdout.strip(),'menu_frame',frame(core),flush=True)
  if not(mask&(1<<chosen)):raise AssertionError('shadow selected unavailable test slot')
  subprocess.run([cc,'-std=c11','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-pedantic',
      str(ROOT/'trace_manual_native.c'),'-o',str(tmp/'manual.so')],check=True)
  man=C.CDLL(str(tmp/'manual.so'))
  class Event(C.Structure):
   _fields_=[(k,C.c_uint32) for k in ('pc','frame','r0','r1','r2','r3','r4','r6','pending','own_reply_header','own_reply_payload','own_reply_valid')]
  class Stats(C.Structure):
   _fields_=[(k,C.c_uint32) for k in ('first_frame','last_frame','count','status')]+[('steps',C.c_uint64)]
  man.sg_trace_original_manual.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,
       C.POINTER(Event),C.c_uint32,C.POINTER(Stats)]
  def native_frames(n,key):
   setkeys(core,key);arr=(Event*128)();stats=Stats()
   man.sg_trace_original_manual(core,regs,n,10000000,arr,128,C.byref(stats))
   setkeys(core,0)
   if stats.status!=1 or stats.count>128:raise RuntimeError('native frame budget or overflow')
   return [arr[k] for k in range(stats.count)]
  menu_frame=frame(core)
  native_frames(2,0)
  if chosen==0:
   native_frames(1,32);native_frames(1,0) # original LEFT and release
  emitted=native_frames(1,1)
  emitted+=native_frames(1,0)
  markers={0x0806bd80:'emit',0x0806b370:'reply_entry',0x0806261c:'completion',
     0x080e5e5c:'consumer_check',0x08094330:'native_validation_result',
     0x0809435c:'slot_commit',0x08094374:'move_commit',0x08094380:'target_commit'}
  history=[]
  for ev in emitted:
   if ev.pc not in markers:raise ValueError('unrecognized original PC trace')
   kind=markers[ev.pc]
   row={'kind':kind,'pc':hex(ev.pc),'frame':ev.frame,'pending':ev.pending}
   if kind=='emit':row.update(actor=ev.r0,subcmd=ev.r2,payload=ev.r3)
   elif kind=='reply_entry':row.update(actor=ev.r0,direction=ev.r1,size=ev.r3,
         reply_header=ev.own_reply_header,reply_payload=ev.own_reply_payload,valid=bool(ev.own_reply_valid))
   elif kind=='completion':row.update(actor=ev.r4)
   else:
    row['actor']=ev.r0 if kind=='consumer_check' else ev.r6
    if kind=='native_validation_result':row['native_result']=ev.r0
    if kind=='slot_commit':row['slot']=ev.r0
    if kind=='move_commit':row['move_id']=ev.r0
   history.append(row)
  expected=['emit','reply_entry','completion','consumer_check','native_validation_result','slot_commit','move_commit','target_commit']
  if [row['kind'] for row in history]!=expected:raise ValueError('original native manual selection markers mismatch: '+str(history))
  if any(row['actor']!=0 for row in history):raise AssertionError('non-player native marker')
  payload=256+chosen
  if not(history[0]['subcmd']==10 and history[0]['payload']==payload and
      history[1]['direction']==1 and history[1]['size']==6 and history[1]['valid'] and
      history[1]['reply_header']==0x0a20 and history[1]['reply_payload']==payload and
      history[2]['pending']&1==0 and history[4]['native_result']==0 and
      history[5]['slot']==chosen and history[6]['move_id']==moves[chosen]):
   raise AssertionError('native original reply/restriction/commit rejected or mismatched')
  print('PASS R12 ORIGINAL NATIVE ACCEPT',chosen,moves[chosen],'frame',history[-1]['frame'],flush=True)
  report={
   'schema':'sg16266-r12-fresh-wild-host-shadow-v1',
   'scope':'one clean-save naturally triggered wild encounter; original engine installer, copy, pending and original menu with HOST button inputs; scorer runs HOST ONLY',
   'original_rom_sha256':sha(rom),'original_save_sha256':sha(save),
   'original_host_sha256':sha(host),'preconstructor_state_sha256':state_digest,
   'original_installer_player_executions':inst0,'original_installer_foe_executions':inst1,
   'original_copy_frame':proof.entry_frame,'original_copy_stores':proof.stores,
   'original_copy_source_sha256':hashlib.sha256(bytes(proof.source_before)).hexdigest(),
   'original_pending_set_after_steps':i,'original_pending_set_frame':proof.entry_frame,
   'original_menu_frame':menu_frame,'original_menu_pending_word':pending,
   'original_player_move_ids':moves,'original_player_request_moves':req,'original_player_pp':pp,
   'original_player_negative_restrictions':restrictions,
   'historical_manual_test_mask':mask,
   'selected_by':'unchanged original isolated C Smart AI ranker compiled HOST only',
   'ranker_proposal':{'slot':chosen,'move_id':moves[chosen],'target':1,'candidate_count':candidate_count},
   'original_native_events':history,
   'native_restriction_result_accepted':True,'host_scripted_original_menu_choices':1,
   'in_rom_auto_submissions':0,'in_rom_auto_acceptance':0,'complete_move_legality':False,
   'complete_target_legality':False,'general_exclusive_player_ownership_certified':False,
   'actor1_AI_modified':False,'auto_items_or_capture':False}
  output.parent.mkdir(parents=True,exist_ok=True)
  output.write_text(json.dumps(report,indent=2)+'\n')
  return report


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('host','rom','save','state','pre_report','output'):
  p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
 p.add_argument('--cc',default='cc')
 p.add_argument('--accepted-mask',type=int,choices=(1,3),default=3)
 a=p.parse_args()
 run(a.host,a.rom,a.save,a.state,a.pre_report,a.output,a.cc,a.accepted_mask)