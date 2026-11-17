#!/usr/bin/env python3
"""Fail-closed ARMv4T Thumb r7/callee/hook-entry auditor.

Public-only invocation checks the exact approved assembly and synthetic tests.
An optional ROM file is read in the *owner's authorized private workspace* and
never written, copied, printed as disassembly, uploaded, or embedded in output.
Raw 16-bit scans find candidates, not a whole-ROM proof of instruction reach.
Native debugger traces remain necessary for proof against indirect branches.
"""
from __future__ import annotations
import argparse
from collections import deque
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

SOURCE_SHA = 'ce8d38b718939243a99eed560d250ed30e15b29255a0b4f0c21f3cd3ced12333'
ROM_SHA = '7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32'
HOOK = 0x65ED8
MIDDLE = {0x65EDA,0x65EDC,0x65EDE}
CALLER_ENTRY = 0x65EB4
CALLER_RESUME = 0x65EE0
CALLEE_ENTRY = 0xE0748
CALLEE_CALLSITE = 0x65EE4
EXPECTED_DEFS = {0x65F04,0x65F5A}


@dataclass(frozen=True)
class Ins:
    address: int
    op: str
    args: str = ''
    width: int = 2


class UnsafeCFG(AssertionError):
    pass


def ensure(ok: bool, msg: str):
    if not ok:
        raise UnsafeCFG(msg)


def regs(s: str) -> set[str]:
    return set(re.findall(r'(?<![a-z0-9_])(?:r(?:1[0-5]|[0-9])|sp|lr|pc)(?![a-z0-9_])',s.lower()))


def rw_r7(ins: Ins) -> tuple[bool,bool]:
    """Return (reads_old_r7, writes_r7); unknown uses fail closed.

    Not a full CPU emulator. Only guards instructions relevant to predef proof.
    Two-operand arithmetic/shift reads its implicit destination operand.
    """
    op=ins.op.lower().split('.')[0]
    args=ins.args.lower()
    if 'r7' not in regs(args):
        return False,False
    if op=='push':
        return True,False
    if op=='pop':
        return False,True
    parts=[s.strip() for s in args.split(',')]
    first=parts[0] if parts else ''
    writes=first=='r7'
    if op in {'mov','movs','ldr','ldrb','ldrh','ldrsb','ldrsh','lsls','lsrs','asrs','adds','subs','and','ands','orrs','eors','bics','muls','adcs','sbcs','neg','negs','rors','uxth','uxtb','sxth','sxtb'}:
        if not writes:
            return True,False
        # For arithmetic with a Thumb-1 two-operand form, dest also input.
        implicit=(op in {'adds','subs','ands','orrs','eors','bics','muls','adcs','sbcs',
                         'lsls','lsrs','asrs','rors'} and len(parts)==2)
        read_from_rest=('r7' in set().union(*(regs(x) for x in parts[1:])))
        return implicit or read_from_rest,True
    # These are explicit read-only uses, even when r7 is the first operand.
    if op in {'str','strb','strh','cmp','cmn','tst','bx','blx'}:
        return True,False
    # Unknown op with r7: never mistake read for a pure write.
    return True,writes


def may_clobber_r1(ins: Ins) -> bool:
    """Conservatively invalidate saved-LR provenance after *any* r1 touch.

    Only proven read-only operations preserve it. Unknown instructions and
    register-list writes (including ranges such as {r0-r3}) are clobbers.
    This is intentionally stricter than full instruction semantics: false
    rejections are safe; false preservation of a return token is not.
    """
    op=ins.op.lower().split('.')[0]
    args=ins.args.lower()
    expanded=regs(args)
    # Numeric ranges inside register lists can touch r1 without spelling it.
    for m in re.finditer(r'(?<![a-z0-9_])r(\d{1,2})\s*-\s*r(\d{1,2})(?![a-z0-9_])', args):
        low,high=map(int,m.groups())
        if low<=1<=high:
            expanded.add('r1')
    if 'r1' not in expanded:
        return False
    if op in {'cmp','cmn','tst','teq','push'}:
        return False
    if op in {'str','strb','strh'}:
        # Store data and base operands are read-only *unless* writeback is used.
        return '!' in args or bool(re.search(r'\]\s*,',args))
    # Everything else touching r1 (including MVN, ROR, LDM, LDRSB, ADR,
    # unknown extensions and unclassified register-list syntax) kills proof.
    return True


def target_in_args(ins: Ins) -> int:
    hits=re.findall(r'(?<![\w])0x([0-9a-fA-F]+)',ins.args)
    ensure(len(hits)>=1, f'branch target unavailable at {ins.address:#x}')
    return int(hits[-1],16)


def edges(ins: Ins) -> tuple[list[int],bool]:
    """Bounded Thumb-1 successors; PC-relative *data* operations are NOT jumps.

    A write to PC, indirect BLX, and unrecognized control transfers abort.
    """
    op=ins.op.lower().split('.')[0]
    nx=ins.address+ins.width
    if op=='bl':
        ensure(ins.width==4, f'bad Thumb-1 BL width at {ins.address:#x}')
        return [nx],False
    if op=='blx':
        raise UnsafeCFG('unsupported BLX/ARM-state indirect calls')
    if op=='b':
        return [target_in_args(ins)],False
    if op in CONDITIONS:
        return [target_in_args(ins),nx],False
    if op=='bx':
        return [],True
    if op=='pop' and 'pc' in regs(ins.args):
        return [],True
    if op.startswith('b') and op not in {'bic','bics'}:
        raise UnsafeCFG(f'unsupported branch {op} at {ins.address:#x}')
    if 'pc' in regs(ins.args):
        parts=[v.strip() for v in ins.args.lower().split(',')]
        dest=parts[0] if parts else ''
        ensure(dest not in {'pc','r15'}, f'write to PC at {ins.address:#x}')
        # A literal LDR reads a PC-relative address, NOT program control.
        # ADR and ADD against PC produce ordinary integer addresses.
        ensure(op in {'ldr','ldrb','ldrh','add','adds','adr','cmp','cmn','tst'},
               f'unclassified PC use at {ins.address:#x}: {op}')
    return [nx],False


CONDITIONS={'beq','bne','bcs','bcc','bhs','blo','bmi','bpl',
            'bvs','bvc','bhi','bls','bge','blt','bgt','ble'}


def predef_caller(insns: dict[int,Ins]) -> tuple[set[int],set[int],set[int]]:
    pending=deque([CALLER_RESUME]); visited=set(); defs=set(); calls=set()
    while pending:
        at=pending.popleft()
        if at in visited:
            continue
        ensure(at in insns, f'caller branch leaves bounded instruction region at {at:#x}')
        visited.add(at)
        inst=insns[at]
        read,write=rw_r7(inst)
        ensure(not read, f'incoming r7 READ before definition: {at:#x} {inst.op} {inst.args}')
        if write:
            defs.add(at)
            continue
        if inst.op.lower()=='bl':
            calls.add(at)
        nexts, terminal=edges(inst)
        ensure(not terminal, f'caller exits before defining r7: {at:#x}')
        pending.extend(nexts)
    ensure(defs, 'no r7 definitions reached')
    return visited,defs,calls


def parse_reglist(ins: Ins) -> tuple[str,...]:
    """Actual ascending Thumb PUSH/POP register order, including ranges.

    A missing brace or an invalid register list must not be interpreted as
    safe stack restoration. No arbitrary SP arithmetic is modeled.
    """
    text=ins.args.strip().lower()
    ensure(text.startswith('{') and text.endswith('}'),
           f'unrecognized register list at {ins.address:#x}: {ins.args}')
    expanded=[]
    for component in text[1:-1].split(','):
        component=component.strip()
        if '-' in component:
            pair=component.split('-')
            ensure(len(pair)==2 and pair[0] in REGNUM and pair[1] in REGNUM,
                   f'invalid range at {ins.address:#x}')
            a,b=REGNUM[pair[0]],REGNUM[pair[1]]
            ensure(0<=a<=b<=7, f'invalid Thumb register range at {ins.address:#x}')
            expanded.extend(f'r{n}' for n in range(a,b+1))
        else:
            expanded.append(component)
    ensure(expanded and len(expanded)==len(set(expanded)),
           f'empty/duplicate register list at {ins.address:#x}')
    for reg in expanded:
        ensure(reg in REGNUM, f'invalid stack register {reg} at {ins.address:#x}')
    expanded.sort(key=lambda r:REGNUM[r])
    return tuple(expanded)


REGNUM={f'r{i}':i for i in range(16)}|{'sp':13,'lr':14,'pc':15}


@dataclass(frozen=True)
class CalleeFlow:
    address:int
    # Top of stack is index 0. Tokens track exact origin of saved registers.
    stack:tuple[str,...]
    r7_value:str                # incoming, worker, restored, unknown
    r1_return:str              # entry_lr_pop or none
    lr_value:str                # incoming or overwritten


def callee_r7_all_returns(insns: dict[int,Ins], entry: int) -> dict:
    """Bounded proof using stack-slot provenance, not mere POP presence.

    The only certified returns are BX LR with original LR, or BX R1 after
    popping original LR *from its exact stack slot*. All modeled return paths
    must restore the original r7, restore SP, and avoid reading incoming r7.

    Limitation: aliases of SP, stores to stack via another base register, and
    calls to unmodeled nested functions cannot be proven here: fail closed on
    an explicit SP store/adjustment or nested BL. Native proof remains open.
    """
    ensure(entry in insns, 'callee entry missing')
    q=deque([CalleeFlow(entry,(), 'incoming','none','incoming')])
    seen=set();returns=set();calls=set(); MAX_STATES=8192; MAX_STACK=64
    while q:
        state=q.popleft()
        if state in seen:continue
        seen.add(state)
        ensure(len(seen)<=MAX_STATES, 'callee CFG state space exceeded bound')
        at=state.address
        ensure(at in insns, f'callee escape/unparsed direct branch: {at:#x}')
        inst=insns[at];op=inst.op.lower().split('.')[0]
        stack=state.stack; r7=state.r7_value
        r1_ret=state.r1_return; lr=state.lr_value
        if at==entry:
            ensure(op=='push', 'callee prologue does not save incoming r7')
        if op in {'push','pop'}:
            selected=parse_reglist(inst)
            if op=='push':
                ensure(set(selected) <= (set(f'r{i}' for i in range(8))|{'lr'}),
                       f'unsupported Thumb PUSH register at {at:#x}')
                if at==entry:
                    ensure({'r7','lr'}<=set(selected),'callee entry must save incoming r7 and lr')
                elif 'r7' in selected:
                    ensure(r7=='worker',f'nested push of non-worker r7 at {at:#x}')
                token=[]
                for reg in selected:
                    if reg=='r7': token.append('entry_r7' if r7=='incoming' else 'worker_r7')
                    elif reg=='lr': token.append('entry_lr' if lr=='incoming' else 'modified_lr')
                    elif reg=='r1': token.append('from_lr_pop' if r1_ret=='entry_lr_pop' else 'unknown')
                    else:token.append('unknown')
                stack=tuple(token)+stack
                ensure(len(stack)<=MAX_STACK, 'unbounded stack depth')
            else:
                ensure(set(selected) <= (set(f'r{i}' for i in range(8))|{'pc'}),
                       f'unsupported Thumb POP register at {at:#x}')
                ensure('pc' not in selected,
                       f'POP into PC unmodeled for this callee at {at:#x}')
                ensure(len(stack)>=len(selected),f'POP unbalanced stack at {at:#x}')
                taken=stack[:len(selected)];stack=stack[len(selected):]
                for reg,token in zip(selected,taken):
                    if reg=='r7':
                        # Only the *original* entry r7 token restores r7.
                        r7= ('restored' if token=='entry_r7' else
                             'worker' if token=='worker_r7' else 'unknown')
                    elif reg=='r1':
                        r1_ret='entry_lr_pop' if token=='entry_lr' else 'none'
        elif op=='bl':
            # Nested BL may inspect r7 or clobber LR; do not assume ABI safety.
            raise UnsafeCFG(f'nested callee BL requires separate callee proof: {at:#x}')
        elif op=='blx':
            raise UnsafeCFG(f'callee BLX requires separate ARM/Thumb proof: {at:#x}')
        elif op=='bx':
            target=inst.args.strip().lower()
            ensure(target in {'lr','r1'},f'unsupported BX target {target} at {at:#x}')
            ensure(r7=='restored',f'callee return lacks original r7 restoration at {at:#x}')
            ensure(not stack,f'callee return has unbalanced SP at {at:#x}')
            ensure((target=='lr' and lr=='incoming') or
                   (target=='r1' and r1_ret=='entry_lr_pop'),
                   f'callee return target lacks original LR provenance at {at:#x}')
            returns.add(at)
            continue
        else:
            # Never claim stack preservation through arbitrary SP arithmetic.
            as_regs=regs(inst.args)
            ensure(not (op in {'add','adds','sub','subs','mov','movs','ldr','ldrb',
                               'ldrh','str','strb','strh','stm','stmia','ldm','ldmia'}
                        and ('sp' in as_regs or '[r13' in inst.args.lower())),
                   f'unmodeled SP/stack memory operation at {at:#x}')
            reads,writes=rw_r7(inst)
            if writes:
                ensure(not reads,f'callee writes r7 but reads old value: {at:#x}')
                ensure(r7!='restored','callee modifies restored r7 before return')
                r7='worker'
            elif reads:
                ensure(r7=='worker',f'callee reads incoming/restored r7 at {at:#x}')
            # Denylist-by-default: only positively recognized r1 read-only
            # instructions retain the original saved-LR return token.
            if may_clobber_r1(inst):
                r1_ret='none'
            parts=[v.strip() for v in inst.args.lower().split(',')]
            if parts and parts[0]=='lr' and op in {'mov','movs','ldr','add','adds'}:
                lr='overwritten'
        successors,terminal=edges(inst)
        ensure(not terminal,f'unmodeled callee terminal at {at:#x}')
        for nx in successors:
            q.append(CalleeFlow(nx,stack,r7,r1_ret,lr))
    ensure(returns,'callee has no independently reached return path')
    return {'visited_count':len({x.address for x in seen}),
            'return_addresses':sorted(returns),'bl_calls':sorted(calls),
            'states_visited':len(seen)}


def thumb16_branch_target(word: int, file_addr: int) -> int|None:
    """Decode only 16-bit unconditional/conditional B; no data/code judgment."""
    op=word >> 11
    if op==0b11100:
        d=word&0x7ff
        if d&0x400: d-=0x800
        return file_addr+4+2*d
    if (word&0xf000)==0xd000:
        cc=(word>>8)&0xf
        if cc>=14: return None  # SVC/undefined are not conditional B
        d=word&0xff
        if d&0x80: d-=0x100
        return file_addr+4+2*d
    return None


def thumb_bl_target(h1:int,h2:int,file_addr:int) -> int|None:
    if (h1&0xf800)!=0xf000 or (h2&0xf800)!=0xf800:return None
    v=((h1&0x7ff)<<12)|((h2&0x7ff)<<1)
    if v&(1<<22):v-=1<<23
    return file_addr+4+v


def raw_incoming_hits(blob:bytes, start:int, targets:set[int]) -> list[tuple[int,int,str]]:
    """Potential direct hits; raw halfwords could include data. NOT CFG proof."""
    hits=[]
    for offset in range(0,len(blob)-1,2):
        addr=start+offset
        h1=int.from_bytes(blob[offset:offset+2],'little')
        t=thumb16_branch_target(h1,addr)
        if t in targets:hits.append((addr,t,'thumb16-raw'))
        if offset+3<len(blob):
            h2=int.from_bytes(blob[offset+2:offset+4],'little')
            t=thumb_bl_target(h1,h2,addr)
            if t in targets:hits.append((addr,t,'thumb-BL-raw'))
    return hits


def direct_cfg_incoming(insns:dict[int,Ins],targets:set[int]) -> list[tuple[int,int,str]]:
    out=[]
    for addr,ins in insns.items():
        op=ins.op.lower().split('.')[0]
        if op=='b' or op in {'beq','bne','bcs','bcc','bhs','blo','bmi','bpl','bvs','bvc','bhi','bls','bge','blt','bgt','ble'}:
            target=target_in_args(ins)
            if target in targets:out.append((addr,target,op))
    return sorted(out)


def require_no_unvetted_hook_branches(hits: list[tuple[int,int,str]]) -> None:
    """Reject ALL unclassified direct branches into the veneer ENTRY or MIDDLE.

    Raw candidates include possible data/literal bytes: failing closed does NOT
    prove a candidate is executable or unsafe. Independent classification is
    required rather than silently ignoring it.
    """
    for from_addr,to_addr,kind in hits:
        if to_addr in MIDDLE:
            raise UnsafeCFG(f'branch enters overwritten veneer middle {to_addr:#x} from {from_addr:#x} ({kind})')
        if to_addr == HOOK:
            raise UnsafeCFG(f'branch directly enters hook at {HOOK:#x} from {from_addr:#x}; r4/r6 provenance unproved')


def hook_entry_gate(caller: dict[int,Ins], raw_blob: bytes, raw_start: int=0) -> dict:
    """Shared production and synthetic end-to-end branch gate.

    Any whole-image raw 16-bit B/conditional B or Thumb BL hit is rejected;
    data hits are deliberately NOT silently accepted. ARM/indirect hits remain
    outside this scanner's coverage and demand separate native evidence.
    """
    targets={HOOK}|MIDDLE
    known=direct_cfg_incoming(caller,targets)
    raw=raw_incoming_hits(raw_blob,raw_start,targets)
    require_no_unvetted_hook_branches(known+raw)
    return {'parsed_direct_count':len(known),'raw_candidate_count':len(raw)}


def visited_address_sha256(visited:set[int]) -> str:
    """Hash a canonical uppercase guest-address list, never private code."""
    lines=''.join(f'0x{0x08000000+off:08X}\n' for off in sorted(visited))
    return hashlib.sha256(lines.encode('ascii')).hexdigest()


def analyze_bounded_fixture(caller:dict[int,Ins],callee:dict[int,Ins],
                            synthetic_blob:bytes,raw_start:int=0)->dict:
    """Executable shared pipeline on caller/callee CFG + arbitrary synthetic bytes.

    This is not a ROM authenticity check; --rom mode additionally pins the ROM.
    """
    visited,defs,calls=predef_caller(caller)
    callee_report=callee_r7_all_returns(callee,CALLEE_ENTRY)
    gate=hook_entry_gate(caller,synthetic_blob,raw_start)
    return {'visited_count':len(visited),'visited_digest':visited_address_sha256(visited),
            'defs':sorted(defs),'calls':sorted(calls),'callee':callee_report,'branches':gate}


def decode_objdump(text:str,base_file:int,region_size:int)->dict[int,Ins]:
    records={}
    for line in text.splitlines():
        m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{4}(?:\s+[0-9a-f]{4})?)\s+([a-z][a-z0-9.]*)\s*(.*)',line)
        if not m:continue
        off=int(m.group(1),16)
        if off>=region_size:continue
        op=m.group(3);width=4 if op=='bl' else 2
        args=m.group(4).split('@')[0].strip()
        # Branch targets printed object-locally must be adjusted to file addresses
        if op=='b' or op in {'beq','bne','bcs','bcc','bhs','blo','bmi','bpl','bvs','bvc','bhi','bls','bge','blt','bgt','ble'}:
            args=re.sub(r'(?<!\w)0x([0-9a-f]+)',lambda hit:hex(int(hit.group(1),16)+base_file),args)
        records[off+base_file]=Ins(off+base_file,op,args,width)
    return records


def disassemble_thumb_private(rom:bytes,start:int,end:int,clang:str,objdump:str,td:Path)->dict[int,Ins]:
    require_range=(0<=start<end<=len(rom) and start%2==0)
    ensure(require_range,'ROM window invalid')
    binpath=td/'private_ramless_window.bin';binpath.write_bytes(rom[start:end])
    src=td/'window.s'
    src.write_text('.syntax unified\n.cpu arm7tdmi\n.thumb\n.section .text.audit,"ax",%progbits\n.global audit\n.thumb_func\naudit:\n'
                  f'.incbin "{binpath}"\n')
    obj=td/'window.o'
    subprocess.run([clang,'--target=armv4t-none-eabi','-mthumb','-c',str(src),'-o',str(obj)],check=True,capture_output=True)
    out=subprocess.run([objdump,'-d','--triple=thumbv4t-none-eabi',str(obj)],check=True,capture_output=True,text=True).stdout
    return decode_objdump(out,start,end-start)


def private_rom_analysis(path:Path,clang:str,objdump:str):
    rom=path.read_bytes()
    ensure(len(rom)==0x2000000 and hashlib.sha256(rom).hexdigest()==ROM_SHA,'protected-ROM identity mismatch')
    with tempfile.TemporaryDirectory(prefix='sg_r4_private_audit_') as temp:
        td=Path(temp)
        caller=disassemble_thumb_private(rom,CALLER_ENTRY,0x66000,clang,objdump,td)
        callee=disassemble_thumb_private(rom,CALLEE_ENTRY,CALLEE_ENTRY+0x80,clang,objdump,td)
        visited,defs,calls=predef_caller(caller)
        ensure(defs==EXPECTED_DEFS, 'caller r7 definition frontier unexpected')
        ensure(calls=={CALLEE_CALLSITE}, 'caller BL calls before definition unexpected')
        ensure(len(visited)==66, 'expected 66 caller addresses')
        b1=int.from_bytes(rom[CALLEE_CALLSITE:CALLEE_CALLSITE+2],'little')
        b2=int.from_bytes(rom[CALLEE_CALLSITE+2:CALLEE_CALLSITE+4],'little')
        ensure(thumb_bl_target(b1,b2,CALLEE_CALLSITE)==CALLEE_ENTRY,'callee branch target unexpected')
        summary=callee_r7_all_returns(callee,CALLEE_ENTRY)
        gate=hook_entry_gate(caller,rom,0)  # any raw hit now FAILS CLOSED
        digest=visited_address_sha256(visited)
    print('READ-ONLY PRIVATE CFG: caller first-r7 defs',len(defs),'predef nodes',len(visited),'BL',len(calls))
    print('READ-ONLY PRIVATE CALLEE: analyzed nodes',summary['visited_count'],'modeled returns',len(summary['return_addresses']))
    print('READ-ONLY PRIVATE ADDRESS-ONLY VISITED SHA256:',digest)
    print('HOOK DIRECT CFG CANDIDATES:',gate['parsed_direct_count'])
    print('HOOK RAW BRANCH CANDIDATES:',gate['raw_candidate_count'])
    print('LIMIT: no indirect BX/ARM-state/global execution proof and no native emulator trace; formal 0/20')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,default=Path(__file__).with_name('player_taunt_recovery_choice_gorilla_r4.s'))
    p.add_argument('--selftest',action='store_true',help='run source-only synthetic regression suite')
    p.add_argument('--rom',type=Path,help='OPTIONAL owner-authorized private, read-only; never used in source-only mode')
    p.add_argument('--clang',default='clang')
    p.add_argument('--objdump',default='llvm-objdump')
    a=p.parse_args()
    ensure(hashlib.sha256(a.source.read_bytes()).hexdigest()==SOURCE_SHA,'approved R4 source mismatch')
    if a.selftest:
        subprocess.run(['python3','-m','unittest','-v','test_r4_source_only_repairs.py'],
                       check=True,cwd=Path(__file__).resolve().parent)
        # Historical address-only metadata, NOT a new ROM scan or native trace.
        packet=json.loads(Path(__file__).with_name('R4_R7_VISITED_ADDRESSES_ONLY.json').read_text())
        addrs=[int(v,16)-0x08000000 for v in packet['visited_original_guest_addresses']]
        ensure(len(addrs)==66 and len(set(addrs))==66,'historical visited metadata invalid')
        print('HISTORICAL SOURCE-ONLY ADDRESS LIST: 66 entries')
        print('HISTORICAL SOURCE-ONLY ADDRESS DIGEST:',visited_address_sha256(set(addrs)))
        print('LIMIT: address metadata is NOT a fresh private-ROM or native gameplay trace')
        return
    print('PASS: R4 exact unchanged assembly SHA')
    if a.rom:private_rom_analysis(a.rom,a.clang,a.objdump)
    else:print('SKIP: ROM-specific CFG and callee verification (not authorized/reproduced here)')

if __name__=='__main__':
    main()
