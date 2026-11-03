"""R13 PRIVATE fixture-locked in-ROM action probe. Input is an exact pinned LAB
ROM with the source Smart AI scorer at the original hook and a one-request gate.
All files are cloned, host sends NO move-menu buttons after completed copy.
This must not be used to certify general gameplay legality or Current promotion.
"""
import ctypes as C,hashlib,json,shutil,tempfile,subprocess
from pathlib import Path
import argparse,re
from probe_shadow_menu import host_as_loadable_shared_object,sha,HOST_SHA,SAVE_SHA
ROM_SHA="70b0f846f8685cc09719476a166621289a5e7d47707695b5de9dc7f3e1bfde05"
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
  subprocess.run([cc,'-std=c11','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-pedantic',str(ROOT/'trace_r13_candidate.c'),'-o',str(tmp/'trace13.so')],check=True)
  tracer=C.CDLL(str(tmp/'trace13.so'))
  class Ev13(C.Structure):
   _fields_=[(k,C.c_uint32) for k in ('pc','frame','r0','r1','r2','r3','r4','r5','r6','pending','cursor','auto_slot','reply_header','reply_payload','reply_valid')]
  class Stats13(C.Structure):
   _fields_=[(k,C.c_uint32) for k in ('start_frame','end_frame','count','status')]+[('steps',C.c_uint64)]
  tracer.sg_r13_trace.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_uint32,C.c_uint64,C.POINTER(Ev13),C.c_uint32,C.POINTER(Stats13)]
  timeline=(Ev13*300)();stats=Stats13()
  setkeys(core,0)
  tracer.sg_r13_trace(core,regs,14,30000000,timeline,300,C.byref(stats))
  print('R13 TRACE',stats.start_frame,stats.end_frame,stats.status,stats.count,stats.steps,flush=True)
  rows=[]
  for j in range(min(stats.count,300)):
   e=timeline[j]
   v={'pc':hex(e.pc),'frame':e.frame,'r0':e.r0,'r1':e.r1,'r2':e.r2,'r3':e.r3,'r4':e.r4,'r5':e.r5,'r6':e.r6,
      'pending':e.pending,'cursor':e.cursor,'auto_slot':e.auto_slot,'reply_header':e.reply_header,'reply_payload':e.reply_payload,'reply_valid':e.reply_valid}
   rows.append(v)
   print('R13EVENT',v,flush=True)
  # Critical assertion: no externally scripted selection after the original
  # request copy. The ONLY route to a valid player command is the modified
  # disposable ROM's strict C fixture gate and existing native auto handler.
  player_emit=[r for r in rows if r['pc']=='0x806bd80' and r['r0']==0 and r['r2']==10]
  actor0_reply=[r for r in rows if r['pc']=='0x806b370' and r['r0']==0 and r['r1']==1 and r['r3']==6]
  own_valid=[r for r in rows if r['pc']=='0x8094330' and r['r6']==0]
  own_slot=[r for r in rows if r['pc']=='0x809435c' and r['r6']==0]
  own_move=[r for r in rows if r['pc']=='0x8094374' and r['r6']==0]
  own_target=[r for r in rows if r['pc']=='0x8094380' and r['r6']==0]
  if not (inst0==1 and inst1==1 and stats.status==1 and stats.count<300 and
      len([r for r in rows if r['pc']=='0x9f2d000'])==1 and
      len([r for r in rows if r['pc']=='0x9f20022' and r['r0']==1])==1 and
      len([r for r in rows if r['pc']=='0x8065eb4'])==1 and
      len(player_emit)==len(actor0_reply)==len(own_valid)==len(own_slot)==len(own_move)==len(own_target)==1 and
      player_emit[0]['r3']==257 and actor0_reply[0]['reply_valid']==1 and
      actor0_reply[0]['reply_header']==0x0a20 and actor0_reply[0]['reply_payload']==257 and
      own_valid[0]['r0']==0 and own_slot[0]['r0']==1 and own_move[0]['r0']==157 and
      own_target[0]['r2']==1 and
      not any(r['pc']=='0x806449c' and r['frame']<=own_target[0]['frame'] for r in rows)):
   raise RuntimeError('LAB candidate did not reach exactly one original in-ROM native accepted actor0 move')
  print('PASS R13 IN-ROM ORIGINAL ACCEPT',frame(core),'player command 257, slot1 move157 target1',flush=True)
  report={'rom_sha256':ROM_SHA,'save_sha256':SAVE_SHA,'state_sha256':state_digest,
     'copy_complete_44':proof.stores==44 and proof.state==2,'pending_set_after_steps':i,
     'events':rows,'status':stats.status,'steps':stats.steps,'end_frame':stats.end_frame,
     'original_player_installer_count':inst0,'original_foe_installer_count':inst1,
     'host_move_menu_buttons_sent':0,'lab_native_in_rom_auto_submission':1,'lab_native_in_rom_auto_acceptance':1,
     'general_owner_certified':False,'complete_move_legality':False,'complete_target_legality':False,
     'normal_playable_auto_enabled':False,'automatic_items_or_capture':False}
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