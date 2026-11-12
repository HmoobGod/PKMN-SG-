#!/usr/bin/env python3
"""Reproduce ORIGINAL in-ROM player-only wild auto from pinned private inputs.

Read-only original user inputs; copies into disposable emulator work directory.
No host move menu button presses, memory writes, ROM build or new hook.
The ROM/save/state/host/private receipt are never uploaded to public GitHub.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import verify_exact_modified_autoplay as verify

HERE = Path(__file__).resolve().parent
HOST_SHA = '4304688a0b44007cca23c9e887af17c44530fd602ee3d1e57a232da397bec769'
LOADABLE_SHA = 'fef5effac26b13f53afe88511990fdf3049184402ca50faf9325d4daed7869c7'

class Event(C.Structure):
    _fields_ = [(k,C.c_uint32) for k in (
        'pc','frame','r0','r1','r2','r3','r4','r5','r6','pending',
        'cursor','auto_slot','reply_header','reply_payload','reply_valid')]
class Stats(C.Structure):
    _fields_ = [(k,C.c_uint32) for k in (
        'start_frame','end_frame','count','status')] + [('steps',C.c_uint64)]

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(2097152),b''):
            h.update(chunk)
    return h.hexdigest()

def run(host,rom,save,state,receipt,output,cc='cc'):
    inputs=((host,HOST_SHA),(rom,verify.ROM_SHA),
            (save,verify.SAVE_SHA),(state,verify.STATE_SHA))
    for path,expected in inputs:
        if not path.is_file() or path.is_symlink() or sha(path)!=expected:
            raise ValueError('unverified read-only private input: '+path.name)
    if output.exists() or output.resolve() in {p.resolve() for p,_ in inputs}:
        raise ValueError('refuse private input overwrite or existing report')
    if not receipt.is_file() or receipt.is_symlink():
        raise ValueError('missing original guest request receipt')
    pre=json.loads(receipt.read_text(encoding='utf-8'))
    if (pre.get('modified_sha256')!=verify.ROM_SHA or
        pre.get('save_sha256')!=verify.SAVE_SHA or
        pre.get('preconstructor_state_sha256')!=verify.PRECONSTRUCTOR_SHA or
        pre.get('request_copy_sha256')!=verify.PRIVATE_REQUEST_SHA or
        pre.get('request_copy_stores')!=44 or
        pre.get('pending_set_guest_steps')!=23):
        raise ValueError('original private request provenance mismatch')
    with tempfile.TemporaryDirectory(prefix='sg_exact_native_replay_') as folder:
        temp=Path(folder)
        raw=bytearray(host.read_bytes())
        if (struct.unpack_from('<Q',raw,0x171B88)[0]!=0x6FFFFFFB or
            struct.unpack_from('<Q',raw,0x171B90)[0]!=0x08000001):
            raise ValueError('unpinned original host ELF metadata')
        struct.pack_into('<Q',raw,0x171B90,1)
        (temp/'host.so').write_bytes(raw)
        if sha(temp/'host.so')!=LOADABLE_SHA:
            raise ValueError('unpinned temporary emulator host image')
        for source,name in ((rom,'game.gba'),(save,'game.sav'),(state,'state.ss')):
            shutil.copyfile(source,temp/name)
        subprocess.run([cc,'-std=c11','-O2','-shared','-fPIC','-Wall',
                        '-Wextra','-Werror','-pedantic',
                        str(HERE/'trace_exact_modified_autoplay.c'),
                        '-o',str(temp/'trace.so')],check=True)
        emulator=C.CDLL(str(temp/'host.so'))
        emulator.mCoreCreate.argtypes=[C.c_int]
        emulator.mCoreCreate.restype=C.c_void_p
        emulator.mCoreLoadFile.argtypes=[C.c_void_p,C.c_char_p]
        emulator.mCoreLoadFile.restype=C.c_bool
        emulator.mCoreLoadSaveFile.argtypes=[C.c_void_p,C.c_char_p,C.c_bool]
        emulator.mCoreLoadSaveFile.restype=C.c_bool
        emulator.mCoreLoadStateNamed.argtypes=[C.c_void_p,C.c_void_p,C.c_int]
        emulator.mCoreLoadStateNamed.restype=C.c_bool
        emulator.mCoreInitConfig.argtypes=[C.c_void_p,C.c_char_p]
        emulator.VFileOpen.argtypes=[C.c_char_p,C.c_int]
        emulator.VFileOpen.restype=C.c_void_p
        core=emulator.mCoreCreate(0)
        if not core:
            raise RuntimeError('mCoreCreate failed')
        def method(offset,return_type,*arg_types):
            ptr=C.c_void_p.from_address(core+offset).value
            if not ptr:
                raise RuntimeError('unknown native emulator ABI offset')
            return C.CFUNCTYPE(return_type,C.c_void_p,*arg_types)(ptr)
        method(0x12F0,None)(core)
        emulator.mCoreInitConfig(core,None)
        if not emulator.mCoreLoadFile(core,str(temp/'game.gba').encode()):
            raise RuntimeError('failed to load disposable exact ROM')
        if not emulator.mCoreLoadSaveFile(core,str(temp/'game.sav').encode(),False):
            raise RuntimeError('failed to load disposable original save')
        method(0x13D0,None)(core)
        vf=emulator.VFileOpen(str(temp/'state.ss').encode(),0)
        if not vf or not emulator.mCoreLoadStateNamed(core,vf,0):
            raise RuntimeError('original exact pending state did not load')
        cpu=C.c_void_p.from_address(core).value
        regs=(C.c_uint32*16).from_address(cpu)
        frame=method(0x1428,C.c_uint32)
        read8=method(0x1488,C.c_uint32,C.c_uint32,C.c_int)
        read16=method(0x1490,C.c_uint32,C.c_uint32,C.c_int)
        read32=method(0x1498,C.c_uint32,C.c_uint32,C.c_int)
        keys=method(0x1408,None,C.c_uint32)
        if frame(core)!=4179 or (read32(core,0x02001D2C,0)&1)==0:
            raise ValueError('original actor0 pending state mismatch')
        own=0x02001ECC
        moves=[read16(core,own+12+2*i,0) for i in range(4)]
        pp=[read8(core,own+37+i,0) for i in range(4)]
        trace=C.CDLL(str(temp/'trace.so'))
        trace.sg_exact_trace.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),
            C.c_uint32,C.c_uint64,C.POINTER(Event),C.c_uint32,C.POINTER(Stats)]
        keys(core,0) # Never scripts player move-menu input
        timeline=(Event*500)()
        stats=Stats()
        trace.sg_exact_trace(core,regs,350,45000000,timeline,500,C.byref(stats))
        if stats.count>=500:
            raise ValueError('guest event capture overflow')
        events=[]
        for i in range(stats.count):
            e=timeline[i]
            events.append(dict(
                pc=hex(e.pc),frame=e.frame,r0=e.r0,r1=e.r1,r2=e.r2,r3=e.r3,
                pending=e.pending,reply_valid=e.reply_valid,
                reply_header=e.reply_header,reply_payload=e.reply_payload))
        report=dict(
            schema=verify.SCHEMA,rom_sha256=verify.ROM_SHA,
            save_sha256=verify.SAVE_SHA,state_sha256=verify.STATE_SHA,
            host_move_menu_buttons_sent=0,emulator_rom_writes=0,
            installed_new_hook=False,provenance=pre,status=stats.status,
            trace_start_frame=stats.start_frame,trace_end_frame=stats.end_frame,
            guest_steps=stats.steps,player_moves_before=moves,player_pp_before=pp,
            player_pp_after=[read8(core,own+37+i,0) for i in range(4)],
            events=events)
        summary=verify.audit(report)
        if sha(rom)!=verify.ROM_SHA or sha(save)!=verify.SAVE_SHA or \
           sha(temp/'game.gba')!=verify.ROM_SHA:
            raise RuntimeError('original/private ROM or save identity changed')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',
                      encoding='utf-8')
    print(json.dumps(summary,indent=2,sort_keys=True))
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','rom','save','state','receipt','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cc',default='cc')
    a=p.parse_args()
    run(a.host,a.rom,a.save,a.state,a.receipt,a.output,a.cc)

if __name__=='__main__':
    main()
