#!/usr/bin/env python3
"""R4 exact-source builder: private disposable local copies only.

No ROM or save is shipped. Never executes the game, uploads data or changes the
protected inputs. Fails before writing if source/binary identity or either output
path is unacceptable. Two output files are installed with exclusive links.
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

SOURCE_SHA256 = 'ce8d38b718939243a99eed560d250ed30e15b29255a0b4f0c21f3cd3ced12333'
GUARD_SHA256 = 'd588d77c7096afcf9130b445d184ef06842f7599da92649c65ae73d637abc584'
GUARD_SIZE = 252
ROM_SHA256 = '7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32'
SAV_SHA256 = '8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
ORIGINAL_HOOK = bytes.fromhex('00 b5 1b 18 2a 70 72 00')
REPLAY = bytes.fromhex('3f bc 00 b5 1b 18 2a 70 72 00')
HOOK_OFFSET = 0x65ED8
CAVE_OFFSET = 0x1F34000
VENEER = struct.pack('<HHI', 0x4F00, 0x4738, 0x09F34001)
SOURCE = Path(__file__).with_name('player_taunt_recovery_choice_gorilla_r4.s')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(cond: bool, reason: str) -> None:
    if not cond:
        raise RuntimeError('FAIL CLOSED: ' + reason)


def build_assembly(clang: str, objcopy: str, build_dir: Path, source: Path = SOURCE) -> bytes:
    """Enforce source SHA *before invoking toolchain* and code SHA before returning.

    Successful hash match makes toolchain-version drift fail closed by construction.
    Private ROM output is not touched by this function.
    """
    require(source.is_file(), 'R4 source missing')
    src = source.read_bytes()
    require(sha(src) == SOURCE_SHA256, 'exact approved R4 assembly source hash mismatch')
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / 'r4_guard.o'
    out = build_dir / 'r4_guard.bin'
    clang_argv = [clang, '--target=armv4t-none-eabi', '-mthumb', '-c', str(source), '-o', str(obj)]
    copy_argv = [objcopy, '-O', 'binary', '-j', '.text.r4guard', str(obj), str(out)]
    subprocess.run(clang_argv, check=True, capture_output=True)
    subprocess.run(copy_argv, check=True, capture_output=True)
    code = out.read_bytes()
    require(len(code) == GUARD_SIZE, 'guard length differs from exactly 252 bytes')
    require(sha(code) == GUARD_SHA256, 'guard binary hash mismatch; toolchain drift or tampering')
    require(code.startswith(bytes.fromhex('3f b4')), 'guard entry push mismatch')
    require(REPLAY in code, 'original replay missing')
    require(code[-4:] == struct.pack('<I', 0x08065EE1), 'Thumb resume literal mismatch')
    return code


def verify_output_paths(rom: Path, sav: Path, output: Path) -> Path:
    """Preflight BOTH paths (and their aliases) before any copy or commit."""
    require(output.suffix.lower() == '.gba', 'output must be .gba; .sav is forbidden')
    save_output = output.with_suffix('.sav')
    require(output != save_output, 'ROM and SAV destination collision')
    for dest in (output, save_output):
        require(not dest.exists() and not dest.is_symlink(), f'output exists: {dest}')
        # resolve() catches aliases through symlinked parent directories
        require(dest.resolve() != rom.resolve(), 'output aliases protected ROM')
        require(dest.resolve() != sav.resolve(), 'output aliases protected save')
        for protected in (rom, sav):
            try:
                require(not os.path.samefile(dest, protected), 'output hardlink aliases protected input')
            except FileNotFoundError:
                pass
    require(rom.resolve() != sav.resolve(), 'ROM and save unexpectedly alias')
    return save_output


def validate_inputs(rom: bytes, sav: bytes, code_size: int) -> None:
    require(len(rom) == 0x2000000 and sha(rom) == ROM_SHA256, 'original ROM identity mismatch')
    require(len(sav) == 0x20000 and sha(sav) == SAV_SHA256, 'original SAV identity mismatch')
    require(code_size == GUARD_SIZE, 'incorrect guard length')
    require(rom[HOOK_OFFSET:HOOK_OFFSET + 8] == ORIGINAL_HOOK, 'original hook overwritten')
    require(rom[CAVE_OFFSET:CAVE_OFFSET + code_size] == b'\xff'*code_size, 'original code cave occupied')


def make_candidate(rom: bytes, code: bytes) -> tuple[bytes, int]:
    require(len(code) == GUARD_SIZE and sha(code) == GUARD_SHA256, 'unauthorized code payload')
    out = bytearray(rom)
    out[HOOK_OFFSET:HOOK_OFFSET + 8] = VENEER
    out[CAVE_OFFSET:CAVE_OFFSET + len(code)] = code
    diffs = [i for i,(a,b) in enumerate(zip(rom, out)) if a != b]
    require(bool(diffs), 'unchanged candidate')
    require(all(HOOK_OFFSET <= i < HOOK_OFFSET+8 or CAVE_OFFSET <= i < CAVE_OFFSET+len(code) for i in diffs), 'out-of-window mutation')
    return bytes(out), len(diffs)


def commit_exclusive(output: Path, candidate: bytes, save_output: Path, save_data: bytes) -> None:
    """Stage both outputs, then use fail-if-present links. Roll back only our links.

    Two-file installation cannot be perfectly atomic on a typical filesystem;
    rollback is best-effort if another process interferes. Never overwrites.
    """
    require(output.suffix.lower() == '.gba', 'output must be .gba')
    for dest in (output, save_output):
        require(not dest.exists() and not dest.is_symlink(), f'destination exists: {dest}')
    require(output.parent.is_dir(), 'destination parent directory does not exist')
    created = []
    with tempfile.TemporaryDirectory(dir=output.parent, prefix='.sg_r4_stage_') as td:
        stage_rom = Path(td) / 'candidate.gba'
        stage_sav = Path(td) / 'candidate.sav'
        stage_rom.write_bytes(candidate)
        stage_sav.write_bytes(save_data)
        require(sha(stage_rom.read_bytes()) == sha(candidate), 'stage ROM integrity error')
        require(sha(stage_sav.read_bytes()) == sha(save_data), 'stage SAV integrity error')
        try:
            for stage, dest in ((stage_sav, save_output), (stage_rom, output)):
                # no-overwrite operation raises FileExistsError for existing path
                os.link(stage, dest, follow_symlinks=False)
                created.append(dest)
        except Exception:
            for dest in reversed(created):
                dest.unlink(missing_ok=True)
            raise


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--sav', type=Path, required=True)
    p.add_argument('--local-output', type=Path, required=True, help='private disposable .gba output only')
    p.add_argument('--clang', default='clang')
    p.add_argument('--objcopy', default='llvm-objcopy')
    a = p.parse_args()
    out = a.local_output.absolute()
    save_out = verify_output_paths(a.rom, a.sav, out) # BEFORE source/toolchain/read/write
    require(out.parent.is_dir(), 'output parent must already exist')
    with tempfile.TemporaryDirectory(prefix='sg_r4_exact_build_') as temp:
        code = build_assembly(a.clang, a.objcopy, Path(temp))
    original_rom = a.rom.read_bytes()
    original_save = a.sav.read_bytes()
    validate_inputs(original_rom, original_save, len(code))
    candidate, count = make_candidate(original_rom, code)
    verify_output_paths(a.rom, a.sav, out) # re-check near commit
    commit_exclusive(out, candidate, save_out, original_save)
    # Original files are rehashed; never edited.
    require(sha(a.rom.read_bytes()) == ROM_SHA256, 'protected original ROM fingerprint changed')
    require(sha(a.sav.read_bytes()) == SAV_SHA256, 'protected original SAV fingerprint changed')
    print('PRIVATE DISPOSABLE candidate:', out)
    print('Code bytes:', len(code), 'SHA256:', sha(code))
    print('Diff bytes (two windows only):', count)
    print('No native gameplay executed; never upload output ROM or save.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('FAIL CLOSED:', exc, file=sys.stderr)
        sys.exit(1)
