#!/usr/bin/env python3
"""Private, bounded, read-only sample parity probe for an already-paused mGBA RSP target.

No host controls, target resumes, breakpoints, steps, guest writes, or reset.
The comparison is SAMPLED parity, not emulator ROM/save identity certification.
The transcript is PRIVATE and never suitable for committing to a repository.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import stat

EXACT_MODIFIED_SHA = '4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44'
PROTECTED_CURRENT_SHA = '7b9ac66d38f38dcddc1cc907822615fcf56689600fdccaffa9df9a836fb9ee32'
ROM_LENGTH = 32 * 1024 * 1024
ROM_BASE = 0x08000000
SAMPLE_BYTES = 8
MAX_FRAME_BYTES = 8192
MAX_TRACE_BYTES = 65536
MAX_TRACE_EVENTS = 64


class IdentityError(RuntimeError):
    pass


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def load_rom(path, expected):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise IdentityError('ROM input must be a regular, non-symlink file')
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size != ROM_LENGTH:
        raise IdentityError('ROM size or file kind invalid')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise IdentityError('ROM SHA-256 mismatch')
    return data


def choose_windows(modified, current):
    """Select 2-3 distinct divergent ROM windows and one common control."""
    if len(modified) != ROM_LENGTH or len(current) != ROM_LENGTH:
        raise IdentityError('incorrect ROM sizes')
    first = last = near_mid = None
    mid_distance = ROM_LENGTH + 1
    differences = 0
    for offset in range(0, ROM_LENGTH - SAMPLE_BYTES + 1, SAMPLE_BYTES):
        if modified[offset:offset + SAMPLE_BYTES] != current[offset:offset + SAMPLE_BYTES]:
            differences += 1
            if first is None:
                first = offset
            last = offset
            distance = abs(offset - ROM_LENGTH // 2)
            if distance < mid_distance:
                near_mid, mid_distance = offset, distance
    if differences < 2:
        raise IdentityError('need two distinct discriminating windows')
    offsets = list(dict.fromkeys((first, near_mid, last)))
    controls = (0, ROM_LENGTH // 4, ROM_LENGTH // 2, (ROM_LENGTH // SAMPLE_BYTES - 1) * SAMPLE_BYTES)
    control = next((o for o in controls if modified[o:o + SAMPLE_BYTES] == current[o:o + SAMPLE_BYTES]
                    and o not in offsets), None)
    if control is None:
        # Scan for any shared full eight-byte control (the input images are already memory-resident).
        control = next((o for o in range(0, ROM_LENGTH - SAMPLE_BYTES + 1, SAMPLE_BYTES)
                        if modified[o:o + SAMPLE_BYTES] == current[o:o + SAMPLE_BYTES]
                        and o not in offsets), None)
    if control is None:
        raise IdentityError('need a common control window')
    return [dict(offset=o, kind='discriminator', exact=modified[o:o + SAMPLE_BYTES].hex(),
                 protected=current[o:o + SAMPLE_BYTES].hex()) for o in offsets] + [
        dict(offset=control, kind='shared_control', exact=modified[control:control + SAMPLE_BYTES].hex(),
             protected=current[control:control + SAMPLE_BYTES].hex())]


class ReadOnlyRSP:
    """Minimal ACK-mode RSP client; all traffic and errors retained in bounded private log."""
    def __init__(self, conn, windows):
        self.conn = conn
        self.allowed = {f'm{ROM_BASE + w["offset"]:08x},{SAMPLE_BYTES:02x}' for w in windows}
        self.trace = []
        self.trace_bytes = 0
        self.dropped_bytes = 0
        self.dropped_events = 0

    def log(self, direction, payload):
        remaining = max(0, MAX_TRACE_BYTES - self.trace_bytes)
        saved = payload[:remaining] if len(self.trace) < MAX_TRACE_EVENTS else b''
        if saved:
            self.trace.append(dict(direction=direction, hex=saved.hex(), truncated=len(saved) != len(payload)))
            self.trace_bytes += len(saved)
        if not saved or len(saved) != len(payload):
            self.dropped_events += int(not saved)
            self.dropped_bytes += len(payload) - len(saved)

    def read_byte(self, raw):
        try:
            byte = self.conn.recv(1)
        except OSError:
            self.log('rx', bytes(raw))
            raise
        if not byte:
            self.log('rx', bytes(raw))
            raise IdentityError('RSP EOF, partial reply retained')
        raw.extend(byte)
        return byte

    def exchange(self, command):
        if command not in ('?', 'g') and command not in self.allowed:
            raise IdentityError('wire request denied by read-only whitelist')
        command_bytes = command.encode('ascii')
        packet = b'$' + command_bytes + b'#' + f'{sum(command_bytes) & 255:02x}'.encode('ascii')
        self.log('tx', packet)
        self.conn.sendall(packet)
        response = bytearray()
        try:
            if self.read_byte(response) != b'+':
                raise IdentityError('missing RSP ACK')
            if self.read_byte(response) != b'$':
                raise IdentityError('missing RSP frame start')
            payload = bytearray()
            while True:
                byte = self.read_byte(response)
                if byte == b'#':
                    break
                if byte == b'$' or len(payload) >= MAX_FRAME_BYTES:
                    raise IdentityError('nested or oversized RSP frame')
                payload.extend(byte)
            trailer = self.read_byte(response) + self.read_byte(response)
            try:
                received_sum = int(trailer, 16)
            except ValueError as error:
                raise IdentityError('invalid RSP checksum trailer') from error
            if (sum(payload) & 255) != received_sum:
                self.log('rx', bytes(response))
                self.log('tx', b'-')
                self.conn.sendall(b'-')
                raise IdentityError('bad RSP response checksum')
            self.log('rx', bytes(response))
            self.log('tx', b'+')
            self.conn.sendall(b'+')
            if b'*' in payload or b'}' in payload:
                raise IdentityError('unsupported RSP RLE/escape reply; raw preserved')
            try:
                return payload.decode('ascii')
            except UnicodeDecodeError as error:
                raise IdentityError('RSP reply not ASCII') from error
        except BaseException:
            # Raw receive bytes must be saved even on errors, without duplicating a completed frame.
            if not self.trace or self.trace[-1].get('direction') != 'rx' or self.trace[-1].get('hex') != response.hex():
                if response and (not any(t['direction'] == 'rx' and t['hex'] == response.hex() for t in self.trace[-3:])):
                    self.log('rx', bytes(response))
            raise


def run(modified_path, protected_path, output_path, port=2345, timeout=2.0):
    modified_path = Path(modified_path)
    protected_path = Path(protected_path)
    output_path = Path(output_path)
    if os.path.realpath(modified_path) == os.path.realpath(protected_path):
        raise IdentityError('ROM inputs alias')
    if os.path.realpath(output_path) in (os.path.realpath(modified_path), os.path.realpath(protected_path)):
        raise IdentityError('report aliases a ROM')
    if output_path.exists() or output_path.is_symlink():
        raise IdentityError('report must have a fresh, non-symlink path')
    if not 1 <= port <= 65535 or not 0.1 <= timeout <= 5:
        raise IdentityError('invalid port or timeout')

    # All file and window validation occurs before ANY debugger contact.
    exact = load_rom(modified_path, EXACT_MODIFIED_SHA)
    protected = load_rom(protected_path, PROTECTED_CURRENT_SHA)
    windows = choose_windows(exact, protected)
    result = dict(schema='rom-sampled-parity-v1', outcome='FAILED_PARTIAL',
                  input_exact_modified_sha256=EXACT_MODIFIED_SHA,
                  input_protected_current_sha256=PROTECTED_CURRENT_SHA,
                  emulator_loaded_rom_verified=False, emulator_loaded_save_verified=False,
                  host_battle_input_excluded=False, engine_request_verified=False,
                  native_acceptance=0, production_auto=0,
                  candidate_windows=windows, samples=[], raw_wire_trace=[],
                  wire_truncated=False, wire_dropped_bytes=0, wire_dropped_events=0,
                  stop_reply=None, g_reply_char_count=None, g_register_layout_verified=False,
                  failure=None, note='Sample parity only; neither complete ROM identity nor native gameplay is certified.')
    client = None
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=timeout) as connection:
            connection.settimeout(timeout)
            client = ReadOnlyRSP(connection, windows)
            result['stop_reply'] = client.exchange('?')
            if not result['stop_reply'].startswith(('S', 'T')):
                raise IdentityError('unexpected RSP stop reply; target may not be paused')
            g = client.exchange('g')
            result['g_reply_char_count'] = len(g)
            if len(g) % 2 or any(ch not in '0123456789abcdefABCDEF' for ch in g):
                raise IdentityError('unexpected g payload; raw saved, no register decoding')
            for window in windows:
                address = ROM_BASE + window['offset']
                response = client.exchange(f'm{address:08x},{SAMPLE_BYTES:02x}')
                try:
                    data = bytes.fromhex(response)
                except ValueError as error:
                    raise IdentityError('remote ROM sample not hex') from error
                if len(data) != SAMPLE_BYTES:
                    raise IdentityError('remote ROM sample length incorrect')
                row = dict(offset=window['offset'], kind=window['kind'],
                           observed=data.hex(), matches_exact_sample=data.hex() == window['exact'],
                           matches_protected_sample=data.hex() == window['protected'])
                result['samples'].append(row)
                if not row['matches_exact_sample']:
                    raise IdentityError('debugger memory sample disagrees with exact modified ROM')
            if not all(w['kind'] != 'discriminator' or not s['matches_protected_sample']
                       for w, s in zip(windows, result['samples'])):
                raise IdentityError('discriminator failed to separate protected ROM')
            result['outcome'] = 'SAMPLED_WINDOW_PARITY_ONLY'
    except (OSError, IdentityError) as error:
        result['failure'] = f'{type(error).__name__}: {error}'
    finally:
        if client:
            result['raw_wire_trace'] = client.trace
            result['wire_truncated'] = bool(client.dropped_bytes or client.dropped_events)
            result['wire_dropped_bytes'] = client.dropped_bytes
            result['wire_dropped_events'] = client.dropped_events
        try:
            if sha(modified_path) != EXACT_MODIFIED_SHA or sha(protected_path) != PROTECTED_CURRENT_SHA:
                result['outcome'] = 'FAILED_PARTIAL'
                result['failure'] = 'private ROM input changed during probe'
        except OSError as error:
            result['outcome'] = 'FAILED_PARTIAL'
            result['failure'] = f'ROM input unavailable for post-probe hash: {error}'
        fd = os.open(output_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(result, stream, sort_keys=True, indent=2)
            stream.write('\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exact-modified-rom', required=True)
    parser.add_argument('--protected-current-rom', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--port', type=int, default=2345)
    parser.add_argument('--timeout', type=float, default=2.0)
    args = parser.parse_args()
    result = run(args.exact_modified_rom, args.protected_current_rom,
                 args.report, args.port, args.timeout)
    print(json.dumps(dict(outcome=result['outcome'], failure=result['failure'],
                          observed=len(result['samples']), native_acceptance=0, production_auto=0)))
    if result['failure']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()