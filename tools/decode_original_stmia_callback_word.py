#!/usr/bin/env python3
"""Read-only Thumb-1 STMIA callback-word candidate, copied conservatively
from the separately reviewed PR82 public decoder research. No ROM access.
"""

def original_thumb_stmia_word_at(opcode, registers, watched_address):
    if type(opcode) is not int or not 0 <= opcode <= 0xFFFF:
        raise ValueError("invalid original Thumb opcode")
    if (type(registers) not in (tuple,list) or len(registers)!=8 or
        any(type(r) is not int or not 0 <= r <= 0xFFFFFFFF for r in registers)):
        raise ValueError("invalid original CPU low-register snapshot")
    if type(watched_address) is not int or not 0 <= watched_address <= 0xFFFFFFFF:
        raise ValueError("invalid original watched callback address")
    if (opcode & 0xF800)!=0xC000:
        return None  # STMIA only, never LDMIA or other load/store
    base_register=(opcode>>8)&7
    register_mask=opcode&255
    if register_mask==0 or register_mask&(1<<base_register):
        return None  # no registers or ambiguous base-register writeback
    base=registers[base_register]
    if (base&3)!=0 or base+4*(register_mask.bit_count()-1)>0xFFFFFFFC:
        return None  # misalignment, overflow or address wrap
    index=0
    for r in range(8):
        if register_mask&(1<<r):
            if base+4*index==watched_address:
                return registers[r]
            index+=1
    return None
