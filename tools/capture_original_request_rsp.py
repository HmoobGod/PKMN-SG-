#!/usr/bin/env python3
"""Bounded local mGBA GDB-RSP read-only actor0 evidence capture (research HOLD).

Connect only to an already-running loopback GDB server with the exact, private,
modified test ROM. Uses debugger breakpoints and register/EWRAM reads; NEVER
sends keys, guest writes, emulator savestates, or an automatic battle command.
A matched marker is not evidence of an engine-owned one-use request or of
Smart Auto-Battle running. Records remain PRIVATE and are never CI fixtures.
"""
import argparse
import hashlib
import json
import os
import re
import secrets
import socket
import time
from pathlib import Path

EXACT_ROM = '4b2585e10265805da12016819c880a4acd50eda2aa24ce977d1dbcc705d3ee44'
EXACT_SAVE = '8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4'
# Original, unpatched instruction PCs. This list is not an injection map.
PCS = (0x0806BD80, 0x0806B370, 0x0806B3A6, 0x0806261C,
       0x08094330, 0x0809435C, 0x08094374, 0x08094380,
       0x0809E6BA, 0x0808E336)
COPY_ENTRY, COPY_DONE = 0x0806B370, 0x0806B3A6
SRC_BASE, DST_PLAYER0, DST_OTHER = 0x0201CF94, 0x0201C794, 0x0201C994
PP_BASE = 0x02001EF1
MAX_PACKET = 65536
HEX = re.compile(rb'[0-9a-fA-F]*\Z')


def require(ok, why):
    if not ok:
        raise ValueError(why)


def digest(path, length, expected):
    p = Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size == length,
            'invalid private ROM/save file')
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    result = h.hexdigest()
    require(result == expected, 'wrong exact private ROM/save identity')
    return result


def ewram(addr, length):
    return type(addr) is int and type(length) is int and 0 < length <= 6 and \
        0x02000000 <= addr and addr + length <= 0x02040000


class RSP:
    """Strict ACK-mode read-only subset; the only non-read commands set/clear breakpoints and resume."""
    def __init__(self, sock):
        self.sock = sock

    def _byte(self):
        b = self.sock.recv(1)
        if not b:
            raise ConnectionError('GDB disconnected')
        return b

    def send(self, command):
        require(type(command) is str and command.isascii() and
                len(command) < 160 and '\x00' not in command,
                'invalid debugger command')
        # Explicit finite whitelist. NO P/G/M/X/vRun, emulator keys or state restore.
        allowed = command in ('?', 'g', 'c') or \
                  re.fullmatch(r'm[0-9a-f]{8},[1-6]', command) or \
                  re.fullmatch(r'[Zz]0,[0-9a-f]{8},2', command)
        require(allowed, 'forbidden debugger operation')
        data = command.encode('ascii')
        self.sock.sendall(b'$' + data + b'#%02x' % (sum(data) & 255))
        ack = self._byte()
        require(ack == b'+', 'GDB did not ACK request')
        return self.receive()

    def receive(self):
        # Ignore only ACKs; never interpret stray printable console output as a stop.
        for _ in range(MAX_PACKET):
            b = self._byte()
            if b == b'$':
                break
            require(b in (b'+',), 'unexpected debugger stream prefix')
        else:
            raise ValueError('missing GDB response frame')
        payload = bytearray()
        while True:
            b = self._byte()
            if b == b'#':
                break
            require(len(payload) < MAX_PACKET and b != b'$', 'oversize or nested GDB packet')
            payload.extend(b)
        trailer = self._byte() + self._byte()
        require(re.fullmatch(rb'[0-9a-fA-F]{2}', trailer), 'invalid GDB checksum text')
        if sum(payload) & 255 != int(trailer, 16):
            self.sock.sendall(b'-')
            raise ValueError('GDB packet checksum mismatch')
        self.sock.sendall(b'+')
        return bytes(payload)


def parse_registers(packet):
    # ARM RSP first 16 32-bit little-endian core registers. More registers may follow.
    require(len(packet) >= 128 and len(packet) % 2 == 0 and HEX.fullmatch(packet),
            'missing/malformed ARM register packet')
    b = bytes.fromhex(packet[:128].decode('ascii'))
    regs = [int.from_bytes(b[i*4:(i+1)*4], 'little') for i in range(16)]
    return regs


def parse_stop(packet):
    require(re.fullmatch(rb'[ST][0-9a-fA-F]{2}(?:.*)?', packet),
            'GDB response is not a CPU stop')
    # A native GDB stub reports signals, but these are not proof of OS process identity.
    return packet.decode('ascii', errors='replace')[:200]


def read_memory(rsp, addr, count):
    require(ewram(addr, count), 'untrusted EWRAM pointer')
    raw = rsp.send(f'm{addr:08x},{count:x}')
    require(len(raw) == count * 2 and HEX.fullmatch(raw), 'incomplete CPU memory read')
    return bytes.fromhex(raw.decode('ascii'))


def run_capture(rom, save, output, port, max_stops=40, timeout=10):
    require(type(max_stops) is int and 1 <= max_stops <= 200, 'invalid stop budget')
    require(type(timeout) in (int, float) and 0 < timeout <= 30, 'invalid timeout')
    require(type(port) is int and 1024 <= port < 65536, 'invalid loopback port')
    out = Path(output)
    require(not out.exists() and not out.is_symlink(), 'output exists; refuse overwrite')
    require(out.resolve() not in (Path(rom).resolve(), Path(save).resolve()),
            'output cannot replace private inputs')
    initial = (digest(rom, 33554432, EXACT_ROM), digest(save, 131072, EXACT_SAVE))
    report = {'schema': 'sg-exact-original-rsp-actor0-observer-v1',
              'rom_sha256': initial[0], 'save_sha256': initial[1],
              'run_id': 'native-' + secrets.token_hex(16),
              'recorder_pid': os.getpid(), 'recorder_start_epoch': time.time(),
              'observer_only': True, 'host_battle_commands': 0,
              'guest_memory_writes': 0, 'new_auto_hook_executed_proven': False,
              'engine_issued_one_use_request_proven': False,
              'dynamic_legality_proven': False, 'native_acceptance': 0,
              'events': [], 'completed_capture': False}
    with socket.create_connection(('127.0.0.1', port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        rsp = RSP(sock)
        parse_stop(rsp.send('?'))  # Need a genuinely attached/paused GDB target.
        installed = []
        try:
            for pc in PCS:
                require(rsp.send(f'Z0,{pc:08x},2') == b'OK', 'breakpoint rejected')
                installed.append(pc)
            active_copy = None
            for _ in range(max_stops):
                stop = parse_stop(rsp.send('c'))
                regs = parse_registers(rsp.send('g'))
                # mGBA/ARM may report next pipelined PC: record raw and both candidates.
                pc = regs[15]
                matched = next((x for x in PCS if pc in (x, x+2, x+4)), None)
                event = {'seq': len(report['events']), 'elapsed_monotonic':
                         time.monotonic(), 'stop': stop, 'raw_pc': f'0x{pc:08x}',
                         'candidate_original_pc': f'0x{matched:08x}' if matched else None,
                         'registers_r0_r4': [f'0x{r:08x}' for r in regs[:5]],
                         'actor0_marker_only': False}
                if matched is not None:
                    if matched == COPY_ENTRY and regs[0] == 0 and regs[1] == 1 and regs[3] == 6:
                        # Source pointer must be measured from paused CPU, not presumed by address.
                        source_ptr = regs[2]
                        if ewram(source_ptr, 6):
                            active_copy = (source_ptr, read_memory(rsp, source_ptr, 6))
                            event['copy_entry_src'] = f'0x{source_ptr:08x}'
                            event['source6_hex_private'] = active_copy[1].hex()
                            event['actor0_marker_only'] = True
                    elif matched == COPY_DONE and active_copy is not None:
                        src, before = active_copy
                        if regs[4] == src:
                            source_now = read_memory(rsp, src, 6)
                            dest = read_memory(rsp, DST_PLAYER0, 6)
                            event['six_byte_pair_equal'] = before == source_now == dest
                            event['copy_destination'] = f'0x{DST_PLAYER0:08x}'
                            event['dest6_hex_private'] = dest.hex()
                            event['actor0_marker_only'] = True
                        active_copy = None
                    elif matched == 0x0809E6BA:
                        event['pp_slots_private'] = list(read_memory(rsp, PP_BASE, 4))
                report['events'].append(event)
            report['completed_capture'] = True
        finally:
            # Debugger cleanup, not an emulator/gameplay operation; never continue on error.
            for pc in reversed(installed):
                try:
                    rsp.send(f'z0,{pc:08x},2')
                except (OSError, ValueError, ConnectionError):
                    pass
    require((digest(rom, 33554432, EXACT_ROM), digest(save, 131072, EXACT_SAVE)) == initial,
            'original private files changed during capture')
    # No report before a complete and verified cleanup; keep trace private.
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write('\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('rom', 'save', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--port', type=int, required=True)
    p.add_argument('--max-stops', type=int, default=40)
    p.add_argument('--timeout', type=float, default=10)
    a = p.parse_args()
    result = run_capture(a.rom, a.save, a.output, a.port, a.max_stops, a.timeout)
    print(json.dumps({'recorded_stops': len(result['events']),
                      'native_gameplay_acceptance': 0,
                      'one_use_request_authority_proven': False}, sort_keys=True))

if __name__ == '__main__':
    main()