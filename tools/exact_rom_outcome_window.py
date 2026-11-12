#!/usr/bin/env python3
"""Read-only, fail-closed byte-window preflight; never grants native gameplay acceptance."""
import argparse, hashlib, json
from pathlib import Path
EXACT = "4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44"
PROTECTED = "7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32"
STORE_PC = 0x0808E336
def inspect(path, before=128, after=64):
    path=Path(path)
    with path.open("rb") as stream:
        digest=hashlib.file_digest(stream,"sha256").hexdigest()
    if digest == PROTECTED: raise ValueError("refuse protected Current ROM")
    if digest != EXACT: raise ValueError("wrong exact modified ROM identity")
    if path.stat().st_size != 33554432: raise ValueError("wrong size")
    if min(before,after)<0 or before%2 or after%2 or after<2: raise ValueError("invalid halfword window")
    offset=STORE_PC-0x08000000
    with path.open("rb") as stream:
        stream.seek(offset)
        if stream.read(2)!=bytes.fromhex("6254"): raise ValueError("wrong store opcode")
        stream.seek(offset-before)
        data=stream.read(before+after)
    return {"classification":"STATIC_ONLY_NOT_OUTCOME_BRANCH_EVIDENCE",
            "sha256":digest,"store_pc":hex(STORE_PC),
            "halfwords":[{"pc":hex(STORE_PC-before+i),"le":data[i:i+2].hex()}
                for i in range(0,len(data),2)],
            "next":"GDB same-replay branch/flags/PC witness required"}
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("rom")
    a.add_argument("--before",type=int,default=128)
    a.add_argument("--after",type=int,default=64)
    v=a.parse_args()
    print(json.dumps(inspect(v.rom,v.before,v.after),indent=2))
