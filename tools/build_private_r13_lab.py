#!/usr/bin/env python3
"""Build only an R13 fixture-locked, PRIVATE original-game automatic-move lab ROM.
This is not a general smart-auto gameplay mod and not safe for Current promotion.
Input exact experimental16266 ROM and 44-byte request must be supplied privately.
The original ROM/save are NEVER written to. No raw private request is committed.
"""
import argparse
import hashlib
import json
import os
import struct
import subprocess
import tempfile
from pathlib import Path

BASE_SHA='6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de'
REQUEST_SHA='46a2425f06b61f66a71f361fa96241c01f73268933fbb0f6fa6264b99086adeb'
CURRENT_SHA='7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32'
ROM_SIZE=33554432
WRAP_OFF=0x09f20000-0x08000000
GATE_OFF=0x09f2d000-0x08000000
WRAP_PIN=bytes.fromhex('ffb5604601b48cb02000694600f078f8042809d0052807d0')
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def sha(b):return hashlib.sha256(b).hexdigest()

def emit_private_header(b):
    if len(b)!=44 or sha(b)!=REQUEST_SHA:
        raise ValueError('private request identity mismatch; R13 must fail closed')
    return 'static const uint8_t k_request[44]={\n '+','.join(f'0x{x:02x}' for x in b)+'\n};\n'

def compile_lab(clang, linker, objcopy, workspace, request_bytes):
    header=workspace/'private_r13_request.h';header.write_text(emit_private_header(request_bytes))
    gate_src=ROOT/'research/r13_fixture_gate.c'
    wrap_src=ROOT/'research/r13_fixture_wrapper.s'
    ld_src=workspace/'r13_guard.ld'
    ld_src.write_text('ENTRY(sg_r13_fixture_gate)\nSECTIONS { . = 0x09F2D000; .text : { *(.text*) *(.rodata*) } .ARM.exidx : { *(.ARM.exidx*) } }\n')
    objs=(workspace/'gate.o',workspace/'wrap.o')
    def run(*args):subprocess.run(list(args),check=True,capture_output=True,text=True)
    run(clang,'--target=armv4t-none-eabi','-march=armv4t','-mthumb','-O2',
        '-ffreestanding','-fno-builtin','-fomit-frame-pointer','-fno-stack-protector','-fno-unwind-tables',
        '-I',str(workspace),'-c',str(gate_src),'-o',str(objs[0]))
    run(linker,'-T',str(ld_src),str(objs[0]),'-o',str(workspace/'gate.elf'))
    run(objcopy,'-O','binary',str(workspace/'gate.elf'),str(workspace/'gate.bin'))
    run(clang,'--target=armv4t-none-eabi','-march=armv4t','-mthumb','-c',str(wrap_src),'-o',str(objs[1]))
    run(linker,'-Ttext=0x09F20000','--entry=sg_r13_wrapper',str(objs[1]),'-o',str(workspace/'wrap.elf'))
    run(objcopy,'-O','binary',str(workspace/'wrap.elf'),str(workspace/'wrap.bin'))
    gate=(workspace/'gate.bin').read_bytes();wrapper=(workspace/'wrap.bin').read_bytes()
    if not(48<=len(wrapper)<=256 and 100<=len(gate)<=4096):
        raise AssertionError('lab overlays exceeded reserved cave budgets')
    return wrapper,gate

def generate(src:bytes,wrapper:bytes,gate:bytes):
    if sha(src)!=BASE_SHA or len(src)!=ROM_SIZE:
        raise ValueError('base experimental ROM identity mismatch (never accept Current)')
    if src[WRAP_OFF:WRAP_OFF+len(WRAP_PIN)]!=WRAP_PIN:
        raise ValueError('original callback hook bytes unexpected')
    if src[WRAP_OFF+68:WRAP_OFF+256]!=bytes([255])*(256-68):
        raise ValueError('wrapper expansion cave is not FF')
    if src[GATE_OFF:GATE_OFF+len(gate)]!=bytes([255])*len(gate):
        raise ValueError('guard cave is not FF')
    out=bytearray(src)
    out[WRAP_OFF:WRAP_OFF+len(wrapper)]=wrapper
    out[GATE_OFF:GATE_OFF+len(gate)]=gate
    delta=[i for i,(a,b) in enumerate(zip(src,out)) if a!=b]
    if not delta or any(not(WRAP_OFF<=i<WRAP_OFF+len(wrapper) or GATE_OFF<=i<GATE_OFF+len(gate)) for i in delta):
        raise AssertionError('out-of-scope ROM mutation')
    return bytes(out),delta

def create_ips32(wrapper:bytes,gate:bytes):
    # IPS32 offsets are ROM file offsets, not CPU bus addresses.
    return (b'IPS32'+WRAP_OFF.to_bytes(4,'big')+len(wrapper).to_bytes(2,'big')+wrapper+
            GATE_OFF.to_bytes(4,'big')+len(gate).to_bytes(2,'big')+gate+b'EEOF')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom',type=Path,required=True,help='exact private baseline experimental16266 ROM')
    ap.add_argument('--private-request',type=Path,required=True,help='exact R11 completed 44-byte player request')
    ap.add_argument('--output',type=Path,required=True,help='disposable output only; original inputs never modified')
    ap.add_argument('--clang',default='clang')
    ap.add_argument('--linker',default='ld.lld')
    ap.add_argument('--objcopy',default='llvm-objcopy')
    args=ap.parse_args()
    for path in [args.output,args.output.with_suffix('.manifest.json'),args.output.with_suffix('.ips32')]:
        if path.exists():ap.error(f'output exists, refusal to overwrite: {path}')
    if args.output.resolve()==args.rom.resolve() or args.output.resolve()==args.private_request.resolve():
        ap.error('refuse to overwrite source')
    b=args.rom.read_bytes();request=args.private_request.read_bytes()
    if args.rom.is_symlink() or args.private_request.is_symlink():ap.error('private inputs must be direct regular files')
    with tempfile.TemporaryDirectory(prefix='sg_r13_private_build_') as folder:
        wrapper,gate=compile_lab(args.clang,args.linker,args.objcopy,Path(folder),request)
    result,deltas=generate(b,wrapper,gate)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(result)
    ips=create_ips32(wrapper,gate)
    args.output.with_suffix('.ips32').write_bytes(ips)
    receipt={'schema':'sg16266-r13-fixture-only-rom-v1','base_rom_sha256':sha(b),
        'private_request_sha256':sha(request),'rom_sha256':sha(result),'ips32_sha256':sha(ips),'bytes_modified':len(deltas),
        'overlay_ranges':[{'guest_addr':'0x09f20000','bytes':len(wrapper)},
          {'guest_addr':'0x09f2d000','bytes':len(gate)}],
        'auto_only_for_historical_fixture':True,'current_rom_modified':False,
        'general_owner_certified':False,'complete_legality_certified':False,
        'default_usable_rom':False,'in_rom_auto_enabled_for_general_play':False}
    args.output.with_suffix('.manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()