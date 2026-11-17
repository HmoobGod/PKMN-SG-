#!/usr/bin/env python3
"""Generate a reproducible ARMv4T layout excerpt from PINNED v1.1.4 source.

This is a *compiled isolated-header projection*, not a full game build. It reads
only the PUBLIC developer source ZIP, checks original header SHA256, takes the
verbatim BattlePokemon declaration and volatile macro, compiles an isolated C
translation unit, and records clang's ARMv4T AST record-layout dump. Never
opens a ROM, save, or proprietary compiled game image.

The BattleStruct prefix through choicedMove is compiled from pinned source;
absolute RAM globals and the original binary are NOT certified by this projection.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

EXPECTED = {
'include/pokemon.h':'1c423000ee2c66bc349031a95080799b8a405aa0208f8ae22a65e7fd277e3615',
'include/battle.h':'a6709aac73c44eaa35ce3ceafb1bee485f8b4f9657b149a1c1f5f0a25bc4c15a',
'include/constants/battle.h':'5f900441dc42cdc7ac42dcf0fb76a8eba86dd4fc42624b863112bd191cd89ae8',
'include/constants/global.h':'062ebb16beac956774fd06e7977d3ea0db0697d4baba127fdd39d1de95b4b5a4',
'include/constants/pokemon.h':'39ff3dba81f29a4dd83bd38b19fcea5842d9e9d5aab8b286f6fa53ab5c201119',
'include/constants/abilities.h':'5f74a1af581bd53fa552faedc2901e08383dfbd59f604767ddac099df8bde6aa',
'include/constants/moves.h':'e16bd8252baac1b8736b499f55f06eed67b902ba39a43ecc14df4f10956f053e',
'include/constants/items.h':'4b2a00e4c91f09199f154024669fa9424eb05b79941fc1b7fc572bb4e3576905',
'include/config/battle.h':'e0edd48bcbb5cf3100ec9a245b6c831996a7cbea1aa70cc042905ed2c41b492b',
'include/constants/species.h':'e80ef1f6f118687037d0b3bd54740375f4a1f2126de966c24d5022c23fbaf8af',
}
PREFIX = 'soulgold-master/'


def require(ok, msg):
    if not ok:
        raise AssertionError(msg)


def extract_struct(text, name):
    hit = re.search(r'(?m)^struct '+re.escape(name)+r'\s*\{',text)
    require(hit is not None, 'struct '+name+' unavailable')
    i = hit.start(); depth = 0; opening = text.index('{',i)
    for j in range(opening,len(text)):
        if text[j]=='{':depth+=1
        if text[j]=='}':
            depth-=1
            if depth==0:
                semi=text.index(';',j)
                return text[i:semi+1]
    raise AssertionError('unterminated struct '+name)


def source(headers, clang):
    # These *verbatim* extracts are deliberately preserved in the Clang input.
    battle_pokemon = extract_struct(headers['include/pokemon.h'], 'BattlePokemon')
    battle_volatile = extract_struct(headers['include/pokemon.h'], 'Volatiles')
    battle_structs='\n'.join(extract_struct(headers['include/battle.h'],name) for name in ['Wish','FutureSight','BattlerState','PartyState','EventStates'])
    raw_bs=extract_struct(headers['include/battle.h'],'BattleStruct')
    require('u16 choicedMove[MAX_BATTLERS_COUNT];' in raw_bs, 'choicedMove field absent')
    battle_struct_prefix=raw_bs.split('u16 choicedMove[MAX_BATTLERS_COUNT];')[0]+'u16 choicedMove[MAX_BATTLERS_COUNT];\n};'
    # Because the header macro depends on many other generated game headers,
    # reproduce its expansion using the original F(...) lines verbatim and
    # documented scalar dimensions; Clang computes actual packing/offsets.
    original = headers['include/constants/battle.h']
    lines=original.splitlines(keepends=True)
    begin=next(i for i,line in enumerate(lines) if line.startswith('#define VOLATILE_DEFINITIONS(F)'))
    last=begin
    while lines[last].rstrip().endswith('\\'):
        last+=1
    volatile_macro=''.join(lines[begin:last+1])
    require('VOLATILE_TORMENT' in volatile_macro and 'VOLATILE_ENCORED_MOVE' in volatile_macro,'source volatile definitions incomplete')
    # Validate all critical constants against actual public source text.
    config=headers['include/config/battle.h']
    dims=headers['include/constants/global.h']
    for key, val in {'MAX_MON_MOVES':4,'MAX_MON_ITEMS_INTERNAL':2,'MAX_MON_INNATES_INTERNAL':3,'MAX_MON_ITEMS':1,'POKEMON_NAME_LENGTH':12,'PLAYER_NAME_LENGTH':7}.items():
        require(re.search(r'(?m)^#define\s+'+key+r'\s+'+str(val)+r'\b', dims) is not None,key+' source dimension mismatched')
    for key,val in {'B_CONFUSION_TURNS':5,'B_DISABLE_TIMER':4,'B_ENCORE_TIMER':4,'B_RAMPAGE_TURNS':3}.items():
        require(re.search(r'(?m)^#define\s+'+key+r'\s+'+str(val)+r'\b',config) is not None,key+' source config mismatch')
    for key,val in {'MOVE_ROCK_SLIDE':157,'MOVE_TAUNT':269}.items():
        require(re.search(r'(?m)^\s*'+key+r'\s*=\s*'+str(val)+r'\s*,', headers['include/constants/moves.h']) is not None,key+' source constant mismatch')
    for key,val in {'ABILITY_OBLIVIOUS':12,'ABILITY_GORILLA_TACTICS':255}.items():
        require(re.search(r'(?m)^\s*'+key+r'\s*=\s*'+str(val)+r'\s*,',headers['include/constants/abilities.h']) is not None,key+' source constant mismatch')
    for key,val in {'ITEM_CHOICE_BAND':442,'ITEM_CHOICE_SPECS':443,'ITEM_CHOICE_SCARF':444}.items():
        require(re.search(r'(?m)^\s*'+key+r'\s*=\s*'+str(val)+r'\s*,',headers['include/constants/items.h']) is not None,key+' source constant mismatch')
    require('BATTLE_TYPE_IS_MASTER          (1 << 2)' in headers['include/constants/battle.h'],'master battle flag not (1<<2)')
    require(re.search(r'(?m)^#define\s+SPECIES_DIALGA_PRIMAL\s+1577\b',headers['include/constants/species.h']) is not None,'pinned source species 1577 not found')
    # Prefix creates no game-specific structs; packed enums mirror the source.
    # Noncritical counters are dimensioned from the pinned public headers
    # and only establish sizes/bit widths, never runtime meaning.
    prelude='''
typedef unsigned char u8;
typedef signed char s8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned char bool8;
#define MAX_MON_MOVES 4
#define MAX_MON_ITEMS_INTERNAL 2
#define MAX_MON_INNATES_INTERNAL 3
#define MAX_MON_ITEMS 1
#define MAX_BATTLERS_COUNT 4
#define PARTY_SIZE 6
#define NUM_BATTLE_SIDES 2
#define NUM_BATTLE_STATS 8
#define POKEMON_NAME_LENGTH 12
#define PLAYER_NAME_LENGTH 7
#define MAX_STAT_STAGE 12
#define MAX_BITS(n) ((1U << (n)) - 1)
#define BIT_SIZE(x) (32 - __builtin_clz((unsigned int)(x)))
#define GET_TYPE(t,max) t
#define GET_MAX(t,max) max
#define TYPE_OF(tuple) GET_TYPE tuple
#define MAX_OF(tuple) GET_MAX tuple
#define UNPACK_VOLATILE_STRUCT(e, f, tuple, ...) TYPE_OF(tuple) f : BIT_SIZE(MAX_OF(tuple));
enum __attribute__((packed)) BattlerId { B_0=0,B_1=1,B_2=2,B_3=3 };
enum __attribute__((packed)) Ability { A_NONE=0,A_GORILLA=255,A_END=531 };
enum __attribute__((packed)) Move { M_NONE=0,M_TAUNT=269,M_END=1023 };
enum __attribute__((packed)) Item { I_NONE=0,I_CHOICE=442,I_END=999 };
enum __attribute__((packed)) Type { T_NONE=0,T_END=26 };
enum __attribute__((packed)) SemiInvulnerableState { S_NONE=0,SEMI_INVULNERABLE_COUNT=7 };
enum __attribute__((packed)) Stat { ST_HP=0,NUM_STATS=6 };
enum __attribute__((packed)) BattleSide { SIDE_0=0,SIDE_1=1 };
enum __attribute__((packed)) EndTurnResolutionOrder { E0=0 };
enum __attribute__((packed)) FirstTurnEventsStates { F0=0 };
enum __attribute__((packed)) FaintedActions { FA0=0 };
enum __attribute__((packed)) CancelerState { C0=0 };
enum __attribute__((packed)) BattleIntroStates { BI0=0 };
enum __attribute__((packed)) SwitchInEvents { SI0=0 };
#define UINT32_MAX 4294967295U
#define UINT8_MAX 255U
#define NUM_SPECIES 1578
#define ABILITIES_COUNT 532
#define MOVES_COUNT_ALL 936
#define B_CONFUSION_TURNS 5
#define B_RAMPAGE_TURNS 3
#define B_DISABLE_TIMER 4
#define B_ENCORE_TIMER 4
#define B_PERISH_SONG_TIMER 3
#define B_SLOW_START_TIMER 5
#define B_EMBARGO_TIMER 5
#define B_MAGNET_RISE_TIMER 5
#define B_TELEKINESIS_TIMER 3
#define B_HEAL_BLOCK_TIMER 5
#define B_LASER_FOCUS_TIMER 2
#define B_THROAT_CHOP_TIMER 2
#define B_WRAP_TURNS 7
#define B_TAUNT_TIMER 5
#define B_TORMENT_TIMER 3
#define B_SYRUP_BOMB_TIMER 3
'''
    # Non-critical packed-enum ranges are size-class surrogates. Moves count 936,
    # abilities count 532 and species count 1578 are checked from pinned headers.
    # Do not label this a full unmodified-header game build.
    out=prelude+'\n'+volatile_macro+'\n'+battle_volatile+'\n'+battle_pokemon+'\n'+battle_structs+'\n'+battle_struct_prefix+'\n'+'''
struct BattlePokemon layout_mon;
struct Volatiles layout_volatile;
char check_stride[(sizeof(struct BattlePokemon)==152) ? 1 : -1];
char check_move1[(__builtin_offsetof(struct BattlePokemon,moves[1])==14) ? 1:-1];
char check_move3[(__builtin_offsetof(struct BattlePokemon,moves[3])==18) ? 1:-1];
char check_pp1[(__builtin_offsetof(struct BattlePokemon,pp[1])==38) ? 1:-1];
char check_ability[(__builtin_offsetof(struct BattlePokemon,ability)==32) ? 1:-1];
char check_item0[(__builtin_offsetof(struct BattlePokemon,items[0])==48) ? 1:-1];
char check_item1[(__builtin_offsetof(struct BattlePokemon,items[1])==50) ? 1:-1];
char check_innate0[(__builtin_offsetof(struct BattlePokemon,innates[0])==142) ? 1:-1];
char check_innate2[(__builtin_offsetof(struct BattlePokemon,innates[2])==146) ? 1:-1];
char check_choiced[(__builtin_offsetof(struct BattleStruct,choicedMove[0])==364) ? 1:-1];
'''
    return out


def verify_enum_counts(headers, clang):
    """Compile actual pinned public enum declarations to verify their counts."""
    def extract_enum(text,name):
        match=re.search(r'enum __attribute__\(\(packed\)\)\s+'+name+r'\s*\{',text)
        require(match is not None,'packed enum not found: '+name)
        opening=text.index('{',match.start())
        closing=text.index('};',opening)
        return text[match.start():closing+2]
    raw=('\n'.join([
        extract_enum(headers['include/constants/moves.h'],'Move'),
        extract_enum(headers['include/constants/abilities.h'],'Ability'),
    ]) + '\nconst unsigned r4_actual_moves = MOVES_COUNT_ALL;\nconst unsigned r4_actual_abilities = ABILITIES_COUNT;\n')
    with tempfile.TemporaryDirectory(prefix='sg_r4_public_enums_') as td:
        path=Path(td)/'enum.c';path.write_text(raw)
        cmd=[clang,'--target=armv4t-none-eabi','-mthumb','-S','-emit-llvm',str(path),'-o','-']
        res=subprocess.run(cmd,capture_output=True,text=True)
        require(res.returncode==0,'public enum compile failed: '+res.stderr[:1000])
        for key,expected in [('r4_actual_moves',936),('r4_actual_abilities',532)]:
            m=re.search(r'@'+key+r'\s*=.*?\bi32\s+(\d+)\b',res.stdout)
            require(m is not None and int(m.group(1))==expected, f'actual pinned enum {key} must be {expected}')
    species=headers['include/constants/species.h']
    require(re.search(r'(?m)^#define\s+SPECIES_EGG\s+\(SPECIES_DIALGA_PRIMAL\s*\+\s*1\)',species) is not None,'SPECIES_EGG source expression')
    require(re.search(r'(?m)^#define\s+NUM_SPECIES\s+SPECIES_EGG\b',species) is not None,'NUM_SPECIES source expression')
    return {'moves':936,'abilities':532,'species':1578}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-zip',type=Path,required=True,help='exact public soulgold-master.zip')
    parser.add_argument('--clang',default='clang')
    parser.add_argument('--dump-out',type=Path,help='public-only Clang record dump output')
    a=parser.parse_args()
    headers={}
    with zipfile.ZipFile(a.source_zip) as z:
        for name,digest in EXPECTED.items():
            raw=z.read(PREFIX+name)
            require(hashlib.sha256(raw).hexdigest()==digest,'header SHA mismatch: '+name)
            headers[name]=raw.decode('utf8')
    verified_counts=verify_enum_counts(headers,a.clang)
    c=source(headers,a.clang)
    with tempfile.TemporaryDirectory(prefix='sg_r4_public_layout_') as t:
        path=Path(t)/'layout.c'
        path.write_text(c)
        obj=Path(t)/'layout.o'
        run=subprocess.run([a.clang,'--target=armv4t-none-eabi','-mthumb','-std=gnu11','-Xclang','-fdump-record-layouts','-c',str(path),'-o',str(obj)],capture_output=True,text=True)
        if run.returncode:
            print(run.stderr[:4000],file=sys.stderr)
            raise RuntimeError('public-source compiled layout failed')
        dump=run.stdout
    for key in ['struct BattlePokemon','struct Volatiles','struct BattleStruct','choicedMove','torment','imprison','disabledMove','encoredMove','encoredMovePos','disableTimer']:
        require(key in dump,'missing record dump detail: '+key)
    print('PASS: 10 exact original header SHA256 identities')
    print('PASS: public source enum IDs, limits, battle flags cross-checked')
    expected_layout={\
        'torment':r'88:7-7\s*\|\s*u32 torment',\
        'imprison':r'98:0-0\s*\|\s*u32 imprison',\
        'disabledMove':r'109:3-12\s*\|\s*u32 disabledMove',\
        'encoredMove':r'110:5-14\s*\|\s*u32 encoredMove',\
        'encoredMovePos':r'117:0-3\s*\|\s*u32 encoredMovePos',\
        'disableTimer':r'117:4-6\s*\|\s*u32 disableTimer',\
        'encoreTimer':r'117:7-9\s*\|\s*u32 encoreTimer',\
        'choicedMove':r'364\s*\|\s*u16\[4\] choicedMove',\
    }
    for label,pattern in expected_layout.items():
        require(re.search(pattern,dump) is not None,'ARMv4T record layout mismatch for '+label)
    print('PASS: Clang armv4t projected BattlePokemon, Volatiles, BattleStruct fields and offsets')
    print('PASS: source enum counts',verified_counts)
    print('NOTE: This is a header-derived isolated projection, not a full v1.1.4 build; BattleStruct prefix compiled, ROM globals not certified')
    print('Clang version:',subprocess.run([a.clang,'--version'],capture_output=True,text=True).stdout.splitlines()[0])
    if a.dump_out:
        a.dump_out.write_text(dump)
        print('WROTE public Clang AST record-layout dump',a.dump_out)

if __name__=='__main__':
    main()
