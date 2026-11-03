"""R10 RESEARCH-only shadow ranker + ordinary menu button trial. R8 context check of one historical battle choice and observe the next genuine
44-byte actor-0 buffer-A request, without calling or changing the native emitter.

Only the exact pinned prebuilt mGBA host and experimental16266 inputs are
accepted. The host is a third-party ELF modified only in a disposable copy to
clear DF_1_PIE for loading with ctypes. Run in a disposable/sandbox process.
This scripted host input trial is NOT native in-ROM Smart AI. It is limited to two previously manually accepted move slots in one exact saved wild fixture, and DOES NOT certify ownership or general legality.
"""
import argparse
import ctypes as C
import hashlib
import json
import re
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


def run(host, rom, save, state, output, compiler='cc', accepted_mask=3):
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
        read8 = method(0x1488, C.c_uint32, C.c_uint32, C.c_int)
        read16 = method(0x1490, C.c_uint32, C.c_uint32, C.c_int)
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
        # Observe only public controller metadata and OWN-BATTLER fields.
        # In particular, do not read opponent moves, HP, PP, item or ability.
        def context():
            flags = read32(core, 0x02001AB4, 0)
            count = read8(core, 0x02001AB8, 0)
            if count != 2 or flags != 4:
                raise ValueError(f'unsupported live battle context: {flags=} {count=}')
            base = read32(core, 0x02001C6C, 0)
            if base != 0x0201BF04:
                raise ValueError('live controller request pointer changed')
            mask = (3 & ~read8(core, 0x02001D42, 0))
            actor = 0
            own = 0x02001ECC + actor * 152
            restricted_ptr = read32(core, 0x02001D24, 0)
            if restricted_ptr < 0x02000000 or restricted_ptr > 0x02040000 - 0x39D or restricted_ptr & 3:
                raise ValueError('invalid original native restriction cache pointer')
            packed_locks = read32(core, own + 0x6C, 0)
            native_restricted_mask = read8(core, restricted_ptr + 0x39C, 0)
            if native_restricted_mask & ~15:
                raise ValueError('unexpected native restriction mask bits')
            contexts = {
                'flags': flags,
                'battlers_count': count,
                'controller_kinds': [read8(core, 0x030001A4 + a, 0) for a in range(count)],
                'controller_completions': [read32(core, 0x03002E48 + 4*a, 0) for a in range(count)],
                'controller_runners': [read32(core, 0x03002E58 + 4*a, 0) for a in range(count)],
                'positions': [read8(core, 0x02001B58 + a, 0) for a in range(count)],
                'public_present_mask': mask,
                'pending_word': read32(core, 0x02001D2C, 0),
                'player_request_opcode': read8(core, base + 0x10, 0),
                'player_own_moves': [read16(core, own + 12+2*m, 0) for m in range(4)],
                'player_request_moves': [read16(core, base + 20+2*m, 0) for m in range(4)],
                'player_own_pp': [read8(core, own + 37+m, 0) for m in range(4)],
                'player_native_restricted_mask_negative_only': native_restricted_mask,
                'player_disabled_move': (packed_locks >> 11) & 1023,
                'player_encored_move': (packed_locks >> 21) & 1023,
                'player_encore_timer': (read32(core, own + 0x74, 0) >> 15) & 7,
                'player_last_move': read16(core, 0x02001DF8 + 2*actor, 0),
                'player_repeat_blocked': read8(core, own + 0x58, 0) >> 7,
            }
            if (contexts['controller_kinds'] != [1, 3] or
                    contexts['controller_completions'] != [0x080625F9, 0x080616D9] or
                    contexts['positions'] != [0, 1] or mask != 3):
                raise ValueError('original controller or battler role not expected wild signature')
            return contexts

        postcopy_context = context()
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
        pending_context = context()
        # Use the actual isolated Smart AI source ranker, outside the game.
        # A historical pair of MANUALLY accepted moves in this exact fixture
        # constrains a host-only acceptance trial, NOT game-side permissions.
        expected_moves=[325,157,92,269]
        expected_pp=[20,9,10,20]
        if (accepted_mask not in (1,3) or
                pending_context['player_own_moves']!=expected_moves or
                pending_context['player_request_moves']!=expected_moves or
                pending_context['player_own_pp']!=expected_pp or
                pending_context['player_native_restricted_mask_negative_only']!=0 or
                pending_context['player_disabled_move']!=0 or
                pending_context['player_encore_timer']!=0 or
                pending_context['player_repeat_blocked']!=0):
            raise ValueError('shadow host test cannot generalize fixture legality')
        rom_bytes=rom.read_bytes()
        md=[]
        for move,pp in zip(expected_moves,expected_pp):
            index=0x0877CC6C-0x08000000+72*move
            packed=int.from_bytes(rom_bytes[index+10:index+12],'little')
            raw_target=int.from_bytes(rom_bytes[index+12:index+14],'little')
            power=packed>>7; category=(packed>>5)&3
            acc=raw_target&127; mode=raw_target>>7
            if category>1 and (accepted_mask&(1<<expected_moves.index(move))):
                raise ValueError('unsupported eligible move category')
            md.extend(map(str,(move,pp,power,acc,mode)))
        root=HERE.parent
        ranker=tmp/'shadow_ranker'
        subprocess.run([compiler,'-std=c11','-O2','-Wall','-Wextra','-Werror',
            '-pedantic','-I'+str(root/'include'),'-I'+str(root/'src'),
            str(HERE/'shadow_ranker.c'),
            str(root/'src'/'ranker_workspace.c'),
            str(root/'src'/'sg_action_gate.c'),
            str(root/'src'/'sg_baseline_mode_guard.c'),
            str(root/'src'/'sg_public_types.c'),'-o',str(ranker)],check=True)
        shadow=subprocess.run([str(ranker),str(accepted_mask),*md],
                              capture_output=True,text=True,check=True)
        match=re.fullmatch(r'SHADOW_ONLY slot=([01]) target=1 candidates=([12]); NO ENGINE PERMISSION\n',shadow.stdout)
        if not match:raise ValueError('unrecognized shadow scorer result')
        chosen_slot=int(match.group(1))
        if not (accepted_mask&(1<<chosen_slot)):
            raise ValueError('shadow scorer selected unverified fixture slot')
        shadow_proposal=dict(slot=chosen_slot,target=1,move_id=expected_moves[chosen_slot],
            candidate_count=int(match.group(2)),tested_manual_fixture_mask=accepted_mask,
            selected_by='original isolated SG public ranker, HOST-ONLY',
            engine_action_authority=False,original_game_ai_enabled=False)
        # Correlate the original copy with the actor's engine-owned request,
        # but NEVER promote the player-controller signature to owner authority.
        core_fields = ['flags', 'battlers_count', 'controller_kinds',
                       'controller_completions', 'positions', 'public_present_mask',
                       'player_request_opcode', 'player_own_moves',
                       'player_request_moves', 'player_own_pp',
                       'player_native_restricted_mask_negative_only',
                       'player_disabled_move', 'player_encored_move',
                       'player_encore_timer', 'player_last_move', 'player_repeat_blocked']
        for field in core_fields:
            if pending_context[field] != postcopy_context[field]:
                raise ValueError(f'own/public context drift at pending: {field}')
        if postcopy_context['pending_word'] != 0 or pending_context['pending_word'] != 1:
            raise ValueError('copy/pending timing changed')
        if pending_context['player_request_opcode'] != 19:
            raise ValueError('pending not linked to exact request location')
        if bytes(read8(core, proof.dest + i, 0) for i in range(44)) != data:
            raise ValueError('request bytes changed between completion and pending')
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
            'postcopy_context': postcopy_context,
            'pending_context': pending_context,
            'r8_public_context_only': True,
            'original_native_installer_seen_this_process': False,
            'engine_owned_request_correlated_this_fixture': True,
            'native_auto_moves': 0,
            'user_ownership_certified': False,
            'move_and_target_legality_certified': False,
            'real_mobile_gameplay_certified': False,
            'native_automatic_battle_acceptance': 0,
        }
        # Native manual menu must be reached under the SAME live request.
        reached=tracer.sg_until_pc(core,regs,0x0806449E,8_000_000)
        if not reached or frame(core)!=14373 or not read32(core,0x02001D2C,0)&1:
            raise ValueError('original player menu/pending gate was not reached')
        original_menu_frame=frame(core)
        subprocess.run([compiler,'-std=c11','-O2','-shared','-fPIC',
                        '-Wall','-Wextra','-Werror',str(HERE/'trace_manual_native.c'),
                        '-o',str(tmp/'original_manual.so')],check=True)
        manual=C.CDLL(str(tmp/'original_manual.so'))
        class ManualEvent(C.Structure):
            _fields_=[(k,C.c_uint32) for k in (
                'pc','frame','r0','r1','r2','r3','r4','r6','pending',
                'own_reply_header','own_reply_payload','own_reply_valid')]
        class ManualStats(C.Structure):
            _fields_=[(k,C.c_uint32) for k in (
                'first_frame','last_frame','count','status')]+[('steps',C.c_uint64)]
        manual.sg_trace_original_manual.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),
            C.c_uint32,C.c_uint32,C.POINTER(ManualEvent),C.c_uint32,C.POINTER(ManualStats)]
        def original_frames(n, buttons):
            keys(core,buttons)
            event_array=(ManualEvent*128)();st=ManualStats()
            manual.sg_trace_original_manual(core,regs,n,8_000_000,event_array,128,C.byref(st))
            clear_keys(core,buttons)
            if st.status!=1 or st.count>128:
                raise RuntimeError('original manual trace not bounded cleanly')
            return [event_array[i] for i in range(st.count)]
        original_frames(2,0)
        if chosen_slot==0:
            original_frames(1,32)  # ordinary human LEFT key to move slot0
            original_frames(1,0)   # release before A
        original_events=original_frames(1,1)  # ordinary human A, never auto
        original_events+=original_frames(1,0)
        markers={0x0806BD80:'emit',0x0806B370:'reply_entry',
            0x0806261C:'completion',0x080E5E5C:'consumer_check',
            0x08094330:'native_validation_result',0x0809435C:'slot_commit',
            0x08094374:'move_commit',0x08094380:'target_commit'}
        history=[]
        for e in original_events:
            if e.pc not in markers:raise ValueError('unexpected original marker')
            entry={'kind':markers[e.pc],'original_pc':hex(e.pc),
                   'frame':e.frame,'pending_word':e.pending}
            if e.pc==0x0806BD80:
                entry.update(emit_actor=e.r0,subcmd=e.r2,encoded_choice=e.r3)
            elif e.pc==0x0806B370:
                entry.update(reply_actor=e.r0,direction=e.r1,bytes=e.r3,
                             reply_header=e.own_reply_header,
                             reply_payload=e.own_reply_payload,
                             reply_ewram_valid=bool(e.own_reply_valid))
            elif e.pc==0x0806261C:
                entry.update(completion_actor=e.r4)
            elif e.pc==0x080E5E5C:
                entry.update(consumer_actor=e.r0)
            else:
                entry.update(consumer_actor=e.r6)
                if e.pc==0x08094330:entry.update(original_native_result=e.r0)
                if e.pc==0x0809435C:entry.update(committed_move_slot=e.r0)
                if e.pc==0x08094374:entry.update(committed_move_id=e.r0)
            history.append(entry)
        if [e['kind'] for e in history]!=[
            'emit','reply_entry','completion','consumer_check',
            'native_validation_result','slot_commit','move_commit','target_commit']:
            raise ValueError('native actor0 original confirmation/consumer markers differ')
        press_frame=14377 if chosen_slot==0 else 14375
        commit_frame=press_frame+1
        expected_move=(325,157)[chosen_slot]
        expected_payload=256+chosen_slot
        if not(history[0]['frame']==history[1]['frame']==history[2]['frame']==press_frame
               and all(e['frame']==commit_frame for e in history[3:])
               and history[0]['encoded_choice']==expected_payload
               and history[1]['reply_header']==0x0A20
               and history[1]['reply_payload']==expected_payload and history[1]['reply_ewram_valid']
               and history[4]['original_native_result']==0
               and history[5]['committed_move_slot']==chosen_slot
               and history[6]['committed_move_id']==pending_context['player_own_moves'][chosen_slot]==expected_move):
            raise ValueError('original native accepted human choice did not match fixture')
        result={'schema':'sg16266-host-shadow-menu-v1',
            'scope':'one disposable host-selected original move menu input in pinned wild single; no in-ROM automatic action authority',
            'underlying_live_request':report,
            'original_manual_menu_frame':original_menu_frame,
            'host_menu_buttons':'LEFT then A' if chosen_slot==0 else 'A',
            'shadow_proposal':shadow_proposal,
            'native_player_events':history,
            'selected_move_slot':chosen_slot,
            'selected_move_id':expected_move,
            'selected_target_position':1,
            'original_native_validation_accepted':True,
            'original_native_emitter_untouched':True,
            'host_scripted_menu_move_choices':1,'in_rom_auto_moves':0,
            'automatic_battle_acceptance':0,
            'general_move_legality_certified':False,
            'exclusive_player_ownership_certified':False,
            'other_encounters_certified':False}
        from verify_shadow_menu import verify
        verify(result)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(f'PASS R10 host-selected original actor0 move slot{chosen_slot} move{expected_move}; native accepted, in-ROM auto=0')
        return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('host', 'rom', 'save', 'state', 'output'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--cc', default='cc', help='host C compiler')
    p.add_argument('--accepted-mask', type=int, choices=(1,3), default=3)
    a = p.parse_args()
    run(a.host, a.rom, a.save, a.state, a.output, a.cc, a.accepted_mask)


if __name__ == '__main__':
    main()