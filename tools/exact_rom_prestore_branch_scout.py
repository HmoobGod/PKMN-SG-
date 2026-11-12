#!/usr/bin/env python3
"""SHA-locked, read-only static Thumb16 pre-store branch scout. NOT an outcome witness."""
import argparse,hashlib,json
from pathlib import Path
EXACT_ROM="4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
PROTECTED_ROM="7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
ROM_SIZE=33554432
ROM_BASE=0x08000000
STORE_PC=0x0808e336
WINDOW_START,WINDOW_END=0x0808e310,0x0808e378
def conditional_target(pc,opcode):
    if (opcode & 0xf000)!=0xd000 or ((opcode>>8)&15)>=14:return None
    imm=opcode&255
    return (pc+4+(((imm^128)-128)*2))&0xffffffff
def inspect(path):
    path=Path(path)
    with path.open("rb") as f: digest=hashlib.file_digest(f,"sha256").hexdigest()
    if digest==PROTECTED_ROM:raise ValueError("protected Current ROM refused")
    if digest!=EXACT_ROM:raise ValueError("wrong exact modified-ROM identity")
    if path.stat().st_size!=ROM_SIZE:raise ValueError("wrong ROM size")
    with path.open("rb") as f:
        f.seek(WINDOW_START-ROM_BASE);code=f.read(WINDOW_END-WINDOW_START)
    if len(code)!=(WINDOW_END-WINDOW_START):raise ValueError("truncated code window")
    def opcode(pc):return int.from_bytes(code[pc-WINDOW_START:pc-WINDOW_START+2],"little")
    if opcode(STORE_PC)!=0x5462:raise ValueError("store opcode mismatch")
    for pc,word in ((0x0808e31a,0xd023),(0x0808e322,0xd11c)):
        if opcode(pc)!=word:raise ValueError("pre-store instruction mismatch")
    branches=[]
    for pc in range(WINDOW_START,STORE_PC,2):
        op=opcode(pc);target=conditional_target(pc,op)
        if target is not None:branches.append({"pc":hex(pc),"opcode":hex(op),"static_target":hex(target)})
    return {"classification":"STATIC_BRANCH_BYTES_NOT_OUTCOME_DECISION","rom_sha256":digest,
            "verified_prior_store_pc":hex(STORE_PC),"pre_store_branches":branches,
            "historical_pp_1":"UNCLASSIFIED","historical_pp_2":"UNCLASSIFIED",
            "formal_native_acceptance":"0/20"}
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("rom");args=parser.parse_args()
    print(json.dumps(inspect(args.rom),indent=2))
