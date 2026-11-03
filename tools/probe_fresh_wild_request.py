"""Observe the original first player move request after FRESH wild engine installers.
No native submissions or game memory writes, original ROM/save cloned; single private
preconstructor state created from normal cold-save emulation on same host.
"""
import ctypes as C,hashlib,json,shutil,tempfile,subprocess
from pathlib import Path
import argparse
from probe_shadow_menu import host_as_loadable_shared_object,sha,HOST_SHA,ROM_SHA,SAVE_SHA
ROOT=Path(__file__).resolve().parent
# Request replay pins each state to its explicit private preconstructor receipt.
# No JSON receipt by itself supplies original engine ownership authority.
class Request(C.Structure):
 _fields_=[(x,C.c_uint32) for x in ('result','start_frame','end_frame','player_installer','foe_installer','copy_frame','actor','source','length','flags','count','kind0','kind1','completion0','completion1','pending','request_opcode')]+[('steps',C.c_uint64)]
class Proof(C.Structure):
 _fields_=[(name,C.c_uint32) for name in ('state','error','begin_frame','end_frame','entry_frame','post_frame','source','dest','actor','direction','length','entry_sp','entry_lr','post_sp','post_lr','stores','pending_entry','pending_post','opcode_post','total_steps','tag')]+[(name,C.c_uint8*44) for name in ('source_before','source_after','dest_after','store_values')]+[('store_indices',C.c_uint32*44)]
def run(host, rom, save, state, pre_report, output, cc='cc'):
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
  assert m.mCoreLoadFile(core,str(tmp/'game.gba').encode());assert m.mCoreLoadSaveFile(core,str(tmp/'game.sav').encode(),False)
  met(0x13d0,None)(core);vf=m.VFileOpen(str(tmp/'state.ss').encode(),0);assert vf and m.mCoreLoadStateNamed(core,vf,0)
  regs=(C.c_uint32*16).from_address(C.c_void_p.from_address(core).value)
  assert regs[15]==0x0806ad48
  frame=met(0x1428,C.c_uint32);setkeys=met(0x1408,None,C.c_uint32)
  read8=met(0x1488,C.c_uint32,C.c_uint32,C.c_int);read16=met(0x1490,C.c_uint32,C.c_uint32,C.c_int);read32=met(0x1498,C.c_uint32,C.c_uint32,C.c_int)
  step=met(0x13e8,None)
  subprocess.run([cc,'-std=c11','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-pedantic',str(ROOT/'wait_original_player.c'),'-o',str(tmp/'wait.so')],check=True)
  w=C.CDLL(str(tmp/'wait.so'));w.sg_wait_player_copy.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(Request)]
  cap=C.CDLL(str(ROOT/'alternate_mgba_capture_player_copy.c')) if False else None
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
  assert proof.pending_post==0
  for i in range(4000):
   if read32(core,0x02001d2c,0)&1:break
   step(core)
  else:raise AssertionError('no pending signal for natural request')
  own=0x02001ecc
  moves=[read16(core,own+12+2*i,0) for i in range(4)]
  req=[read16(core,proof.dest+4+2*i,0) for i in range(4)]
  pp=[read8(core,own+37+i,0) for i in range(4)]
  print('PENDING',i,'frame',frame(core),'flags',hex(read32(core,0x02001ab4,0)),'kind',read8(core,0x030001a4,0),read8(core,0x030001a5,0),'moves',moves,'request',req,'pp',pp,flush=True)
  assert moves==req and read32(core,0x02001ab4,0)==4
  report={'schema':'sg16266-r11-fresh-wild-installer-copy-v1','scope':'one normal wild from original cold-save, saved before controller constructor, original host reloaded; no automatic move or general player authority',
          'original_rom_sha256':sha(rom),
          'original_save_sha256':sha(save),
          'preconstructor_state_sha256':state_digest,
          'preconstructor_frame':pre['before_controller']['frame'],'installer_player_executions':inst0,'installer_foe_executions':inst1,'trace_windows':windows,
          'copy_frame':proof.entry_frame,'copy_stores':proof.stores,'copy_source_sha256':hashlib.sha256(bytes(proof.source_before)).hexdigest(),
          'pending_set_steps':i,'pending_set_frame':frame(core),'player_own_move_ids':moves,'player_request_move_ids':req,'player_own_pp':pp,
          'auto_submissions':0,'automatic_battle_acceptance':0,'native_hook_modified':False,'general_owner_authority':False,'complete_legality_certified':False}
  p=output;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(report,indent=2)+'\n')
  print('PASS R11 SAME-WILD INSTALLER / 44-COPY / PENDING SHA',hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('host','rom','save','state','pre_report','output'):
  p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
 p.add_argument('--cc',default='cc')
 a=p.parse_args()
 run(a.host,a.rom,a.save,a.state,a.pre_report,a.output,a.cc)