#!/usr/bin/env python3
"""Read-only original-file identity and console receipt adapter for future live GDB probes.

Call `NativeCaptureReceipt` in the *same* Python process that actually drives
mGBA, immediately after obtaining a verified GDB S02 handshake. This helper
never launches the emulator, reads guest memory, synthesizes original CPU
instructions, mutates any ROM/save, or loads/emits any savestate. The caller
must supply actual unaltered STOP records from a connected debugger.

A process/start marker remains an *attestation*, not externally verified PID
or proof of native engine authority. No receipt alone earns a native pass.
"""
import hashlib
import json
import os
import secrets
import time
from pathlib import Path

from verify_native_wild_chain import (
    EXACT_ROM_SHA256, ALLOWED_BP_ADDRESSES, BP_RE, SNAP_RE, KEY_RE,
    verify_capture,
)


def digest(path):
    # Only reads; no original file write path.
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class NativeCaptureReceipt:
    def __init__(self, rom_path, original_save_path):
        self.rom = Path(rom_path)
        self.original_save = Path(original_save_path)
        self.rom_hash = digest(self.rom)
        if self.rom_hash != EXACT_ROM_SHA256:
            raise ValueError('exact modified ROM hash required for native receipt')
        self.save_hash = digest(self.original_save)
        self.pid = os.getpid()
        self.started_epoch = round(time.time(), 3)
        self.run_id = 'native-' + secrets.token_hex(16)
        self.start_marker = (
            f'RUN_START {self.run_id} pid={self.pid} start={self.started_epoch}'
        )
        self.lines = [self.start_marker]
        self.events = []
        self.finished = False
        self.last_key_t = -1.0
        self.movement_seen = False

    def note_breakpoint(self, pc):
        if pc not in ALLOWED_BP_ADDRESSES:
            raise ValueError('unrecognized breakpoint for receipt')
        self.lines.append(f'BP {pc} OK')

    def note_screenshot_label(self, name):
        # Records a screenshot *label* only. Never opens/loads a state or PNG.
        line = 'SNAP ' + name
        if SNAP_RE.fullmatch(line) is None:
            raise ValueError('invalid screenshot-only label')
        self.lines.append(line)

    def note_key(self, key, relative_seconds):
        line = f'KEY {key} {relative_seconds}'
        if KEY_RE.fullmatch(line) is None:
            raise ValueError('invalid host key/clock record')
        timestamp = float(relative_seconds)
        if timestamp <= self.last_key_t:
            raise ValueError('host key clock regression')
        if key in ('Left', 'Right', 'Up', 'Down'):
            self.movement_seen = True
        elif self.movement_seen:
            raise ValueError('host confirmation after movement prohibited')
        self.last_key_t = timestamp
        self.lines.append(line)

    def note_original_gdb_stop(self, row):
        if type(row) is not dict or 'run_id' in row:
            raise ValueError('raw CPU STOP must be a debugger-supplied dict')
        # Console row is preserved with its original keys; only the companion
        # capture event gets a run id. No fabricated CPU data is added.
        self.lines.append('STOP ' + json.dumps(row, allow_nan=False, separators=(',', ':')))
        self.events.append(dict(row, run_id=self.run_id))

    def finalize(self, *, mode='v5-full', output_dir=None):
        if self.finished:
            raise ValueError('receipt already closed')
        rom_post, save_post = digest(self.rom), digest(self.original_save)
        if (rom_post, save_post) != (self.rom_hash, self.save_hash):
            raise ValueError('original ROM or save changed during capture')
        self.lines.append(f'EVENTS {len(self.events)}')
        self.lines.append(f'ORIGINAL_POST_HASH {rom_post} {save_post}')
        console = '\n'.join(self.lines) + '\n'
        run = {
            'run_id': self.run_id,
            'start_marker': self.start_marker,
            'console_sha256': hashlib.sha256(console.encode()).hexdigest(),
            'provenance': 'INSTRUMENTED_RUN',
            'process_id_observed': True,
            'pid': self.pid,
            'started_epoch': self.started_epoch,
            'initial_save_sha256': self.save_hash,
        }
        capture = {
            'rom_sha256': self.rom_hash,
            'save_sha256': self.save_hash,
            'run': run,
            'original_cpu_events': self.events,
        }
        result = verify_capture(capture, console, mode)
        result['source_rom_rehashed_at_end'] = True
        result['source_save_rehashed_at_end'] = True
        result['receipt_generator'] = 'READ_ONLY_HOST_LOG_ADAPTER_NOT_EMULATOR_INTEGRATION'
        if output_dir is not None:
            output = Path(output_dir)
            if output.exists():
                raise FileExistsError('never replace an existing receipt directory')
            output.mkdir(parents=True)
            (output / 'original_console.log').write_text(console)
            (output / 'original_cpu_capture.json').write_text(json.dumps(capture, indent=2))
            (output / 'verified_report.json').write_text(json.dumps(result, indent=2))
        self.finished = True
        return result
