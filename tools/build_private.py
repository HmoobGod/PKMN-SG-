"""Reproduce the 16265 cave against a private, SHA-pinned 16264 ROM."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
BASE='db9142c47bbf636f101f3459020c346d838cef9a67d4703d776f24de32f66156'
EXPECTED='deef0016003b281137ef2b85479e4e3691c909f7a2df51725149bf600d22442a'
CAVE='2585b6c3b0e64e93733f93af63dc71a89dfa3d3a5a1af4a898a54dcfe0674330'
IPS='2d016f702ae654427a583abf96ea605ef6cc194e382119f2f7c787f87bd1cb34'
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-rom',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);p.add_argument('--zig',required=True);a=p.parse_args()
 base=a.base_rom.resolve().read_bytes()
 if len(base)!=32*1024*1024 or sha(base)!=BASE:p.error('Expected exact private 16264 base ROM; input rejected before compilation/output')
 outdir=a.out_dir.resolve()
 if outdir==a.base_rom.resolve().parent:p.error('Output directory must differ from the private input directory')
 version=subprocess.check_output([a.zig,'version'],text=True).strip()
 if version!='0.13.0':p.error('This checkpoint requires Zig 0.13.0')
 from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
 from elftools.elf.elffile import ELFFile
 with tempfile.TemporaryDirectory()as td:
  t=Path(td);objects=[]
  for filename,name in [('diagnostic.c','diagnostic'),('snapshot.c','snapshot'),('ranker_workspace.c','ranker'),('sg_action_gate.c','sg_action_gate'),('sg_baseline_mode_guard.c','sg_baseline_mode_guard'),('sg_public_types.c','sg_public_types')]:
   obj=t/(name+'.o');subprocess.run([a.zig,'cc','-target','thumb-freestanding-eabi','-mcpu=arm7tdmi','-O2','-ffreestanding','-fno-builtin','-fno-stack-protector','-ffunction-sections','-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),'-c',str(ROOT/'src'/filename),'-o',str(obj)],check=True);objects.append(str(obj))
  elf=t/'snapshot.elf';subprocess.run([a.zig,'build-exe','-target','thumb-freestanding-eabi','-mcpu','arm7tdmi','-fentry=sg_run_diagnostic','--script',str(ROOT/'src/link.ld'),'--gc-sections',*objects,'-femit-bin='+str(elf)],check=True)
  with elf.open('rb')as f:
   e=ELFFile(f)
   if any(s['sh_flags']&2 and s.name not in ['.text','.ARM.exidx']and s['sh_size']for s in e.iter_sections()):raise RuntimeError('Unexpected allocated ELF section')
   section=e.get_section_by_name('.text');assert section['sh_addr']==0x09f20100;code=section.data()
  wrapper,_=Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm((ROOT/'src/wrapper.s').read_text(),addr=0x09f20000,as_bytes=True)
  assert len(wrapper)<256 and len(code)<0x2f00
  cave=bytearray(b'\xff'*(256+len(code)));cave[:len(wrapper)]=wrapper;cave[256:]=code
  if sha(cave)!=CAVE:raise RuntimeError('Compiled cave differs from pinned16265; no outputs written')
  rom=bytearray(base);offset=0x1f20000;rom[offset:offset+len(cave)]=cave
  if sha(rom)!=EXPECTED:raise RuntimeError('ROM differs from pinned16265; no outputs written')
  patch=b'IPS32'+offset.to_bytes(4,'big')+len(cave).to_bytes(2,'big')+cave+b'EEOF'
  if sha(patch)!=IPS:raise RuntimeError('IPS differs from pinned16265; no outputs written')
  inputs={str(p.relative_to(ROOT)):sha(p.read_bytes())for folder in ['src','include']for p in sorted((ROOT/folder).glob('*'))if p.is_file()}
  receipt=dict(checkpoint=16265,compiler='Zig '+version,base_sha256=BASE,rom_sha256=EXPECTED,cave_sha256=CAVE,ips_sha256=IPS,public_source_hashes=inputs,scope='exact artifact reproduction; no emulator execution or automatic enablement')
  # Validate everything before making the private output directory.
  outdir.mkdir(parents=True,exist_ok=True)
  for name,data in [('SoulGold_16265_EXPERIMENTAL.gba',rom),('from_16264.ips32',patch),('cave.bin',cave),('snapshot.elf',elf.read_bytes()),('build_receipt.json',(json.dumps(receipt,indent=2)+'\n').encode())]:(outdir/name).write_bytes(data)
 print('PASS: exact16265 ROM, cave and IPS reproduced in private output directory')
if __name__=='__main__':main()
