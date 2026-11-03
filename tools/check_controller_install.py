"""Optional original-instruction installer test with an explicit private ROM."""
from pathlib import Path
import argparse,hashlib,json
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rom=a.rom.read_bytes()
 assert hashlib.sha256(rom).hexdigest()=='6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de'
 assert not a.output.exists();rows=[]
 for entry,kind,completion,run in [(0x08063d24,1,0x080625f9,0x080619d5),(0x080619a0,3,0x080616d9,0x08060ac5),(0x0806645c,2,0x08065e39,0x08065b61)]:
  for actor in range(4):
   u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(UC_CPU_ARM_TI925T)
   for address,size in [(0x08000000,0x2000000),(0x02000000,0x40000),(0x03000000,0x8000)]:u.mem_map(address,size)
   u.mem_write(0x08000000,rom);ew=bytearray(b'\xa5'*0x40000);iw=bytearray(b'\xcc'*0x8000);u.mem_write(0x02000000,bytes(ew));u.mem_write(0x03000000,bytes(iw))
   expected={0x030001a4+actor:bytes([kind]),0x03002e48+4*actor:completion.to_bytes(4,'little'),0x03002e58+4*actor:run.to_bytes(4,'little')}
   if kind==1:expected.update({0x02001e80:b'\0',0x02001e6a:b'\0'})
   for address,data in expected.items():
    target=ew if address<0x03000000 else iw;base=0x02000000 if address<0x03000000 else 0x03000000;target[address-base:address-base+len(data)]=data
   registers=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11];saved=list(range(0x123400,0x123408));sp=0x03007dd0
   for reg,val in zip(registers,saved):u.reg_write(reg,val)
   u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,0x08010001);u.reg_write(UC_ARM_REG_R0,actor);writes=[]
   def write(uc,access,address,size,value,data):writes.append((address,size,value))
   u.hook_add(UC_HOOK_MEM_WRITE,write);u.emu_start(entry|1,0x08010000,count=100)
   assert u.reg_read(UC_ARM_REG_PC)==0x08010000 and u.reg_read(UC_ARM_REG_SP)==sp and u.reg_read(UC_ARM_REG_LR)==0x08010001
   assert [u.reg_read(reg)for reg in registers]==saved
   assert bytes(u.mem_read(0x02000000,0x40000))==ew and bytes(u.mem_read(0x03000000,0x8000))==iw
   assert len(writes)==len(expected)and {address for address,size,value in writes}==set(expected)
   rows.append(dict(entry=hex(entry),actor=actor,kind=kind,writes=[dict(address=hex(address),bytes=size,value=value)for address,size,value in writes]))
 report=dict(rom_sha256=hashlib.sha256(rom).hexdigest(),test_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),passed=len(rows),cases=rows,scope='Original installer instructions under Unicorn TI925T, constructed actors and sentinel RAM; not game initialization, ownership or hardware proof')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(rows),'original installer cases with exact full-EWRAM/IWRAM comparison')
if __name__=='__main__':main()
