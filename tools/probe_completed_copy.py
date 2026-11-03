"""Optional read-only paired native copier PC trace using pinned private mGBA bridge.

Requires private mGBA bridge and runtime: NEVER links to battle command emitter.
Produces a *private local* report; no raw ROM or fixture is published.
A completed copy is NOT player ownership, move legality or auto authorization.
"""
import argparse
import ctypes as C
import datetime
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from check_copy_postloop import check_rom, ENTRY, POST_A
from verify_native_copy_pairs import validate_trace, BRIDGE_SHA, RUNTIME_SHA, SAVE_SHA, STATE_SHA

STORE_PC = 0x0806B3BE
PENDING_ADDR = 0x02001D2C
BUFFER_PTR_ADDR = 0x02001C6C
FLAGS_ADDR = 0x02001AB4


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def in_ewram(addr, count):
    return 0x02000000 <= addr and addr + count <= 0x02040000


def bind(l):
    functions = {
        'sg_open': ([C.c_char_p, C.c_char_p], C.c_int),
        'sg_load': ([C.c_char_p], C.c_int),
        'sg_read': ([C.c_uint, C.c_uint], C.c_uint),
        'sg_frames': ([C.c_uint, C.c_uint], None),
        'sg_until_external': ([C.c_uint, C.c_uint, C.c_char_p], C.c_int),
        'sg_reg': ([C.c_uint], C.c_uint),
        'sg_frame': ([], C.c_uint),
        'sg_close': ([], None),
        'sg_refresh_prefetch': ([], None),
    }
    for name, (argtypes, restype) in functions.items():
        fn = getattr(l, name)
        fn.argtypes, fn.restype = argtypes, restype


def run(args):
    # Read + pin every private input before opening or executing anything.
    identities = {key: sha(getattr(args, key)) for key in ('rom','save','state','bridge','runtime')}
    assert identities['save'] == SAVE_SHA
    assert identities['state'] == STATE_SHA
    assert identities['bridge'] == BRIDGE_SHA
    assert identities['runtime'] == RUNTIME_SHA
    assert check_rom(args.rom)['rom_variant'] == '16266'
    assert not args.output.exists(), 'never overwrite an existing report'
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        shutil.copy2(args.rom, temp/'battle.gba')
        shutil.copy2(args.save, temp/'battle.sav')
        bridge = C.CDLL(str(args.bridge.resolve()))
        bind(bridge)
        assert bridge.sg_open(str(temp/'battle.gba').encode(), str(temp/'battle.sav').encode())
        try:
            assert bridge.sg_load(str(args.state).encode())
            bridge.sg_refresh_prefetch()
            assert bridge.sg_reg(15) == 0x08065B1A and bridge.sg_reg(4) == 0
            assert bridge.sg_until_external(0x0806449C, 120, str(temp/'menu').encode())
            bridge.sg_frames(2, 0)
            # The previous pinned local runtime uses these exact debugger ABI offsets.
            base = C.cast(bridge.sg_reg, C.c_void_p).value - 0x4E50
            core = C.c_void_p.from_address(base + 0x37AA0).value
            cpu = C.c_void_p.from_address(core).value
            debug = C.c_void_p.from_address(base + 0x12288).value
            platform = C.c_void_p.from_address(debug+24).value
            assert C.c_void_p.from_address(debug+128).value == base+0x3C70
            assert list((C.c_uint*16).from_address(cpu)) == [bridge.sg_reg(i) for i in range(16)]
            mg = C.CDLL(str(args.runtime.resolve()))
            mg.mDebuggerRunFrame.argtypes = [C.c_void_p]
            mg.mDebuggerRunFrame.restype = None
            set_break = C.CFUNCTYPE(C.c_ssize_t,C.c_void_p,C.c_void_p)(
                C.c_void_p.from_address(platform+56).value)
            for address in (ENTRY, STORE_PC, POST_A):
                bp = C.create_string_buffer(32)
                C.c_uint.from_buffer(bp, 8).value = address
                C.c_int.from_buffer(bp, 12).value = -1
                assert set_break(platform,bp) >= 0

            def reg_snapshot():
                return list((C.c_uint*16).from_address(cpu))

            def read_bytes(addr, count):
                if not in_ewram(addr,count):
                    raise ValueError('untrusted native EWRAM pointer')
                return bytes(bridge.sg_read(addr+i,1) for i in range(count))

            attempts=[]
            active=[None]
            errors=[]
            callback_hits=[0]
            callback_t = C.CFUNCTYPE(None,C.c_void_p,C.c_int,C.c_void_p)
            @callback_t
            def stop_callback(debugger,reason,info):
                try:
                    if reason == 2 and info:
                        pc=C.c_uint.from_address(info).value
                        if pc not in (ENTRY,STORE_PC,POST_A):
                            return
                        callback_hits[0] += 1
                        if callback_hits[0] > 100000:
                            raise RuntimeError('probe event cap exceeded')
                        regs=reg_snapshot()
                        frame=bridge.sg_frame()
                        sp,lr=regs[13:15]
                        if pc==ENTRY:
                            actor,direction,source,count=regs[:4]
                            if actor!=0 or direction!=0 or count!=44:
                                return
                            if not in_ewram(source,44) or read_bytes(source,1)!=b'\x13':
                                return
                            if active[0] is not None:
                                raise RuntimeError('overlapping original invocation')
                            flags=bridge.sg_read(FLAGS_ADDR,4)
                            if flags & 2:
                                raise RuntimeError('link mode cannot certify this path')
                            buffer=bridge.sg_read(BUFFER_PTR_ADDR,4)
                            dest=buffer+actor*512+0x10
                            if not in_ewram(dest,44) or not (source+44<=dest or dest+44<=source):
                                raise RuntimeError('overlapping/out-of-bounds buffer')
                            # Source memory is snapshotted BEFORE any original byte-copy instructions.
                            raw=read_bytes(source,44)
                            active[0]={
                                'entry':dict(hit=callback_hits[0],pc=pc,frame=frame,actor=actor,direction=direction,
                                    source=source,destination=dest,count=count,link_flag=False,
                                    sp=sp,lr=lr,source_bytes_hex=raw.hex()),
                                'stores':[],'post':None}
                        elif pc==STORE_PC:
                            if active[0] is None:
                                return
                            x=active[0]
                            source,dest=x['entry']['source'],x['entry']['destination']
                            index=regs[1]
                            if index!=len(x['stores']) or index>=44:
                                raise RuntimeError('extra/out-of-order native store')
                            if regs[0]!=dest or regs[4]!=source:
                                raise RuntimeError('native src/dest register mismatch')
                            x['stores'].append(dict(hit=callback_hits[0],pc=pc,frame=frame,index=index,source=source,
                                dest=dest,value=regs[3]&255,sp=sp,lr=lr))
                        else:
                            if active[0] is None:
                                return
                            x=active[0]
                            source,dest=x['entry']['source'],x['entry']['destination']
                            x['post']=dict(hit=callback_hits[0],pc=pc,frame=frame,source=regs[4],dest=regs[0],
                                copied=regs[1],count=regs[2],sp=sp,lr=lr,
                                source_bytes_hex=read_bytes(source,44).hex(),
                                dest_bytes_hex=read_bytes(dest,44).hex())
                            attempts.append(x)
                            active[0]=None
                except Exception as exc:
                    errors.append(dict(error=repr(exc),frame=bridge.sg_frame(),
                                       pc=hex(pc) if 'pc' in locals() else None))
                finally:
                    C.c_int.from_address(debugger+32).value=1

            old_callback=C.c_void_p.from_address(debug+128).value
            C.c_void_p.from_address(debug+128).value=C.cast(stop_callback,C.c_void_p).value
            C.c_int.from_address(debug+32).value=1
            def frames(n,key=0):
                bridge.sg_frames(0,key)
                for _ in range(n):
                    mg.mDebuggerRunFrame(debug)
            try:
                if args.case=='cancel':
                    frames(1,2)
                    frames(180)
                    frames(1,1)
                elif args.case=='confirm':
                    frames(1,1)
                frames(1200)
            finally:
                C.c_void_p.from_address(debug+128).value=old_callback
            assert not errors,errors
            assert active[0] is None,'unfinished original byte copy; fail closed'
            assert attempts,'no positive post-copy path observed'
            report={
                'case':args.case,'started_utc':started,'hashes':identities,
                'observer_only':True,'auto_dispatch':False,'attempts':attempts,
                'reported_pairs':len(attempts),'player_ownership_proven':False,
                'move_target_authorized':False,
                'scope':'Read-only private original function entry / per-store PC / postloop trace. No request/session permission proof. No automatic commands.',
                'copy_observer_pc_hits':callback_hits[0],
                'engine_owner_certificate':False,
            }
            summary=validate_trace(report)
        finally:
            bridge.sg_close()
    assert identities == {key: sha(getattr(args,key)) for key in identities},'private input changed'
    assert not args.output.exists()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS observer-only private trace',summary)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','save','state','bridge','runtime','output'):
        parser.add_argument('--'+key,required=True,type=Path)
    parser.add_argument('--case',choices=['cancel','confirm'],default='cancel')
    run(parser.parse_args())

if __name__=='__main__':main()