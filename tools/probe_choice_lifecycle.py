"""Observe native move-request/reply/consumer lifetimes; never submit a choice directly."""
import argparse,ctypes as C,datetime,hashlib,json,shutil,tempfile,time
from pathlib import Path
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=['confirm','cancel','late_disable','late_encore','late_repeat','late_pp0'],required=True)
for name in ['rom','save','state','bridge','runtime','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();assert not a.output.exists()
paths=[a.rom,a.save,a.state,a.bridge,a.runtime];hashes=[sha(x)for x in paths]
assert hashes==['6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de','8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4','0dbcb91a26a3825357f14c18800708a28ef371db57e8fe907ecfbb9dc2c1c7ef','defd52e255c64153c61b2ce7b02de0b79ea8a1c83bd3993b7b79c46f34de8013','0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d']
started=datetime.datetime.now(datetime.timezone.utc).isoformat();start=time.monotonic()
with tempfile.TemporaryDirectory()as td:
 t=Path(td);shutil.copy(a.rom,t/'a.gba');shutil.copy(a.save,t/'a.sav');l=C.CDLL(str(a.bridge.resolve()))
 for name,args,ret in [('sg_open',[C.c_char_p,C.c_char_p],C.c_int),('sg_load',[C.c_char_p],C.c_int),('sg_read',[C.c_uint,C.c_uint],C.c_uint),('sg_write',[C.c_uint,C.c_uint,C.c_uint],None),('sg_frames',[C.c_uint,C.c_uint],None),('sg_until_external',[C.c_uint,C.c_uint,C.c_char_p],C.c_int),('sg_reg',[C.c_uint],C.c_uint),('sg_frame',[],C.c_uint),('sg_close',[],None),('sg_refresh_prefetch',[],None)]:f=getattr(l,name);f.argtypes=args;f.restype=ret
 assert l.sg_open(str(t/'a.gba').encode(),str(t/'a.sav').encode())
 try:
  assert l.sg_load(str(a.state).encode());l.sg_refresh_prefetch();assert l.sg_reg(15)==0x08065b1a and l.sg_reg(4)==0
  res=l.sg_read(0x02001c6c,4);assert 0x02000000<=res<0x0203f000
  def context():
   battle=l.sg_read(0x02001abc,4);assert 0x02000000<=battle<=0x0203ffe8
   cache=l.sg_read(0x02001d24,4);assert 0x02000000<=cache<=0x0203fc60 and not cache&3
   return dict(pending=l.sg_read(0x02001d2c,4),opcode=l.sg_read(res+0x10,1),run=hex(l.sg_read(0x03002e58,4)),cached_restrictions=l.sg_read(cache+0x39c,1),selection_script_flags=l.sg_read(battle+0x17,1))
  assert context()['pending']&1 and context()['opcode']==19
  epochs=[dict(id=0,origin='seeded request in saved hook state',frame=l.sg_frame(),request_sha256=hashlib.sha256(bytes(l.sg_read(res+0x10+i,1)for i in range(44))).hexdigest(),request_bytes=44,emit=[],reply=[],completion=[],validation=[],commits=[])]
  active=[0];last_submitted=[None];checked=[None];events=[];errors=[]
  assert l.sg_until_external(0x0806449c,120,str(t/'menu').encode());l.sg_frames(2,0)
  base=C.cast(l.sg_reg,C.c_void_p).value-0x4e50;core=C.c_void_p.from_address(base+0x37aa0).value;cpu=C.c_void_p.from_address(core).value;debug=C.c_void_p.from_address(base+0x12288).value;platform=C.c_void_p.from_address(debug+24).value
  assert C.c_void_p.from_address(debug+128).value==base+0x3c70
  assert list((C.c_uint*16).from_address(cpu))==[l.sg_reg(i)for i in range(16)]
  mg=C.CDLL(str(a.runtime.resolve()));mg.mDebuggerRunFrame.argtypes=[C.c_void_p]
  points={0x0806b370:'copy',0x0806bd80:'emit',0x0806261c:'completion',0x080e5e5c:'check',0x08094330:'validation',0x0809435c:'slot_commit',0x08094374:'move_commit',0x08094380:'target_commit'}
  setbp=C.CFUNCTYPE(C.c_ssize_t,C.c_void_p,C.c_void_p)(C.c_void_p.from_address(platform+56).value)
  for address in points:
   bp=C.create_string_buffer(32);C.c_uint.from_buffer(bp,8).value=address;C.c_int.from_buffer(bp,12).value=-1;assert setbp(platform,bp)>=0
  CB=C.CFUNCTYPE(None,C.c_void_p,C.c_int,C.c_void_p)
  @CB
  def entered(d,reason,info):
   try:
    if reason==2 and info:
     pc=C.c_uint.from_address(info).value
     if pc in points:
      regs=list((C.c_uint*16).from_address(cpu));kind=points[pc];e=dict(event=kind,pc=hex(pc),frame=l.sg_frame(),lr=hex(regs[14]),context=context())
      if kind=='copy'and regs[0]==0 and regs[1]in [0,1]:
       size=regs[3];ptr=regs[2];assert 0<size<=512 and 0x02000000<=ptr and ptr+size<=0x02040000
       raw=bytes(l.sg_read(ptr+i,1)for i in range(size));e.update(direction=regs[1],size=size,header=list(raw[:6]))
       if regs[1]==0:
        if raw[0]==19:
         assert size==44
         assert active[0]is None,'new move request before old completion'
         epoch=dict(id=len(epochs),origin='observed native buffer-A copy',frame=l.sg_frame(),request_sha256=hashlib.sha256(raw).hexdigest(),request_bytes=size,emit=[],reply=[],completion=[],validation=[],commits=[]);epochs.append(epoch);active[0]=epoch['id'];e['epoch']=active[0]
        events.append(e)
       elif raw[:2]==bytes([32,10]):
        assert active[0]is not None,'move reply without open request'
        epoch=epochs[active[0]];assert len(epoch['emit'])==1 and not epoch['reply'];assert int.from_bytes(raw[2:6],'little')==epoch['emit'][0]['payload']
        e['epoch']=active[0];epoch['reply'].append(e);events.append(e)
      elif kind=='emit'and regs[0]==0 and regs[2]==10:
       assert active[0]is not None,'emit without open request'
       epoch=epochs[active[0]];assert not epoch['emit'],'duplicate emit in request'
       assert e['context']['pending']&1 and e['context']['opcode']==19
       e.update(epoch=active[0],payload=regs[3]);epoch['emit'].append(e);events.append(e)
      elif kind=='completion'and regs[4]==0 and active[0]is not None:
       epoch=epochs[active[0]];assert len(epoch['emit'])==len(epoch['reply'])==1
       assert not e['context']['pending']&1 and e['context']['run']=='0x80619d5'
       e['epoch']=active[0];epoch['completion'].append(e);last_submitted[0]=active[0];active[0]=None;events.append(e)
      elif kind=='check'and regs[14]==0x08094331:
       assert regs[0]==regs[6]
       checked[0]=last_submitted[0]if regs[0]==0 else None
       if regs[0]==0:assert checked[0]is not None
      elif kind=='validation'and regs[6]==0 and checked[0]is not None:
       epoch=epochs[checked[0]];assert not epoch['validation'];e.update(epoch=checked[0],result=regs[0]);epoch['validation'].append(e);events.append(e)
      elif kind.endswith('_commit')and regs[6]==0 and checked[0]is not None:
       epoch=epochs[checked[0]];assert epoch['validation']and epoch['validation'][0]['result']==0;e['epoch']=checked[0];epoch['commits'].append(e);events.append(e)
   except Exception as exc:errors.append(dict(error=repr(exc),pc=hex(pc),event=kind,frame=l.sg_frame(),active=active[0],last_submitted=last_submitted[0],checked=checked[0]))
   C.c_int.from_address(d+32).value=1
  old=C.c_void_p.from_address(debug+128).value;C.c_void_p.from_address(debug+128).value=C.cast(entered,C.c_void_p).value;C.c_int.from_address(debug+32).value=1
  def frames(n,key=0):
   l.sg_frames(0,key)
   for _ in range(n):mg.mDebuggerRunFrame(debug)
  try:
   mon=0x02001ecc
   if a.case=='late_disable':l.sg_write(mon+0x6c,(l.sg_read(mon+0x6c,4)&~(1023<<11))|(157<<11),4)
   if a.case=='late_encore':l.sg_write(mon+0x6c,(l.sg_read(mon+0x6c,4)&~(1023<<21))|(325<<21),4);l.sg_write(mon+0x74,(l.sg_read(mon+0x74,4)&~(7<<15))|(1<<15),4)
   if a.case=='late_repeat':l.sg_write(mon+0x58,l.sg_read(mon+0x58,1)|128,1);l.sg_write(0x02001df8,157,2)
   if a.case=='late_pp0':l.sg_write(mon+38,0,1)
   frames(1,2 if a.case=='cancel'else 1);frames(180)
   if a.case!='confirm':
    assert l.sg_read(0x03002e58,4)==0x0806449d
    frames(1,1)
   frames(1200)
  finally:C.c_void_p.from_address(debug+128).value=old
  if errors:
   a.output.parent.mkdir(parents=True,exist_ok=True);a.output.with_suffix('.failure.json').write_text(json.dumps(dict(errors=errors,epochs=epochs,events=events),indent=2))
  assert not errors,errors
  submitted=[x for x in epochs if x['emit']]
  assert submitted
  for epoch in submitted:
   assert len(epoch['emit'])==len(epoch['reply'])==len(epoch['completion'])==1
   if epoch['emit'][0]['payload']==65535:assert not epoch['validation']and not epoch['commits']
   else:
    assert len(epoch['validation'])==1
    assert [e['event']for e in epoch['commits']]==(['slot_commit','move_commit','target_commit']if epoch['validation'][0]['result']==0 else[])
  if a.case not in ['confirm','cancel']:assert submitted[0]['validation'][0]['result']==1
  assert any(x['validation']and x['validation'][0]['result']==0 for x in submitted)
  report=dict(case=a.case,started_utc=started,elapsed_seconds=time.monotonic()-start,hashes=dict(zip(['rom','save','state','bridge','runtime'],hashes)),probe_source_sha256=sha(__file__),epochs=epochs,events=events,active_epoch_at_end=active[0],constructed=a.case not in ['confirm','cancel'],host_epoch_ids_only=True,automatic_dispatch=False,scope='Request/reply correlation in one saved fixture; IDs are host observation counters, not engine tokens or action authority; late restrictions are host mutations')
 finally:l.sg_close()
assert [sha(x)for x in paths]==hashes
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS',a.case,len(epochs),'requests',len(submitted),'submitted')
