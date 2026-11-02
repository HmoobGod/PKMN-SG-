"""Read-only scorer observation with explicitly labeled disposable request mutations."""
import argparse,ctypes as C,datetime,hashlib,json,shutil,struct,tempfile
from pathlib import Path
SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ROMS={'deef0016003b281137ef2b85479e4e3691c909f7a2df51725149bf600d22442a':16265,'6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de':16266}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['rom','save','state','bridge','output']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--case',choices=['normal','pending0','pending_other','opcode18','opcode20','other_pending_bits'],required=True);a=p.parse_args()
 identities={name:SHA(getattr(a,name))for name in ['rom','save','state','bridge']}
 assert identities['rom']in ROMS
 assert identities['save']=='8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
 assert identities['state']=='0dbcb91a26a3825357f14c18800708a28ef371db57e8fe907ecfbb9dc2c1c7ef'
 assert identities['bridge']=='defd52e255c64153c61b2ce7b02de0b79ea8a1c83bd3993b7b79c46f34de8013'
 assert not a.output.exists()
 with tempfile.TemporaryDirectory()as td:
  t=Path(td);shutil.copy(a.rom,t/'a.gba');shutil.copy(a.save,t/'a.sav');l=C.CDLL(str(a.bridge.resolve()))
  for name,args,ret in [('sg_open',[C.c_char_p,C.c_char_p],C.c_int),('sg_load',[C.c_char_p],C.c_int),('sg_read',[C.c_uint,C.c_uint],C.c_uint),('sg_write',[C.c_uint,C.c_uint,C.c_uint],None),('sg_until_external',[C.c_uint,C.c_uint,C.c_char_p],C.c_int),('sg_reg',[C.c_uint],C.c_uint),('sg_frame',[],C.c_uint),('sg_close',[],None),('sg_refresh_prefetch',[],None)]:f=getattr(l,name);f.argtypes=args;f.restype=ret
  assert l.sg_open(str(t/'a.gba').encode(),str(t/'a.sav').encode())
  try:
   assert l.sg_load(str(a.state).encode());l.sg_refresh_prefetch();assert l.sg_reg(15)==0x08065b1a and l.sg_reg(4)==0
   res=l.sg_read(0x02001c6c,4);pending=l.sg_read(0x02001d2c,4);opcode=l.sg_read(res+0x10,1)
   assert pending&1 and opcode==19
   if a.case in ['pending0','pending_other','other_pending_bits']:l.sg_write(0x02001d2c,{'pending0':0,'pending_other':2,'other_pending_bits':15}[a.case],4)
   if a.case in ['opcode18','opcode20']:l.sg_write(res+0x10,int(a.case[-2:]),1)
   buffers=lambda:bytes(l.sg_read(res+offset+i,1)for offset in [0x10,0x810]for i in range(512))
   def heap():
    head=l.sg_read(0x03001d2c,4);address=head;prev=head;blocks=[]
    for _ in range(1024):
     assert 0x02000000<=address<=0x0203fff0 and address%4==0
     assert l.sg_read(address+2,2)==0xa3a3 and l.sg_read(address+8,4)==prev
     size=l.sg_read(address+4,4)&0x3ffff;nxt=l.sg_read(address+12,4)
     blocks.append([address,size,l.sg_read(address,1)&1])
     if nxt==head:return blocks
     assert nxt==address+16+size;prev=address;address=nxt
    raise AssertionError('heap cycle')
   before=buffers();h=heap();request_pending=l.sg_read(0x02001d2c,4);request_opcode=l.sg_read(res+0x10,1)
   assert l.sg_until_external(0x09f20010,8,str(t/'scored').encode())
   sp=l.sg_reg(13);result=struct.unpack('<12I',bytes(l.sg_read(sp+i,1)for i in range(48)))
   excluded=a.case in ['pending0','pending_other','opcode18','opcode20']and ROMS[identities['rom']]==16266
   assert result[0]==(2 if excluded else 4),(a.case,result)
   if excluded:assert result[1:4]==(0,0,0)and result[11]==0
   assert buffers()==before and heap()==h and l.sg_read(0x02001d2c,4)==request_pending
   report=dict(checkpoint=ROMS[identities['rom']],case=a.case,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),identities=identities,pending=request_pending,opcode=request_opcode,result=dict(zip(['status','bytes','pointer','count','actor','slot','target','move','power','accuracy','policy','freed'],result)),buffers_unchanged=True,heap_headers_restored=True,constructed=a.case!='normal',smart_dispatch=False,scope='Original game hook reaches scorer once; stop at scorer return; pending/opcode mutations only in disposable RAM; not natural stale-request gameplay or ownership proof')
  finally:l.sg_close()
 assert identities=={name:SHA(getattr(a,name))for name in identities}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS',ROMS[identities['rom']],a.case)
if __name__=='__main__':main()
