"""Static path check for a prospective non-link buffer-A post-copy witness.

Reads a user-supplied, SHA-pinned private ROM; no ROM bytes are shipped,
emulated, modified or authorized for automatic execution.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

BASE, ENTRY, POST_A, END = 0x08000000, 0x0806B370, 0x0806B3C6, 0x0806B3D8
WINDOW_SHA = 'c3d3181837d0aaf69fc471c4f5598870257c622c81bca9771a5d96d45850ab57'
ROM_HASHES = {
    'Current': '7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32',
    '16266': '6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de',
}


class ShapeError(ValueError):
    pass


def require(ok, msg):
    if not ok:
        raise ShapeError(msg)


def sign_extend(value, bits):
    assert 0 <= value < (1 << bits)
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def conditional_target(hw, pc):
    require((hw & 0xF000) == 0xD000 and (hw & 0x0F00) < 0x0E00,
            f'not Thumb conditional branch at {pc:#x}')
    return (hw >> 8) & 15, pc + 4 + 2 * sign_extend(hw & 255, 8)


def unconditional_target(hw, pc):
    require((hw & 0xF800) == 0xE000, f'not Thumb B at {pc:#x}')
    return pc + 4 + 2 * sign_extend(hw & 0x7FF, 11)


def literal_target(hw, pc):
    require((hw & 0xF800) == 0x4800, f'not Thumb literal LDR at {pc:#x}')
    return ((pc + 4) & ~3) + 4 * (hw & 255)


def window_from_rom(rom):
    require(len(rom) >= END - BASE, 'short ROM')
    return rom[ENTRY - BASE:END - BASE]


def verify_native_window(window, check_hash=True):
    require(len(window) == END - ENTRY, 'wrong native window size')
    digest = hashlib.sha256(window).hexdigest()
    if check_hash:
        require(digest == WINDOW_SHA, 'pinned native window SHA mismatch')

    def h(pc):
        i = pc - ENTRY
        require(0 <= i <= len(window) - 2 and i % 2 == 0, 'bad halfword offset')
        return struct.unpack_from('<H', window, i)[0]

    def w(pc):
        i = pc - ENTRY
        require(0 <= i <= len(window) - 4 and i % 4 == 0, 'bad literal offset')
        return struct.unpack_from('<I', window, i)[0]

    # Conditions: MI=4, EQ=0, NE=1, LT=11, GT=12.
    for pc, cond, dest in [
        (0x806B37C, 4, 0x806B3C8),  # link takes alternate path
        (0x806B380, 0, 0x806B3AC),  # direction=0
        (0x806B384, 1, 0x806B3A6),  # invalid direction
        (0x806B388, 0, 0x806B3A6),  # zero B length
        (0x806B3A4, 11, 0x806B39C),  # B loop
        (0x806B3AE, 0, 0x806B3A6),  # zero A length
        (0x806B3C4, 12, 0x806B3BC),  # A loop
    ]:
        require(conditional_target(h(pc), pc) == (cond, dest),
                f'conditional path drift at {pc:#x}')
    for pc, dest in [(0x806B3C6, 0x806B3A6),
                     (0x806B3CE, 0x806B3A6)]:
        require(unconditional_target(h(pc), pc) == dest,
                f'unconditional path drift at {pc:#x}')

    # Decode operand shapes, not copied instruction-byte dumps.
    def shift(pc, rd, rm, amount):
        v = h(pc)
        require((v >> 11) == 0 and (v & 7) == rd and
                ((v >> 3) & 7) == rm and ((v >> 6) & 31) == amount,
                f'shift operand drift at {pc:#x}')

    def imm(pc, op, reg, value):
        v = h(pc)
        require((v & 0xF800) == op and ((v >> 8) & 7) == reg
                and (v & 255) == value, f'immediate operand drift at {pc:#x}')

    def byte_access(pc, load, base, index, data):
        v = h(pc)
        require((v & 0xFE00) == (0x5C00 if load else 0x5400)
                and ((v >> 6) & 7) == index
                and ((v >> 3) & 7) == base and (v & 7) == data,
                f'byte copy operand drift at {pc:#x}')

    def cmp_regs(pc, rd, rm):
        v = h(pc)
        require((v & 0xFC00) == 0x4000 and ((v >> 6) & 15) == 10
                and ((v >> 3) & 7) == rm and (v & 7) == rd,
                f'compare operand drift at {pc:#x}')

    require((h(0x806B370) & 0xFFFF) == 0xB510, 'wrong prologue shape')
    shift(0x806B374, 2, 3, 0)
    shift(0x806B37A, 3, 3, 30)
    imm(0x806B37E, 0x2800, 1, 0)
    imm(0x806B382, 0x2800, 1, 1)
    imm(0x806B3AC, 0x2800, 2, 0)
    shift(0x806B3B4, 0, 0, 9)
    imm(0x806B3B8, 0x3000, 0, 16)
    for pc in (0x806B3BC, 0x806B39C):
        byte_access(pc, True, 4, 1, 3)
        byte_access(pc + 2, False, 0, 1, 3)
        imm(pc + 4, 0x3000, 1, 1)
    cmp_regs(0x806B3C2, 2, 1)
    cmp_regs(0x806B3A2, 1, 2)
    require(h(0x806B3A6) == 0xBC10 and h(0x806B3AA) == 0x4700,
            'shared return drift')
    require(literal_target(h(0x806B376), 0x806B376) == 0x806B3D0,
            'battle flags literal drift')
    require(literal_target(h(0x806B3B2), 0x806B3B2) == 0x806B3D4,
            'request buffer literal drift')
    require(w(0x806B3D0) == 0x02001AB4 and w(0x806B3D4) == 0x02001C6C,
            'native pointer identity drift')
    return {'window_sha256': digest, 'static_shape': 'PASS',
            'copier_entry_pc': hex(ENTRY), 'candidate_A_postloop_pc': hex(POST_A),
            'shared_epilogue_pc': hex(0x806B3A6),
            'link_alternative_pc': hex(0x806B3C8),
            'runtime_copy_completion_observed': False,
            'automatic_dispatch_authorized': False}


def check_rom(path):
    rom = path.read_bytes()
    sha = hashlib.sha256(rom).hexdigest()
    names = [name for name, expected in ROM_HASHES.items() if sha == expected]
    require(len(names) == 1, 'unknown ROM hash; refuse to infer a copy boundary')
    return {'rom_variant': names[0], 'rom_sha256': sha,
            **verify_native_window(window_from_rom(rom))}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', required=True, type=Path)
    p.add_argument('--other-rom', type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    one = check_rom(args.rom)
    two = check_rom(args.other_rom) if args.other_rom else None
    if two:
        require(one['rom_sha256'] != two['rom_sha256'], 'expected distinct ROMs')
        require(one['window_sha256'] == two['window_sha256'],
                'different copier code')
    result = {'scope': 'static-only, no native replay, no hook',
              'first': one, 'second': two}
    if args.output:
        require(not args.output.exists(), 'refuse overwrite')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS static-only native copy postloop candidate', one['rom_variant'],
          two['rom_variant'] if two else '', hex(POST_A))


if __name__ == '__main__':
    main()
