"""Optional private-ROM test: original resolver with isolated helper stubs.

Requires Unicorn. No game, emitter or native acceptance run is performed.
"""
from pathlib import Path
import argparse,hashlib,itertools,json,struct,time
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
import unicorn
ROM_SHA='deef0016003b281137ef2b85479e4e3691c909f7a2df51725149bf600d22442a'
TABLE=0x0877cc6c

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 rom=a.rom.read_bytes()
 if hashlib.sha256(rom).hexdigest()!=ROM_SHA:p.error('Expected exact private 16265 ROM')
 u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(UC_CPU_ARM_TI925T)
 for address,size in [(0x08000000,0x2000000),(0x02000000,0x40000),(0x03000000,0x8000)]:u.mem_map(address,size)
 u.mem_write(0x08000000,rom)
 saved_regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
 saved_values=[0x12340000+i for i in range(8)];sp=0x03007d00;state={}
 def code(uc,address,size,data):
  state['steps']+=1
  if address==0x08010000:state['returned']=True;uc.emu_stop()
  elif address==0x080de03c:
   # Deliberately isolate the type-reader: fill its three-byte output.
   assert uc.reg_read(UC_ARM_REG_R0)==state['actor']
   assert sp-128<=uc.reg_read(UC_ARM_REG_R2)<=sp-3
   uc.mem_write(uc.reg_read(UC_ARM_REG_R2),bytes([8 if state['ghost'] else 0,0,0]))
   state['helpers'].append('type_reader_stub');uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  elif address==0x080e0028:
   assert uc.reg_read(UC_ARM_REG_R0)==state['actor']
   state['helpers'].append('effect_predicate_stub');uc.reg_write(UC_ARM_REG_R0,state['effect_result']);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  elif address==0x080083d4:raise AssertionError('Unexpected diagnostic path')
  else:assert 0x080e0748<=address<0x080e08d0,hex(address)
 def write(uc,access,address,size,value,data):
  assert sp-128<=address and address+size<=sp,(hex(address),size)
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_WRITE,write)
 rows=[];tests=0;start=time.monotonic()
 for move in range(1,936):
  entry=TABLE-0x08000000+72*move
  effect,packed,target=struct.unpack_from('<HHH',rom,entry+8)
  power=packed>>7;category=(packed>>5)&3;accuracy=target&127;raw=target>>7
  eligible=raw in [1,6] and power>0 and accuracy<=100 and category<=1
  if not eligible and effect not in [4,83,321]:continue
  modes=set();calls=set()
  for actor,species,ghost,effect_result in itertools.product([0,2],[25,0x599],[False,True],[0,1]):
   state.clear();state.update(actor=actor,ghost=ghost,effect_result=effect_result,helpers=[],steps=0,returned=False)
   for reg,val in zip(saved_regs,saved_values):u.reg_write(reg,val)
   u.mem_write(0x02001ecc+actor*152,species.to_bytes(2,'little'))
   u.reg_write(UC_ARM_REG_R0,actor);u.reg_write(UC_ARM_REG_R1,move);u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,0x08010001)
   u.emu_start(0x080e0749,0x08010002,count=2000)
   assert state['returned'] and u.reg_read(UC_ARM_REG_SP)==sp
   assert [u.reg_read(reg)for reg in saved_regs]==saved_values
   expected=raw
   if effect==83 and not ghost:expected=7
   elif effect==4 and rom[entry+39]&128 and effect_result:expected=6
   elif effect==321 and species==0x599:expected=6
   actual=u.reg_read(UC_ARM_REG_R0);assert actual==expected,(move,actor,species,ghost,effect_result,actual,expected)
   if eligible:assert actual in [1,6],(move,actual)
   modes.add(actual);calls.update(state['helpers']);tests+=1
  rows.append(dict(move_id=move,effect=effect,raw_mode=raw,metadata_eligible=eligible,resolved_modes=sorted(modes),stubbed_helpers=sorted(calls)))
 receipt=dict(rom_sha256=ROM_SHA,test_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),unicorn_version=unicorn.__version__,executions=tests,moves=len(rows),metadata_eligible_moves=sum(row['metadata_eligible']for row in rows),override_rows=[row for row in rows if row['effect']in [4,83,321]],elapsed_seconds=time.monotonic()-start,all_expected_modes_match=True,metadata_eligible_modes_stay_in_1_6=True,sp_and_r4_r11_preserved=True,stores_bounded_to_stack=True,scope='Original resolver instructions; helper outputs stubbed; actor/species/type combinations constructed; no emulator gameplay, complete target legality, ownership or automatic acceptance claim')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
