#!/usr/bin/env python3
"""Opt-in, local-only launcher for PR28's explicitly read-only Current probe.

Checks test-copy filenames, exact ROM/save hashes and exact reviewed observer
bytes before invoking ONLY --probe-only --current-copy-probe-only. A successful
probe is RSP compatibility evidence, not gameplay, ROM-loaded attestation, or
permission for a native battle hook. No network other than observer localhost.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import subprocess
import sys
from pathlib import Path

ROM_SHA = '7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32'
SAVE_SHA = '8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
ROM_LEN = 33554432
SAVE_LEN = 131072
ROM_FILENAME = 'Pokemon_SoulGold_TEST_COPY.gba'
SAVE_FILENAME = 'Pokemon_SoulGold_TEST_COPY.sav'
# GitHub PR28 exact head 41ab3cdf45e249f321b4cb206a1d843fe5639b57;
# any changes need separate review. SHA calculated from extracted PR28 source.
OBSERVER_SHA = '7d1e30f8a3a51b586708b37a2e0f5793f835723ad3df935144dc8962d2156d2a'
ALLOWED_REPORT_STATUS = {'FAILED_OR_PARTIAL', 'RESEARCH_ONLY'}


class PreflightError(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise PreflightError(reason)


def fingerprint(path: Path, expected_length: int, expected_sha: str) -> str:
    """Hash existing regular non-symlink, never write/rename these files."""
    require(path.is_file() and not path.is_symlink(), 'required file absent or symlink: ' + path.name)
    require(path.stat().st_nlink == 1, 'hardlinked input or observer refused: ' + path.name)
    require(path.stat().st_size == expected_length, 'unexpected size: ' + path.name)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1 << 20), b''):
            h.update(part)
    digest = h.hexdigest()
    require(digest == expected_sha, 'SHA256 mismatch for ' + path.name)
    return digest


def validate_paths(rom: Path, save: Path, observer: Path, private_dir: Path):
    require(rom.name == ROM_FILENAME and save.name == SAVE_FILENAME,
            'only specifically named disposable TEST_COPY files allowed')
    require(rom.resolve() != save.resolve(), 'ROM and save must be different files')
    require(rom.resolve() != observer.resolve() and save.resolve() != observer.resolve(),
            'observer cannot be a ROM or save')
    require(not private_dir.is_symlink(), 'private report directory cannot be a symlink')
    # The tool must not be stored inside the protected input file or replace it.
    require(private_dir.resolve() not in (rom.resolve(), save.resolve()),
            'report output directory cannot equal an input file')
    fingerprint(rom, ROM_LEN, ROM_SHA)
    fingerprint(save, SAVE_LEN, SAVE_SHA)
    fingerprint(observer, observer.stat().st_size if observer.is_file() else 0, OBSERVER_SHA)
    require(observer.name == 'capture_original_request_rsp.py',
            'unexpected observer script name')


def private_target(private_dir: Path) -> Path:
    """Create only our own unguessable report filename, no pre-existing clobber."""
    if private_dir.exists():
        require(private_dir.is_dir() and not private_dir.is_symlink(),
                'private directory is not a regular directory')
    else:
        private_dir.mkdir(parents=True, mode=0o700)
    for _ in range(4):
        destination = private_dir / ('current-rsp-probe-' + secrets.token_hex(8) + '.json')
        if not destination.exists() and not destination.is_symlink():
            return destination
    raise PreflightError('could not find unique output path')


def run(rom: Path, save: Path, observer: Path, private_dir: Path,
        port: int = 2345, run_probe: bool = False, timeout: float = 10.0) -> dict:
    require(type(port) is int and 1024 <= port <= 65535, 'invalid localhost GDB port')
    require(type(timeout) in (int, float) and 0.1 <= timeout <= 30,
            'invalid probe timeout')
    require(type(run_probe) is bool, 'run_probe must be boolean')
    rom, save, observer, private_dir = map(Path, (rom, save, observer, private_dir))
    validate_paths(rom, save, observer, private_dir)
    outcome = {
        'scope': 'local_Current_duplicate_only',
        'exact_test_rom_sha256': ROM_SHA,
        'exact_test_save_sha256': SAVE_SHA,
        'exact_pr28_observer_sha256': OBSERVER_SHA,
        'observer_source_only_awaits_independent_review': True,
        'emulator_loaded_rom_verified': False,
        'engine_request_or_gameplay_certified': False,
        'formal_native_acceptance': 0,
        'performed_local_rsp_probe': False,
        'private_report_path': None,
    }
    if not run_probe:
        outcome['status'] = 'SAFE_PREFLIGHT_ONLY_NO_CONNECTION'
        return outcome
    target = private_target(private_dir)
    # Hardcoded safe options. No shell, no opportunity to inject c/s/Z0 or
    # guest writes. PR28 observer still enforces its own wire-level whitelist.
    command = [sys.executable, str(observer),
               '--rom', str(rom), '--save', str(save), '--output', str(target),
               '--port', str(port), '--timeout', str(timeout), '--max-stops', '1',
               '--probe-only', '--current-copy-probe-only']
    try:
        completed = subprocess.run(command, check=False, capture_output=True,
                                   text=True, timeout=max(20.0, timeout + 10.0))
        outcome['observer_process_exit_code'] = completed.returncode
        outcome['performed_local_rsp_probe'] = True
        # The subprocess may fail; this is never proof of an emulator connection.
        if target.is_file() and not target.is_symlink():
            require(target.stat().st_size <= 2_000_000, 'private report exceeds size limit')
            data = json.loads(target.read_text(encoding='utf-8'))
            require(isinstance(data, dict), 'observer JSON is not an object')
            require(data.get('input_rom_identity_class') == 'current-duplicate-probe-only',
                    'observer reported unexpected ROM identity class')
            require(data.get('native_acceptance') == 0,
                    'observer reported forbidden native acceptance')
            require(data.get('current_rom_loaded_in_emulator_proven') is False,
                    'observer claimed unsupported loaded ROM identity')
            require(data.get('events') == [] and data.get('probe_only') is True,
                    'observer was not restricted to probe-only')
            require(data.get('tool_sent_battle_commands') == 0 and
                    data.get('tool_sent_guest_writes') == 0, 'observer reported unsafe command')
            require(data.get('input_file_rom_sha256') == ROM_SHA and
                    data.get('input_file_save_sha256') == SAVE_SHA, 'observer input identity mismatch')
            outcome['private_report_path'] = str(target)
            evidence_complete = (completed.returncode == 0 and
                                 data.get('failure') is None and
                                 data.get('input_files_unchanged') is True and
                                 isinstance(data.get('probe_transcript'), dict))
            outcome['status'] = ('PRIVATE_PROBE_REPORT_SAVED_NEEDS_ANALYSIS'
                                 if evidence_complete else 'PRIVATE_PARTIAL_REPORT_SAVED')
        else:
            outcome['status'] = 'NO_REPORT_OBSERVER_FAILED'
    except subprocess.TimeoutExpired:
        # Do not claim cleanup of a debugger that might have disconnected.
        outcome['status'] = 'OBSERVER_PROCESS_TIMEOUT_NO_NATIVE_EVIDENCE'
        outcome['private_report_path'] = str(target) if target.exists() else None
    # Validate inputs again even if observer failed or timed out.
    fingerprint(rom, ROM_LEN, ROM_SHA)
    fingerprint(save, SAVE_LEN, SAVE_SHA)
    fingerprint(observer, observer.stat().st_size, OBSERVER_SHA)
    return outcome


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, default=Path(ROM_FILENAME))
    p.add_argument('--save', type=Path, default=Path(SAVE_FILENAME))
    p.add_argument('--observer', type=Path, required=True,
                   help='extracted PR28 tools/capture_original_request_rsp.py at approved exact hash')
    p.add_argument('--private-dir', type=Path, default=Path('SoulGold_Private_Probe_Reports'))
    p.add_argument('--port', type=int, default=2345)
    p.add_argument('--timeout', type=float, default=10.0)
    p.add_argument('--run-probe', action='store_true',
                   help='EXPLICIT OPT-IN: connect to already paused local mGBA GDB server')
    a = p.parse_args()
    try:
        result = run(a.rom, a.save, a.observer, a.private_dir,
                     port=a.port, run_probe=a.run_probe, timeout=a.timeout)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    if result.get('status') in ('PRIVATE_PARTIAL_REPORT_SAVED',
                                'NO_REPORT_OBSERVER_FAILED',
                                'OBSERVER_PROCESS_TIMEOUT_NO_NATIVE_EVIDENCE'):
        raise SystemExit(2)


if __name__ == '__main__':
    main()