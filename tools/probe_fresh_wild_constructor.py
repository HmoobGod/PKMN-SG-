"""Read-only engine fresh-wild installer capture from exact original user save.
Other than ordinary emulated button inputs and a private emulator state saved BEFORE
original controller initialization, there are NO game memory edits.
Strict pinned ROM/save and one pinned, temporary ELF host.
"""
import argparse
import ctypes as C,hashlib,json,os,shutil,sys,tempfile,subprocess
from probe_shadow_menu import host_as_loadable_shared_object, HOST_SHA, LOADABLE_SHA, ROM_SHA, SAVE_SHA, sha
from pathlib import Path
HERE=Path(__file__).resolve().parent
class Event(C.Structure):
 _fields_=[(x,C.c_uint32) for x in ('guest_pc','frame','actor_reg0','reg1','reg3','reg4','lr','flags','pending','battler_count','kind0','kind1','completion0','completion1','runner0','runner1','opcode0')]
class Stats(C.Structure):
 _fields_=[(x,C.c_uint32) for x in ('state','first_frame','last_frame','event_count','overflow')]+[('steps',C.c_uint64)]
class Constructor(C.Structure):
 _fields_=[('reason',C.c_uint32),('frame',C.c_uint32),('pc',C.c_uint32),('flags',C.c_uint32),('count',C.c_uint32),('kind0',C.c_uint32),('kind1',C.c_uint32),('install0',C.c_uint32),('install1',C.c_uint32),('steps',C.c_uint64)]

def run(route, host, rom, save, state, report, cc='cc'):
 if any(not p.is_file() for p in (host,rom,save)):
  raise FileNotFoundError('required private host, ROM, or save is absent')
 for p,digest in ((host,HOST_SHA),(rom,ROM_SHA),(save,SAVE_SHA)):
  if sha(p)!=digest:raise ValueError('private input SHA256 mismatch: '+str(p))
 if state.exists() or report.exists():raise FileExistsError('refuse to overwrite private evidence')
 with tempfile.TemporaryDirectory(prefix='sg_new_wild_') as td:
  temp=Path(td)
  shutil.copyfile(rom,temp/'game.gba');shutil.copyfile(save,temp/'game.sav')
  host_as_loadable_shared_object(host,temp/'host.so')
  subprocess.run([cc,'-std=c11','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-pedantic',str(HERE/'stop_at_wild_ctor.c'),'-o',str(temp/'stop.so')],check=True)
  lib=C.CDLL(str(temp/'host.so'));lib.mCoreCreate.argtypes=[C.c_int];lib.mCoreCreate.restype=C.c_void_p
  lib.mCoreLoadFile.argtypes=[C.c_void_p,C.c_char_p];lib.mCoreLoadFile.restype=C.c_bool
  lib.mCoreLoadSaveFile.argtypes=[C.c_void_p,C.c_char_p,C.c_bool];lib.mCoreLoadSaveFile.restype=C.c_bool
  lib.mCoreInitConfig.argtypes=[C.c_void_p,C.c_char_p];lib.VFileOpen.argtypes=[C.c_char_p,C.c_int];lib.VFileOpen.restype=C.c_void_p
  lib.mCoreSaveStateNamed.argtypes=[C.c_void_p,C.c_void_p,C.c_int];lib.mCoreSaveStateNamed.restype=C.c_bool
  core=lib.mCoreCreate(0)
  def method(offset,ret,*types):return C.CFUNCTYPE(ret,C.c_void_p,*types)(C.c_void_p.from_address(core+offset).value)
  method(0x12f0,None)(core);lib.mCoreInitConfig(core,None)
  assert lib.mCoreLoadFile(core,str(temp/'game.gba').encode());assert lib.mCoreLoadSaveFile(core,str(temp/'game.sav').encode(),False)
  frame=method(0x1428,C.c_uint32);keys=method(0x1408,None,C.c_uint32);runframe=method(0x13d8,None)
  method(0x13d0,None)(core)
  regs=(C.c_uint32*16).from_address(C.c_void_p.from_address(core).value)
  observer=C.CDLL(str(temp/'stop.so'))
  observer.sg_until_fresh_wild_constructor.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(Constructor)]
  def ordinary_frames(n,key=0):
   keys(core,key)
   for i in range(n):runframe(core)
   keys(core,0)
  # Confirm original save via the title/Continue screens, no battle choices.
  ordinary_frames(2300)
  for n in (100,140,150,250):
   ordinary_frames(3,1);ordinary_frames(n)
  print('SAVE LOADED',frame(core),flush=True)
  records=[]
  for button,name in route:
   keys(core,button)
   s=Constructor();observer.sg_until_fresh_wild_constructor(core,regs,180,22000000,C.byref(s))
   keys(core,0)
   records.append({'direction':name,'button':button,'end_frame':frame(core),'reason':s.reason,'pc':hex(s.pc),'flags':hex(s.flags),'count':s.count,'kinds':[s.kind0,s.kind1]})
   print('MOVE',name,records[-1],flush=True)
   if s.reason==2:
    state.parent.mkdir(parents=True,exist_ok=True)
    report.parent.mkdir(parents=True,exist_ok=True)
    # Save the core's exact serialized guest state directly. This binary's
    # mCoreSaveStateNamed+VFileOpen combination preallocated zeroed bytes and
    # returned false in the first investigation; never preserve that artifact.
    size=method(0x13f0,C.c_size_t)(core)
    if size!=397312:raise ValueError('unknown core savestate byte count')
    blob=(C.c_uint8*size)()
    saved=method(0x1400,C.c_bool,C.c_void_p)(core,C.cast(blob,C.c_void_p))
    raw=bytes(blob)
    if not saved or raw[:4]!=bytes.fromhex('07000001') or not any(raw):
     raise RuntimeError('host core serialization failed or returned blank state')
    state.write_bytes(raw)
    state_sha=hashlib.sha256(state.read_bytes()).hexdigest()
    doc={'schema':'sg16266-cold-save-precontroller-v1','scope':'ONE original normal wild from clean boot; no auto action / no ownership certificate',
         'original_rom_sha256':sha(rom),
         'original_save_sha256':sha(save),
         'loadable_host_sha256':LOADABLE_SHA,
         'provenance':'no savestate used before original battle constructor; ordinary original title/continue/movement only',
         'before_controller':{'frame':s.frame,'original_guest_pc':hex(s.pc),'battle_flags':s.flags,'battlers':s.count,'kinds':[s.kind0,s.kind1],
                'player_runner':hex(s.install0),'opponent_runner':hex(s.install1)},
         'route':records, 'private_prewild_state_sha256':state_sha, 'private_prewild_state_bytes':state.stat().st_size,
         'installed_player_certified_general':False,'native_auto_acceptance':0,'opponent_ai_modified':False}
    report.write_text(json.dumps(doc,indent=2)+'\n')
    print('PASS RECORDED PRECONTROLLER',state_sha,state.stat().st_size,'frame',s.frame,flush=True)
    if sha(host)!=HOST_SHA or sha(rom)!=ROM_SHA or sha(save)!=SAVE_SHA:
     raise ValueError('original private inputs changed during observation')
    return 0
   if s.reason==3:
    print('UNSUPPORTED MODE',hex(s.flags),'refuse wild certificate',flush=True)
    return 3
   if s.reason not in (1,):raise RuntimeError('step budget or missing result')
   ordinary_frames(80)
  print('NO ENCOUNTER DURING BOUNDED ROUTE',flush=True)
  return 2

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('host','rom','save','output_state','output_report'):
  p.add_argument('--'+n.replace('_','-'),required=True,type=Path)
 p.add_argument('--cc',default='cc')
 a=p.parse_args()
 route=[(16,'right'),(128,'down'),(32,'left'),(64,'up'),(16,'right_second'),(128,'down_second'),(32,'left_second'),(64,'up_second')]
 sys.exit(run(route,a.host,a.rom,a.save,a.output_state,a.output_report,a.cc))