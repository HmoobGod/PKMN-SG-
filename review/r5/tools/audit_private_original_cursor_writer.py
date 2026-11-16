#!/usr/bin/env python3
"""Fail-closed audit of a PRIVATE original-ROM move-cursor store trace.

No ROM/save/memory data is embedded in this source. All run inputs stay in a
private local folder; output contains only bounded confirmation and counts.
Source-to-C identity, move legality, automatic intent, manual fallback, and
native acceptance are NEVER certified by this tool.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROM_START=0x08000000
ROM_SIZE=0x2000000
CURSOR_POINTER_ADDR=0x02001E90
SLOT_OFFSET=0x106
TARGET_OFFSET=0x10A
STORE_SLOT_PC=0x0801862E
STORE_TARGET_PC=0x08016FB6
INIT_PTR_PC=0x080F8438
CLEAR_PTR_PC=0x080F85DA
SELECTOR_CALL_PC=0x08018620
SELECTOR_PC=0x080183F0


def thumb_bl(rom, pc):
    if not isinstance(rom,(bytes,bytearray,memoryview)) or len(rom)!=ROM_SIZE:
        return None
    off=pc-ROM_START
    if off<0 or off+4>len(rom) or off%2:
        return None
    hi=int.from_bytes(rom[off:off+2],"little")
    lo=int.from_bytes(rom[off+2:off+4],"little")
    if (hi & 0xf800)!=0xf000 or (lo & 0xf800)!=0xf800:
        return None
    disp=((hi&0x7ff)<<12)|((lo&0x7ff)<<1)
    if disp&0x400000:disp-=0x800000
    return (pc+4+disp)&0xffffffff


def check_rom(rom):
    if not isinstance(rom,(bytes,bytearray,memoryview)) or len(rom)!=ROM_SIZE:
        return False
    def h(pc):
        return int.from_bytes(rom[pc-ROM_START:pc-ROM_START+2],"little")
    return (h(STORE_SLOT_PC)==0x7018 and h(STORE_TARGET_PC)==0x7018
            and thumb_bl(rom,SELECTOR_CALL_PC)==SELECTOR_PC
            and h(0x08018624)==0x4B35 and h(0x08018626)==0x681A
            and h(0x08018628)==0x1913 and h(0x0801862A)==0x3307
            and h(0x0801862C)==0x33FF)


def is_byte(x):return type(x) is int and 0<=x<=255

def parse_hex(s):
    if type(s) is not str or len(s)!=10 or not s.startswith('0x'):
        raise ValueError('bad fixed-width hexadecimal field')
    try:return int(s[2:],16)
    except ValueError:raise ValueError('bad fixed-width hexadecimal field') from None


def in_ram_pointer(p):return 0x02000000<=p<=0x0203FEF5 and not(p&1)


def audit(events, rom_ok=True):
    if type(events) is not list or len(events)>4005 or type(rom_ok) is not bool:
        raise ValueError('invalid event array')
    ptr=0
    counts={'pointer_initialized':0,'pointer_cleared':0,'slot_stores':0,
            'target_stores':0,'changed_slot_stores':0,'changed_target_stores':0}
    last_f=-1;summary=None;invalid=0;seen={"pointer":False,"slot":False,"target":False}
    for e in events:
        if type(e) is not dict or type(e.get('event')) is not str:
            raise ValueError('invalid event row')
        kind=e['event']
        if kind=='cursor_sample_change':
            if type(e.get('f')) is not int or e['f']<0:
                raise ValueError('bad sample time')
            continue # samples are not writer provenance
        if kind=='cursor_trace_summary':
            if summary is not None:raise ValueError('duplicate summary')
            summary=e
            continue
        if kind!='cursor_store':raise ValueError('unknown event kind')
        if summary is not None:raise ValueError('store after terminal summary')
        f=e.get('f')
        if type(f) is not int or f<0 or f<last_f:
            raise ValueError('nonmonotonic original CPU event order')
        last_f=f
        ckind=e.get('kind')
        if ckind not in ('pointer','slot','target'):
            raise ValueError('unknown cursor store category')
        try:
            pc=parse_hex(e['pc']);dst=parse_hex(e['address'])
            b=parse_hex(e['ptr_before']);a=parse_hex(e['ptr_after'])
            parse_hex(e['lr'])
        except KeyError:raise ValueError('missing required CPU identity') from None
        width=e.get('width'); thumb=e.get('thumb');value=e.get('value')
        r=e.get('regs');slot_before=e.get('slot_before');slot_after=e.get('slot_after')
        target_before=e.get('target_before');target_after=e.get('target_after')
        if width not in (1,4) or type(width) is not int or thumb!=1 or type(thumb) is not int or type(value) is not int or not 0<=value<=0xffffffff or (type(r) is not list or len(r)!=8 or any(type(v) is not int or not 0<=v<=0xffffffff for v in r)):
            raise ValueError('invalid CPU store schema')
        if type(slot_before) is not int or type(slot_after) is not int or type(target_before) is not int or type(target_after) is not int:
            raise ValueError('invalid cursor values')
        if ckind=='pointer':
            if dst!=CURSOR_POINTER_ADDR or width!=4 or b!=ptr or value!=a:
                raise ValueError('inconsistent pointer store')
            if pc==INIT_PTR_PC and ptr==0 and in_ram_pointer(a) and slot_before==-1 and target_before==-1 and 0<=slot_after<=3 and 0<=target_after<=3 and r[0]==a:
                counts['pointer_initialized']+=1
            elif pc==CLEAR_PTR_PC and ptr!=0 and a==0 and slot_after==-1 and target_after==-1 and 0<=slot_before<=3 and 0<=target_before<=3:
                counts['pointer_cleared']+=1
            else:raise ValueError('not a recognized pointer lifecycle edge')
            ptr=a
        elif ckind=='slot':
            if (pc!=STORE_SLOT_PC or width!=1 or not in_ram_pointer(ptr)
                or b!=ptr or a!=ptr or dst!=ptr+SLOT_OFFSET or r[3]!=dst
                or r[4]!=0 or (value&0xff)!=r[0]&0xff or not is_byte(value)
                or not 0<=slot_before<=3 or not 0<=slot_after<=3 or slot_after!=value
                or not 0<=target_before<=3 or target_after!=target_before):
                raise ValueError('slot store source/address mismatch')
            counts['slot_stores']+=1
            if slot_before!=slot_after:counts['changed_slot_stores']+=1
        else:
            if (pc!=STORE_TARGET_PC or width!=1 or not in_ram_pointer(ptr)
                or b!=ptr or a!=ptr or dst!=ptr+TARGET_OFFSET or r[3]!=dst
                or (value&0xff)!=(r[0]&0xff) or not is_byte(value)
                or not 0<=target_before<=3 or not 0<=target_after<=3 or target_after!=value
                or not 0<=slot_before<=3 or slot_after!=slot_before):
                raise ValueError('target store source/address mismatch')
            counts['target_stores']+=1
            if target_before!=target_after:counts['changed_target_stores']+=1
    if summary is None:raise ValueError('missing trace summary')
    for key in ('stores','pointer_writes','slot_writes','valid_samples'):
        if type(summary.get(key)) is not int or summary[key]<0:
            raise ValueError('invalid summary counters')
    count_total=counts['pointer_initialized']+counts['pointer_cleared']+counts['slot_stores']+counts['target_stores']
    if summary['stores']!=count_total or summary['pointer_writes']!=counts['pointer_initialized']+counts['pointer_cleared'] or summary['slot_writes']!=counts['slot_stores']:
        raise ValueError('missing/unattributed original stores')
    return {'schema':'sg-private-actor0-cursor-original-writer-r4-unverified',
            'exact_rom_static_writer_path_verified':bool(rom_ok),
            'private_cpu_store_rows_schema_and_source_valid':True,
            'pointer_initializations':counts['pointer_initialized'],
            'pointer_clears':counts['pointer_cleared'],
            'original_player0_slot_store_candidates':counts['slot_stores'],
            'slot_changes':counts['changed_slot_stores'],
            'original_target_store_candidates':counts['target_stores'],
            'target_changes':counts['changed_target_stores'],
            'selector_returns_value_to_slot_writer_candidate':bool(rom_ok and counts['slot_stores']>0),
            'actual_taunt_failure_root_cause_certified':False,
            'original_engine_one_use_request_certified':False,
            'dynamic_move_and_target_legality_certified':False,
            'manual_fallback_certified':False,
            'no_forced_switch_certified':False,
            'exact_source_to_rom_build_identity_certified':False,
            'original_native_acceptance_scenarios':0,
            'production_authorized':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--private-rom',type=Path,required=True)
    ap.add_argument('--expected-rom-sha256',required=True)
    ap.add_argument('--private-cursor-log',type=Path,required=True)
    args=ap.parse_args()
    rom=args.private_rom.read_bytes()
    if hashlib.sha256(rom).hexdigest()!=args.expected_rom_sha256.lower():
        raise SystemExit('ROM fingerprint mismatch')
    if not check_rom(rom):raise SystemExit('exact-ROM cursor instruction gate failed')
    data=[json.loads(x) for x in args.private_cursor_log.read_text().splitlines()]
    result=audit(data,True)
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':main()
