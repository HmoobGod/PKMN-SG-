"""Observe original controller installation from an earlier field fixture."""
import ctypes as C,hashlib,json,shutil,tempfile,datetime,time,argparse
from pathlib import Path
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--partner-fixture',action='store_true')
for name in ['rom','save','state','bridge','runtime','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();assert not a.output.exists()
rom,save,state,bridge,runtime=a.rom,a.save,a.state,a.bridge,a.runtime
expected=['6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de','8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4','97def16b802f95a7dd990577afe1083f96e8cdee80001cea251d2fb3977cbe24','defd52e255c64153c61b2ce7b02de0b79ea8a1c83bd3993b7b79c46f34de8013','0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d']
assert [sha(x)for x in [rom,save,state,bridge,runtime]]==expected
started=datetime.datetime.now(datetime.timezone.utc).isoformat();t0=time.monotonic()
with tempfile.TemporaryDirectory()as td:
 t=Path(td);shutil.copy(rom,t/'a.gba');shutil.copy(save,t/'a.sav');l=C.CDLL(str(bridge.resolve()))
 for n,args,ret in [('sg_open',[C.c_char_p,C.c_char_p],C.c_int),('sg_load',[C.c_char_p],C.c_int),('sg_read',[C.c_uint,C.c_uint],C.c_uint),('sg_frames',[C.c_uint,C.c_uint],None),('sg_reg',[C.c_uint],C.c_uint),('sg_frame',[],C.c_uint),('sg_trace',[C.c_uint,C.c_uint,C.c_char_p],C.c_int),('sg_close',[],None),('sg_refresh_prefetch',[],None)]:f=getattr(l,n);f.argtypes=args;f.restype=ret
 assert l.sg_open(str(t/'a.gba').encode(),str(t/'a.sav').encode())
 try:
  assert l.sg_load(str(state).encode());l.sg_refresh_prefetch()
  if a.partner_fixture:
   l.sg_fixture_native_partner.argtypes=[C.c_int];l.sg_fixture_double.argtypes=[C.c_uint];l.sg_fixture_native_partner(1);l.sg_fixture_double(0)
  assert l.sg_trace(0,0,str(t/'init').encode())
  base=C.cast(l.sg_reg,C.c_void_p).value-0x4e50;core=C.c_void_p.from_address(base+0x37aa0).value;cpu=C.c_void_p.from_address(core).value;debug=C.c_void_p.from_address(base+0x12288).value;platform=C.c_void_p.from_address(debug+24).value
  assert C.c_void_p.from_address(debug+128).value==base+0x3c70
  assert list((C.c_uint*16).from_address(cpu))==[l.sg_reg(i)for i in range(16)]
  mg=C.CDLL(str(runtime.resolve()));mg.mDebuggerRunFrame.argtypes=[C.c_void_p]
  setbp=C.CFUNCTYPE(C.c_ssize_t,C.c_void_p,C.c_void_p)(C.c_void_p.from_address(platform+56).value)
  points={0x0806a8b0:'constructor_entry',0x0806aad8:'constructor_end',0x0806ad46:'ordinary_assignment',0x0806ad5e:'assignment_done',0x08063d24:'player_install_entry',0x08063d46:'player_install_end',0x080619a0:'opponent_install_entry',0x080619b8:'opponent_install_end',0x0806645c:'partner_install_entry',0x08066474:'partner_install_end',0x08065b18:'scorer_hook'}
  for address in points:
   bp=C.create_string_buffer(32);C.c_uint.from_buffer(bp,8).value=address;C.c_int.from_buffer(bp,12).value=-1;assert setbp(platform,bp)>=0
  events=[];errors=[];CB=C.CFUNCTYPE(None,C.c_void_p,C.c_int,C.c_void_p)
  def snapshot():
   count=l.sg_read(0x02001ab8,1)
   return dict(flags=l.sg_read(0x02001ab4,4),count=count,pending=l.sg_read(0x02001d2c,4),controllers=[dict(actor=i,position=l.sg_read(0x02001b58+i,1),kind=l.sg_read(0x030001a4+i,1),completion=hex(l.sg_read(0x03002e48+i*4,4)),run=hex(l.sg_read(0x03002e58+i*4,4)))for i in range(min(count,4))])
  @CB
  def entered(d,reason,info):
   try:
    if reason==2 and info:
     address=C.c_uint.from_address(info).value
     if address in points:
      regs=list((C.c_uint*16).from_address(cpu));events.append(dict(event=points[address],pc=hex(address),frame=l.sg_frame(),r0=regs[0],r4=regs[4],lr=hex(regs[14]),context=snapshot()))
   except Exception as e:errors.append(str(e))
   C.c_int.from_address(d+32).value=1
  old=C.c_void_p.from_address(debug+128).value;C.c_void_p.from_address(debug+128).value=C.cast(entered,C.c_void_p).value;C.c_int.from_address(debug+32).value=1
  try:
   for n,key in [(100,32),(160,64),(120,16),(450,0)]:
    l.sg_frames(0,key)
    for _ in range(n):mg.mDebuggerRunFrame(debug)
   final=snapshot()
  finally:C.c_void_p.from_address(debug+128).value=old
  assert not errors
  assert any(x['event']=='constructor_entry'for x in events)
  assert any(x['event']=='player_install_entry'and x['r0']==0 for x in events)
  report=dict(started_utc=started,elapsed_seconds=time.monotonic()-t0,probe_source_sha256=sha(__file__),hashes=dict(zip(['rom','save','state','bridge','runtime'],expected)),partner_fixture=a.partner_fixture,events=events,final=final,host_writes='none'if not a.partner_fixture else'existing engine-initialization partner/double fixture; not authentic story partner',automatic_dispatch=False,scope='Controller installation observations from one earlier field fixture, not general player/session ownership or target approval')
  out=a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 finally:l.sg_close()
assert [sha(x)for x in [rom,save,state,bridge,runtime]]==expected
