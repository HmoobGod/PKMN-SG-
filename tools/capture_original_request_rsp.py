#!/usr/bin/env python3
"""Local original-ROM GDB-RSP research observer; no native gameplay approval.

Only communicate with a pre-existing loopback debugger. Probe mode never
resumes the target. Capture is bounded, reports partial failures, and cannot
attest emulator-loaded ROM/save identity, host input, or one-use AI authority.
All reports contain private data and must remain OFF public GitHub.
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
PCS = (0x0806BD80, 0x0806B370, 0x0806B3A6, 0x0806261C,
       0x08094330, 0x0809435C, 0x08094374, 0x08094380,
       0x0809E6BA, 0x0808E336)
COPY_ENTRY, COPY_DONE, PP_WRITER, MAIN_CLEAR = 0x0806B370, 0x0806B3A6, 0x0809E6BA, 0x0808E336
SRC_BASE, DST_PLAYER0, DST_OTHER = 0x0201CF94, 0x0201C794, 0x0201C994
PP_BASE, MAIN_BYTE = 0x02001EF1, 0x03005A0D
# ONLY independently observed original memory locations. A valid EWRAM pointer
# is not necessarily permission to read it through the debugger.
READ_WINDOWS = ((SRC_BASE, SRC_BASE+6), (DST_PLAYER0, DST_PLAYER0+6),
                (DST_OTHER, DST_OTHER+6), (PP_BASE, PP_BASE+4),
                (MAIN_BYTE, MAIN_BYTE+1))
MAX_PACKET = 65536
HEX = re.compile(rb'[0-9a-fA-F]*\Z')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path, size, expected):
    p = Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size == size,
            'invalid private ROM/save file')
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    value = h.hexdigest()
    require(value == expected, 'wrong exact private ROM/save identity')
    return value


def ewram(address, count):
    return type(address) is int and type(count) is int and 0 < count <= 6 and \
        0x02000000 <= address and address+count <= 0x02040000


def permitted_memory(address, count):
    return type(address) is int and type(count) is int and 0 < count <= 6 and any(
        lo <= address and address+count <= hi for lo, hi in READ_WINDOWS)


class RSP:
    """Minimal ACK-mode client. The public send path enforces every address."""
    def __init__(self, sock):
        self.sock = sock
        self.running = False
        self._pp_step_armed = False

    def _byte(self):
        b = self.sock.recv(1)
        if not b:
            raise ConnectionError('GDB disconnected')
        return b

    def _validate(self, command):
        require(type(command) is str and command.isascii() and
                len(command) < 160 and '\x00' not in command,
                'invalid debugger command')
        require(not self.running, 'target is running; interrupt before debugger access')
        if command in ('?', 'g'):
            return
        if command == 'c':
            require(not self.running, 'cannot resume an already-running target')
            return
        if command == 's':
            require(self._pp_step_armed and not self.running,
                    'single step requires immediate validated player0 PP stop')
            return
        match = re.fullmatch(r'm([0-9a-f]{8}),([1-6])', command)
        if match:
            require(permitted_memory(int(match[1], 16), int(match[2], 16)),
                    'memory address outside named read windows')
            return
        match = re.fullmatch(r'([Zz])0,([0-9a-f]{8}),2', command)
        if match:
            require(int(match[2], 16) in PCS, 'breakpoint outside original PC whitelist')
            require(not self.running, 'cannot modify breakpoints while running')
            return
        raise ValueError('forbidden debugger operation')

    def _transmit(self, command):
        self._validate(command)
        if command == 's':
            self._pp_step_armed = False  # one-use even if the packet fails
        else:
            self._pp_step_armed = False  # no deferred stepping after intervening commands
        data = command.encode('ascii')
        self.sock.sendall(b'$' + data + b'#%02x' % (sum(data) & 255))
        require(self._byte() == b'+', 'GDB did not ACK request')

    def receive(self):
        # A timeout *before* a frame can mean a still-running game. Once a
        # frame begins, any timeout is an error, not a reusable half-packet.
        for _ in range(MAX_PACKET):
            b = self._byte()
            if b == b'$':
                break
            require(b == b'+', 'unexpected/stale debugger stream prefix')
        else:
            raise ValueError('missing GDB response frame')
        payload = bytearray()
        try:
            while True:
                b = self._byte()
                if b == b'#':
                    break
                require(len(payload) < MAX_PACKET and b != b'$',
                        'oversize or nested GDB packet')
                # Unsupported RSP escape or RLE must fail closed, not misdecode.
                require(b not in (b'}', b'*'), 'unsupported GDB escaped/RLE payload')
                payload.extend(b)
            trailer = self._byte()+self._byte()
        except socket.timeout as error:
            raise ValueError('timeout inside GDB response frame') from error
        require(re.fullmatch(rb'[0-9a-fA-F]{2}', trailer), 'invalid GDB checksum text')
        if sum(payload) & 255 != int(trailer, 16):
            self.sock.sendall(b'-')
            raise ValueError('GDB packet checksum mismatch')
        self.sock.sendall(b'+')
        return bytes(payload)

    def send(self, command):
        require(command != 'c', 'use bounded resume instead of raw c')
        if command == 's':
            try:
                self._transmit(command)
            finally:
                # If ACK fails the guest may already be stepping.
                self.running = True
            result = self.receive()
            parse_stop(result)
            self.running = False
            return result
        self._transmit(command)
        return self.receive()

    def arm_pp_step(self, original_pc):
        require(original_pc == PP_WRITER and not self.running and
                not self._pp_step_armed, 'PP step can only follow validated PP marker')
        self._pp_step_armed = True

    def resume(self, absolute_deadline, per_receive_timeout):
        try:
            try:
                self._transmit('c')
            finally:
                self.running = True  # even an ACK failure may leave guest running
            while time.monotonic() < absolute_deadline:
                remaining = absolute_deadline - time.monotonic()
                self.sock.settimeout(max(0.001, min(per_receive_timeout, remaining)))
                try:
                    stop = parse_stop(self.receive())
                except socket.timeout:
                    continue  # no frame started; target still running
                self.running = False
                return stop, False
            # Overall deadline: interrupt and drain before removing any BP.
            return self.interrupt_stop(max_wait=min(3.0, per_receive_timeout)), True
        except BaseException:
            raise

    def interrupt_stop(self, max_wait=2.0):
        require(self.running, 'interrupt reserved for running target')
        self.sock.sendall(b'\x03')  # GDB out-of-band interrupt; no guest write
        deadline = time.monotonic()+max_wait
        while time.monotonic() < deadline:
            self.sock.settimeout(max(0.001, min(0.2, deadline-time.monotonic())))
            try:
                stop = parse_stop(self.receive())
            except socket.timeout:
                continue
            self.running = False
            return stop
        raise TimeoutError('GDB interrupt stop not received; breakpoints left installed')


def parse_registers(packet):
    require(len(packet) >= 128 and len(packet) % 2 == 0 and HEX.fullmatch(packet),
            'missing/malformed ARM register packet')
    raw = bytes.fromhex(packet[:128].decode('ascii'))
    return [int.from_bytes(raw[i*4:(i+1)*4], 'little') for i in range(16)]


def parse_stop(packet):
    require(re.fullmatch(rb'(?:S[0-9a-fA-F]{2}|T[0-9a-fA-F]{2}[^\r\n]*)', packet),
            'GDB response is not a CPU stop')
    return packet.decode('ascii')[:200]


def read_memory(rsp, address, count):
    require(permitted_memory(address, count), 'memory outside named read windows')
    raw = rsp.send(f'm{address:08x},{count:x}')
    require(len(raw) == count*2 and HEX.fullmatch(raw), 'incomplete CPU memory read')
    return bytes.fromhex(raw.decode('ascii'))


def private_write(path, report):
    # Exclusive creation with owner-only permissions, including partial traces.
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write('\n')


def match_pc(raw_pc, bias):
    possibilities = [(pc, raw_pc-pc) for pc in PCS if raw_pc-pc in (0, 2, 4)]
    require(len(possibilities) == 1, 'unknown/ambiguous original breakpoint stop')
    matched, observed_bias = possibilities[0]
    require(bias is None or observed_bias == bias, 'original CPU PC bias changed')
    return matched, observed_bias


def run_capture(rom, save, output, port, max_stops=40, timeout=10,
                deadline_seconds=120, probe_only=False):
    require(type(max_stops) is int and 1 <= max_stops <= 200, 'invalid stop budget')
    require(type(timeout) in (int, float) and 0 < timeout <= 30, 'invalid timeout')
    require(type(deadline_seconds) in (int, float) and 0 < deadline_seconds <= 1800,
            'invalid capture deadline')
    require(type(port) is int and 1024 <= port < 65536, 'invalid loopback port')
    out = Path(output)
    require(out.resolve() not in (Path(rom).resolve(), Path(save).resolve()),
            'output cannot replace private inputs')
    require(not out.exists() and not out.is_symlink(), 'output exists; refuse overwrite')
    initial = (digest(rom, 33554432, EXACT_ROM), digest(save, 131072, EXACT_SAVE))
    report = dict(
        schema='sg-exact-original-rsp-actor0-observer-v2',
        input_file_rom_sha256=initial[0], input_file_save_sha256=initial[1],
        run_id='native-' + secrets.token_hex(16), recorder_pid=os.getpid(),
        recorder_start_epoch=time.time(), observer_only=True,
        tool_sent_battle_commands=0, tool_sent_guest_writes=0,
        operator_input_log='NOT_RECORDED', host_input_during_battle='NOT_EXCLUDED',
        emulator_loaded_rom_verified=False, emulator_loaded_save_verified=False,
        new_auto_hook_executed_proven=False, engine_issued_one_use_request_proven=False,
        dynamic_legality_proven=False, native_acceptance=0,
        probe_only=probe_only, probe_transcript=None, events=[],
        marker_stop_count=0, stop_budget_reached=False, deadline_reached=False,
        failure=None, pc_bias=None,
        interrupt_stop=None, input_files_unchanged=False,
        leftover_breakpoints=[], cleanup_errors=[])
    installed = []
    rsp = None
    started = time.monotonic()
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            rsp = RSP(sock)
            try:
                stop = rsp.send('?')
                parse_stop(stop)
                if probe_only:
                    raw_regs = rsp.send('g')
                    parse_registers(raw_regs)
                    raw_bytes = rsp.send(f'm{SRC_BASE:08x},6')
                    require(len(raw_bytes) == 12 and HEX.fullmatch(raw_bytes),
                            'invalid GDB probe memory response')
                    report['probe_transcript'] = dict(
                        stop_raw_ascii=stop.decode('ascii'), registers_raw_hex=raw_regs.decode('ascii'),
                        register_payload_bytes=len(raw_regs)//2,
                        named_memory_address=f'0x{SRC_BASE:08x}',
                        named_memory_response_hex=raw_bytes.decode('ascii'))
                else:
                    absolute_deadline = started + deadline_seconds
                    for pc in PCS:
                        remaining = absolute_deadline-time.monotonic()
                        require(remaining > 0, 'capture deadline expired during setup')
                        sock.settimeout(min(timeout, remaining))
                        installed.append(pc)  # cleanup even if ACK/response is lost
                        require(rsp.send(f'Z0,{pc:08x},2') == b'OK',
                                'debugger breakpoint rejected')
                    active_copy = None
                    for _ in range(max_stops):
                        if time.monotonic() >= absolute_deadline:
                            report['deadline_reached'] = True
                            break
                        stop, deadline_hit = rsp.resume(absolute_deadline, timeout)
                        if deadline_hit:
                            report['deadline_reached'] = True
                            report['interrupt_stop'] = stop
                            break
                        regs = parse_registers(rsp.send('g'))
                        raw_pc = regs[15]
                        marker, bias = match_pc(raw_pc, report['pc_bias'])
                        report['pc_bias'] = bias
                        event = dict(seq=len(report['events']), elapsed_monotonic=time.monotonic()-started,
                                     stop=stop, raw_pc=f'0x{raw_pc:08x}',
                                     candidate_original_pc=f'0x{marker:08x}',
                                     registers_r0_r15=[f'0x{x:08x}' for x in regs],
                                     actor0_marker_only=False)
                        if marker == COPY_ENTRY and regs[0] == 0 and regs[1] == 1 and regs[3] == 6:
                            ptr = regs[2]
                            event['copy_entry_src_register_r2'] = f'0x{ptr:08x}'
                            if permitted_memory(ptr, 6):
                                active_copy = (ptr, read_memory(rsp, ptr, 6))
                                event['source6_hex_private'] = active_copy[1].hex()
                                event['actor0_marker_only'] = True
                        elif marker == COPY_DONE and active_copy is not None:
                            src, before = active_copy
                            # r0 is an observed candidate pointer, NOT a proven engine destination.
                            candidate = regs[0]
                            event['epilogue_r0_candidate_destination'] = f'0x{candidate:08x}'
                            event['destination_is_player0_buffer'] = candidate == DST_PLAYER0
                            event['destination_is_other_buffer'] = candidate == DST_OTHER
                            event['copy_register_r4_matches_entry_src'] = regs[4] == src
                            if regs[4] == src and permitted_memory(candidate, 6):
                                source_now = read_memory(rsp, src, 6)
                                destination = read_memory(rsp, candidate, 6)
                                event['six_byte_pair_equal'] = before == source_now == destination
                                event['dest6_hex_private'] = destination.hex()
                                event['actor0_marker_only'] = True
                            active_copy = None
                        elif marker == PP_WRITER:
                            event['pp_register_r0_actor'] = regs[0]
                            event['pp_register_r1_address'] = f'0x{regs[1]:08x}'
                            event['pp_register_r6_value'] = f'0x{regs[6]:08x}'
                            if regs[0] == 0 and PP_BASE <= regs[1] < PP_BASE+4:
                                before = read_memory(rsp, regs[1], 1)[0]
                                event['pp_before'] = before
                                rsp.arm_pp_step(marker)
                                step_stop = rsp.send('s')
                                step_regs = parse_registers(rsp.send('g'))
                                require(step_regs[15] == raw_pc+2,
                                        'PP single-step did not advance one Thumb instruction')
                                after = read_memory(rsp, regs[1], 1)[0]
                                event.update(pp_single_step_stop=parse_stop(step_stop),
                                             pp_after=after,
                                             pp_decrement_observed=(before > 0 and after == before-1 and
                                                                    after == (regs[6] & 255)),
                                             pp_store_value_matches_r6=(after == (regs[6] & 255)))
                        elif marker == MAIN_CLEAR:
                            event['main_byte_before_only'] = read_memory(rsp, MAIN_BYTE, 1)[0]
                        # A copy must be adjacent in the observed marker sequence.
                        # Never join an entry with a later unrelated epilogue.
                        if active_copy is not None and marker not in (COPY_ENTRY, COPY_DONE):
                            active_copy = None
                            event['incomplete_previous_copy_pair'] = True
                        report['events'].append(event)
                        report['marker_stop_count'] += 1
                    else:
                        report['stop_budget_reached'] = True
            finally:
                # On an error, stop the running guest *before* debugger cleanup.
                # Never send z0 to a known-running target. Bound all cleanup.
                if rsp is not None and rsp.running:
                    try:
                        report['interrupt_stop'] = rsp.interrupt_stop(max_wait=2.0)
                    except (OSError, ConnectionError, TimeoutError, ValueError) as error:
                        report['cleanup_errors'].append('interrupt: '+str(error))
                if rsp is not None and not rsp.running:
                    cleanup_deadline = time.monotonic()+3.0
                    for pc in reversed(installed):
                        remaining = cleanup_deadline-time.monotonic()
                        if remaining <= 0:
                            report['cleanup_errors'].append('breakpoint cleanup time budget expired')
                            break
                        sock.settimeout(min(0.25, remaining))
                        try:
                            require(rsp.send(f'z0,{pc:08x},2') == b'OK', 'breakpoint removal rejected')
                            installed.remove(pc)
                        except (OSError, ConnectionError, TimeoutError, ValueError) as error:
                            report['cleanup_errors'].append(f'0x{pc:08x}: '+str(error))
                report['leftover_breakpoints'] = [f'0x{x:08x}' for x in installed]
    except (Exception, KeyboardInterrupt) as error:
        report['failure'] = type(error).__name__+': '+str(error)
    try:
        report['input_files_unchanged'] = (
            digest(rom, 33554432, EXACT_ROM), digest(save, 131072, EXACT_SAVE)) == initial
    except (OSError, ValueError) as error:
        report['failure'] = (report['failure']+'; ' if report['failure'] else '') + \
                            'input rehash: '+str(error)
    if report['deadline_reached'] and not report['failure']:
        report['failure'] = 'overall capture deadline reached; partial evidence only'
    if report['cleanup_errors'] and not report['failure']:
        report['failure'] = 'debugger cleanup incomplete'
    # Stop budget is descriptive, NEVER a native acceptance/completion claim.
    private_write(out, report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('rom', 'save', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--port', type=int, required=True)
    p.add_argument('--max-stops', type=int, default=40)
    p.add_argument('--timeout', type=float, default=10)
    p.add_argument('--deadline-seconds', type=float, default=120)
    p.add_argument('--probe-only', action='store_true')
    a = p.parse_args()
    result = run_capture(a.rom, a.save, a.output, a.port,
                         a.max_stops, a.timeout, a.deadline_seconds, a.probe_only)
    print(json.dumps(dict(recorded_stops=len(result['events']),
                          capture_status='FAILED_OR_PARTIAL' if result['failure'] else 'RESEARCH_ONLY',
                          failure=result['failure'], native_gameplay_acceptance=0), sort_keys=True))
    if result['failure']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()