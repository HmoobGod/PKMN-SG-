"""Replay one historical *manual* battle choice and observe the next genuine
44-byte actor-0 buffer-A request, without calling or changing the native emitter.

Only the exact pinned prebuilt mGBA host and experimental16266 inputs are
accepted. The host is a third-party ELF modified only in a disposable copy to
clear DF_1_PIE for loading with ctypes. Run in a disposable/sandbox process.
This test does not prove player ownership, move legality, Android fidelity,
or safety to enable automatic submission.
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

HOST_SHA = '4304688a0b44007cca23c9e887af17c44530fd602ee3d1e57a232da397bec769'
LOADABLE_SHA = 'fef5effac26b13f53afe88511990fdf3049184402ca50faf9325d4daed7869c7'
ROM_SHA = '6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de'
SAVE_SHA = '8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
STATE_SHA = '0dbcb91a26a3825357f14c18800708a28ef371db57e8fe907ecfbb9dc2c1c7ef'
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pinned(path, expected, label):
    value = sha(path)
    if value != expected:
        raise ValueError(f'{label}: SHA mismatch; expected {expected}, received {value}')


def host_as_loadable_shared_object(src, dest):
    raw = bytearray(Path(src).read_bytes())
    # In this specific pinned ELF only: DT_FLAGS_1 at 0x171b88, value at 0x171b90.
    if struct.unpack_from('<Q', raw, 0x171B88)[0] != 0x6FFFFFFB:
        raise ValueError('ELF DT_FLAGS_1 identity differs')
    if struct.unpack_from('<Q', raw, 0x171B90)[0] != 0x08000001:
        raise ValueError('unexpected ELF PIE/flags')
    struct.pack_into('<Q', raw, 0x171B90, 1)
    dest.write_bytes(raw)
    pinned(dest, LOADABLE_SHA, 'temporary mGBA host')


class Event(C.Structure):
    _fields_ = [(key, C.c_uint32) for key in
                ('pc', 'frame', 'r0', 'r1', 'r2', 'r3', 'r4', 'sp', 'lr')]


class Stats(C.Structure):
    _fields_ = [(key, C.c_uint32) for key in
                ('start_frame', 'end_frame', 'event_count', 'stop_reason')] + [
                ('steps', C.c_uint64)]


class Proof(C.Structure):
    _fields_ = [(name, C.c_uint32) for name in (
        'state', 'error', 'begin_frame', 'end_frame', 'entry_frame', 'post_frame',
        'source', 'dest', 'actor', 'direction', 'length', 'entry_sp', 'entry_lr',
        'post_sp', 'post_lr', 'stores', 'pending_entry', 'pending_post',
        'opcode_post', 'total_steps', 'tag')] + [
        (name, C.c_uint8 * 44) for name in (
            'source_before', 'source_after', 'dest_after', 'store_values')] + [
        ('store_indices', C.c_uint32 * 44)]


def run(host, rom, save, state, output, compiler='cc'):
    for path, digest, label in [(host, HOST_SHA, 'original prebuilt host'),
                                (rom, ROM_SHA, 'experimental16266 ROM'),
                                (save, SAVE_SHA, 'user save'),
                                (state, STATE_SHA, 'pinned savestate')]:
        pinned(path, digest, label)
    if output.exists():
        raise FileExistsError(f'Will not overwrite existing report: {output}')
    with tempfile.TemporaryDirectory(prefix='sg16266_r7_') as folder:
        tmp = Path(folder)
        shared = tmp / 'host.so'
        host_as_loadable_shared_object(host, shared)
        # All emulated input files are disposable copies. No writing to originals.
        for original, name in [(rom, 'game.gba'), (save, 'game.sav'), (state, 'state.ss')]:
            shutil.copyfile(original, tmp / name)
        for src, name in [('alternate_mgba_trace_frames.c', 'trace.so'),
                          ('alternate_mgba_capture_player_copy.c', 'capture.so')]:
            subprocess.run([compiler, '-std=c11', '-O2', '-fPIC', '-shared',
                            '-Wall', '-Wextra', '-Werror', str(HERE / src),
                            '-o', str(tmp / name)], check=True)
        emu = C.CDLL(str(shared))
        emu.mCoreCreate.argtypes = [C.c_int]
        emu.mCoreCreate.restype = C.c_void_p
        emu.mCoreLoadFile.argtypes = [C.c_void_p, C.c_char_p]
        emu.mCoreLoadFile.restype = C.c_bool
        emu.mCoreInitConfig.argtypes = [C.c_void_p, C.c_char_p]
        emu.mCoreLoadSaveFile.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
        emu.mCoreLoadSaveFile.restype = C.c_bool
        emu.mCoreLoadStateNamed.argtypes = [C.c_void_p, C.c_void_p, C.c_int]
        emu.mCoreLoadStateNamed.restype = C.c_bool
        emu.VFileOpen.argtypes = [C.c_char_p, C.c_int]
        emu.VFileOpen.restype = C.c_void_p
        core = emu.mCoreCreate(0)
        if not core:
            raise RuntimeError('mCoreCreate failed')

        def method(offset, ret, *params):
            p = C.c_void_p.from_address(core + offset).value
            if not p:
                raise RuntimeError(f'missing core method {offset:#x}')
            return C.CFUNCTYPE(ret, C.c_void_p, *params)(p)

        method(0x12F0, None)(core)
        emu.mCoreInitConfig(core, None)
        if not emu.mCoreLoadFile(core, str(tmp / 'game.gba').encode()):
            raise RuntimeError('mCoreLoadFile failed')
        if not emu.mCoreLoadSaveFile(core, str(tmp / 'game.sav').encode(), False):
            raise RuntimeError('mCoreLoadSaveFile failed')
        method(0x13D0, None)(core)
        state_vf = emu.VFileOpen(str(tmp / 'state.ss').encode(), 0)
        if not state_vf or not emu.mCoreLoadStateNamed(core, state_vf, 0):
            raise RuntimeError('mCoreLoadStateNamed failed')
        cpu = C.c_void_p.from_address(core).value
        if not cpu:
            raise RuntimeError('missing ARM CPU')
        regs = (C.c_uint32 * 16).from_address(cpu)
        read32 = method(0x1498, C.c_uint32, C.c_uint32, C.c_int)
        frame = method(0x1428, C.c_uint32)
        keys = method(0x1408, None, C.c_uint32)
        clear_keys = method(0x1418, None, C.c_uint32)
        if (regs[15], regs[4]) != (0x08065B1A, 0):
            raise ValueError(f'unexpected savestate CPU state: {regs[15]:#x}, {regs[4]:#x}')
        if read32(core, 0x02001C6C, 0) != 0x0201BF04:
            raise ValueError('savestate request pointer changed')
        old = regs[15]
        prefetch_before = (C.c_uint32.from_address(cpu + 0x11c).value,
                           C.c_uint32.from_address(cpu + 0x120).value)
        host_base = C.cast(emu.mCoreCreate, C.c_void_p).value - 0x60120
        refresh_thumb = C.CFUNCTYPE(C.c_uint32, C.c_void_p)(host_base + 0xBF8F0)
        regs[15] = old - 2
        refresh_thumb(cpu)
        prefetch_after = (C.c_uint32.from_address(cpu + 0x11c).value,
                          C.c_uint32.from_address(cpu + 0x120).value)
        if regs[15] != old or prefetch_after != (0x4B00, 0x4718):
            raise ValueError('Thumb savestate prefetch restoration failed')
        tracer = C.CDLL(str(tmp / 'trace.so'))
        tracer.sg_until_pc.argtypes = [C.c_void_p, C.POINTER(C.c_uint32),
                                      C.c_uint32, C.c_uint32]
        tracer.sg_until_pc.restype = C.c_uint32
        tracer.sg_trace_frames.argtypes = [C.c_void_p, C.POINTER(C.c_uint32),
                                           C.c_uint32, C.c_uint32,
                                           C.POINTER(Event), C.c_uint32,
                                           C.POINTER(Stats)]
        reached = tracer.sg_until_pc(core, regs, 0x0806449E, 8_000_000)
        if not reached or frame(core) != 14244:
            raise ValueError('historical manual menu boundary was not reproduced')

        def frames(n, button):
            keys(core, button)
            arr = (Event * 2048)()
            stats = Stats()
            tracer.sg_trace_frames(core, regs, n, 12_000_000, arr, 2048,
                                   C.byref(stats))
            clear_keys(core, button)
            if stats.stop_reason != 1 or stats.event_count >= 2048:
                raise RuntimeError('frame stepping did not terminate cleanly')
            return arr[:stats.event_count], stats

        frames(2, 0)
        events, stats = frames(1, 1)  # Manual A, not a Smart AI action.
        emits = [x for x in events if x.pc == 0x0806BD80 and x.r0 == 0]
        if len(emits) != 1 or emits[0].r2 != 10 or emits[0].r3 != 257:
            raise ValueError('original native manual emitter payload mismatch')
        capture = C.CDLL(str(tmp / 'capture.so'))
        capture.sg_capture_player_request.argtypes = [C.c_void_p,
            C.POINTER(C.c_uint32), C.c_uint32, C.c_uint32, C.POINTER(Proof)]
        proof = Proof()
        capture.sg_capture_player_request(core, regs, 200, 18_000_000,
                                          C.byref(proof))
        data = bytes(proof.source_before)
        if (proof.state != 2 or proof.error != 0 or proof.stores != 44
                or proof.entry_frame != 14369 or proof.post_frame != 14369
                or proof.length != 44 or proof.actor != 0
                or bytes(proof.source_after) != data
                or bytes(proof.dest_after) != data
                or bytes(proof.store_values) != data
                or list(proof.store_indices) != list(range(44))
                or data[0] != 19 or proof.entry_lr != proof.post_lr):
            raise ValueError(f'completed actor-0 copy did not verify: '
                             f'{proof.state=} {proof.error=} {proof.stores=}')
        # An original byte copy is NOT yet a pending player request. This
        # fixture sets the pending bit later in the original engine path.
        if read32(core, 0x02001D2C, 0) & 1:
            raise ValueError('unexpected pending bit at original postloop')
        step = method(0x13E8, None)
        first_pending = None
        for i in range(2000):
            value = read32(core, 0x02001D2C, 0)
            if value & 1:
                first_pending = (i, regs[15], frame(core), value)
                break
            step(core)
        if first_pending != (23, 0x080D4CA4, 14369, 1):
            raise ValueError(f'original pending transition changed: {first_pending}')
        opcode = method(0x1488, C.c_uint32, C.c_uint32, C.c_int)(
            core, proof.dest, 0)
        if opcode != 19:
            raise ValueError('pending transition no longer matches move request')
        # This is a witness for these emulator instructions, NOT game authority.
        report = {
            'schema': 'sg16266-alt-mgba-observer-v1',
            'case': 'manual_confirm_then_next_actor0_move_request',
            'scope': 'one disposable emulator fixture; not a proof of action authority',
            'rom_sha256': sha(rom), 'save_sha256': sha(save),
            'savestate_sha256': sha(state),
            'original_host_sha256': sha(host),
            'patched_host_sha256': sha(shared),
            'savestate_version_warning': 'emulator reported warning; acknowledged, not cleared',
            'cpu_thumb_prefetch_refreshed': True,
            'prefetch_before': [hex(x) for x in prefetch_before],
            'prefetch_after': [hex(x) for x in prefetch_after],
            'human_confirm_frame': emits[0].frame,
            'human_confirm_original_payload': emits[0].r3,
            'entry_frame': proof.entry_frame, 'post_frame': proof.post_frame,
            'actor': proof.actor, 'direction': proof.direction, 'length': proof.length,
            'entry_pc': '0x0806b370', 'store_pc': '0x0806b3be',
            'post_pc': '0x0806b3c6',
            'source_address': proof.source, 'destination_address': proof.dest,
            'entry_sp': proof.entry_sp, 'post_sp': proof.post_sp,
            'entry_lr': proof.entry_lr, 'post_lr': proof.post_lr,
            'store_indices': list(proof.store_indices),
            'store_values_hex': bytes(proof.store_values).hex(),
            'source_before_hex': data.hex(),
            'source_after_hex': bytes(proof.source_after).hex(),
            'destination_after_hex': bytes(proof.dest_after).hex(),
            'pending_at_copy_entry': proof.pending_entry,
            'pending_at_post_copy': proof.pending_post,
            'opcode_at_post_copy': proof.opcode_post,
            'pending_set_after_post_guest_steps': first_pending[0],
            'pending_transition_pc': hex(first_pending[1]),
            'pending_transition_frame': first_pending[2],
            'pending_word_after_transition': first_pending[3],
            'pending_request_opcode_after_transition': opcode,
            'native_auto_moves': 0,
            'user_ownership_certified': False,
            'move_and_target_legality_certified': False,
            'real_mobile_gameplay_certified': False,
            'native_automatic_battle_acceptance': 0,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        print('PASS alternative mGBA replay; entry/post frame', proof.entry_frame,
              '44 native stores verified, original manual payload', emits[0].r3,
              'no automatic battle actions')
        return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('host', 'rom', 'save', 'state', 'output'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--cc', default='cc', help='host C compiler')
    a = p.parse_args()
    run(a.host, a.rom, a.save, a.state, a.output, a.cc)


if __name__ == '__main__':
    main()