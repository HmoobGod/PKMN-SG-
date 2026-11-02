"""Ordinary-button cancel/reject recovery. Late restrictions are disposable RAM fixtures."""
import ctypes as C,sys,tempfile,shutil,json,datetime,argparse
from pathlib import Path
import hashlib
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bind(l):
 for name,args,ret in [('sg_open',[C.c_char_p,C.c_char_p],C.c_int),('sg_load',[C.c_char_p],C.c_int),('sg_read',[C.c_uint,C.c_uint],C.c_uint),('sg_frames',[C.c_uint,C.c_uint],None),('sg_until_external',[C.c_uint,C.c_uint,C.c_char_p],C.c_int),('sg_reg',[C.c_uint],C.c_uint),('sg_close',[],None),('sg_frame',[],C.c_uint),('sg_refresh_prefetch',[],None)]:
  f=getattr(l,name);f.argtypes=args;f.restype=ret
p=argparse.ArgumentParser();p.add_argument('--case',choices=['cancel','late_disable','late_encore','late_repeat'],required=True)
for name in ['rom','save','state','bridge','runtime','out_dir']:p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
a=p.parse_args()
r=a.out_dir;rom=a.rom;state=a.state
assert sha(rom)=='6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de'
assert sha(state)=='0dbcb91a26a3825357f14c18800708a28ef371db57e8fe907ecfbb9dc2c1c7ef'
assert sha(a.save)=='8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
assert sha(a.bridge)=='defd52e255c64153c61b2ce7b02de0b79ea8a1c83bd3993b7b79c46f34de8013'
assert sha(a.runtime)=='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'
r.mkdir(parents=True,exist_ok=True);assert not(r/('flow_'+a.case+'.json')).exists()
with tempfile.TemporaryDirectory() as td:
 t=Path(td);shutil.copy(rom,t/'a.gba');shutil.copy(a.save,t/'a.sav');l=C.CDLL(str(a.bridge.resolve()));bind(l);l.sg_write.argtypes=[C.c_uint,C.c_uint,C.c_uint]
 assert l.sg_open(str(t/'a.gba').encode(),str(t/'a.sav').encode());assert l.sg_load(str(state).encode());l.sg_refresh_prefetch()
 try:
  def request_snapshot(actor):
   res=l.sg_read(0x02001c6c,4)
   return dict(actor=actor,pending_bits=l.sg_read(0x02001d2c,4),opcode=l.sg_read(res+0x10+actor*512,1),run=hex(l.sg_read(0x03002e58+4*actor,4)))
  assert l.sg_reg(15)==0x08065b1a
  initial_request=request_snapshot(0);assert initial_request['pending_bits']&1 and initial_request['opcode']==19
  assert l.sg_until_external(0x0806449c,120,str(t/'menu').encode());l.sg_frames(2,0);assert l.sg_read(0x02001e54,1)==1
  base=C.cast(l.sg_reg,C.c_void_p).value-0x4e50;core=C.c_void_p.from_address(base+0x37aa0).value;cpu=C.c_void_p.from_address(core).value;debug=C.c_void_p.from_address(base+0x12288).value;platform=C.c_void_p.from_address(debug+24).value
  assert C.c_void_p.from_address(debug+128).value==base+0x3c70
  assert list((C.c_uint*16).from_address(cpu))==[l.sg_reg(i) for i in range(16)]
  mg=C.CDLL(str(a.runtime.resolve()));mg.mDebuggerRunFrame.argtypes=[C.c_void_p]
  setbp=C.CFUNCTYPE(C.c_ssize_t,C.c_void_p,C.c_void_p)(C.c_void_p.from_address(platform+56).value)
  points=[0x08065b18,0x080e5e5c,0x08094330,0x0806bd80,0x0806449c]
  for addr in points:
   bp=C.create_string_buffer(32);C.c_uint.from_buffer(bp,8).value=addr;C.c_int.from_buffer(bp,12).value=-1;assert setbp(platform,bp)>=0
  events=[];errors=[];pending=[None];inputs=[];CB=C.CFUNCTYPE(None,C.c_void_p,C.c_int,C.c_void_p)
  @CB
  def entered(d,reason,info):
   try:
    if reason==2 and info:
     pc=C.c_uint.from_address(info).value
     if pc in points:
      regs=list((C.c_uint*16).from_address(cpu))
      if pc==0x080e5e5c:pending[0]=regs[0]
      actor=regs[4] if pc==0x08065b18 else regs[0] if pc==0x0806449c else 0
      if pc!=0x0806449c or not events or events[-1]['pc']!='0x806449c':
       events.append(dict(pc=hex(pc),frame=l.sg_frame(),r0=regs[0],r1=regs[1],r2=regs[2],r3=regs[3],lr=hex(regs[14]),checked_actor=pending[0],request=request_snapshot(actor) if actor<4 else None))
   except Exception as e:errors.append(str(e))
   C.c_int.from_address(d+32).value=1
  old=C.c_void_p.from_address(debug+128).value;C.c_void_p.from_address(debug+128).value=C.cast(entered,C.c_void_p).value;C.c_int.from_address(debug+32).value=1
  def frames(n,key=0):
   inputs.append(dict(frame=l.sg_frame(),frames=n,key=key));l.sg_frames(0,key)
   for _ in range(n):mg.mDebuggerRunFrame(debug)
  mon=0x02001ecc
  if a.case=='late_disable':l.sg_write(mon+0x6c,(l.sg_read(mon+0x6c,4)&~(1023<<11))|(157<<11),4)
  if a.case=='late_encore':l.sg_write(mon+0x6c,(l.sg_read(mon+0x6c,4)&~(1023<<21))|(325<<21),4);l.sg_write(mon+0x74,(l.sg_read(mon+0x74,4)&~(7<<15))|(1<<15),4)
  if a.case=='late_repeat':l.sg_write(mon+0x58,l.sg_read(mon+0x58,1)|128,1);l.sg_write(0x02001df8,157,2)
  try:
   frames(1,2 if a.case=='cancel' else 1);frames(120)
   assert l.sg_read(0x03002e58,4)==0x0806449d,(a.case,hex(l.sg_read(0x03002e58,4)))
   slot=l.sg_read(0x02001e54,1);assert slot==(1 if a.case=='cancel' else 0),slot
   emits=lambda:[e for e in events if e['pc']=='0x806bd80' and e['r0']==0 and e['r2']==10]
   first=emits();assert len(first)==1 and first[0]['r3']==(0xffff if a.case=='cancel' else 257),first
   if a.case!='cancel':assert any(e['pc']=='0x8094330' and e['checked_actor']==0 and e['r0']==1 for e in events)
   before=len(emits());frames(60);assert len(emits())==before
   pp=l.sg_read(mon+37+slot,1);frames(1,1);history=[]
   for _ in range(1200):frames(1);history.append(l.sg_read(mon+37+slot,1))
   assert len(emits())>=2 and emits()[1]['r3']==slot|(1<<8)
   assert any(e['pc']=='0x8094330' and e['checked_actor']==0 and e['r0']==0 for e in events)
   assert pp-1 in history and not errors
   assert any(e['pc']=='0x8065b18' and e['request']['actor']==0 for e in events) if a.case=='cancel' else any(e['pc']=='0x806449c' for e in events)
   requests=[e for e in events if e['pc']in ['0x8065b18','0x806449c']and e['request']['actor']==0]
   assert all(e['request']['pending_bits']&1 and e['request']['opcode']==19 for e in requests),requests
   out=dict(initial_request=initial_request,observed_request_entries=requests,request_fields_valid_at_observed_entries=True,case=a.case,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rom_sha256=sha(rom),state_sha256=sha(state),bridge_sha256=sha(a.bridge),runtime_sha256=sha(a.runtime),native_events=events,recovered_slot=slot,menu_recovered=True,waited_60_frames_without_resubmission=True,pp_decrement_observed=True,continued_frames=1200,inputs=inputs,constructed=a.case!='cancel',scope='same natural wild fixture; late restrictions are host mutations; cancel uses existing auto Fight re-entry; not automatic Smart AI')
   (r/('flow_'+a.case+'.json')).write_text(json.dumps(out,indent=2)+'\n');print('PASS',a.case)
  finally:C.c_void_p.from_address(debug+128).value=old
 finally:l.sg_close()
