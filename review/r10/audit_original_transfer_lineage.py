#!/usr/bin/env python3
"""Offline source-only validator for original *guest CPU store* provenance.

Never uploads or embeds any ROM/save/CPU log. The exact-ROM memory addresses,
opcode PCs, and private source rows are supplied only by an authorized private
caller. Even a valid report is evidence for the EXISTING ROM, NOT an installed
Smart Auto-Battle patch, native legality, safety, or a working manual fallback.
"""
from dataclasses import dataclass
from collections import Counter
import re

MAX_ROWS = 20000
MAX_FRAME = 1000000
MAX_PP_DISTANCE = 90
_HEX40 = re.compile(r'[0-9a-fA-F]{80}\Z')


@dataclass(frozen=True)
class Pins:
    transfer_buffer: int
    player_receive_buffer: int
    other_receive_buffer: int
    header_writer_pc: int
    payload_writer_pc: int
    copy_writer_pc: int
    response_writer_pc: int
    original_fight_lr: int
    original_move_lr: int
    original_pp_raw_pc: int
    player_pp_base: int


class EvidenceError(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise EvidenceError(reason)


def number(x, name):
    require(type(x) is int and 0 <= x <= 0xffffffff, f'invalid {name}')
    return x


def load_rows(rows, fields, limit=MAX_ROWS):
    require(type(rows) is list and 0 < len(rows) <= limit, 'missing/unbounded rows')
    for row in rows:
        require(type(row) is dict, 'row not a dict')
        require(all(k in row for k in fields), 'missing required row field')
        number(row['f'], 'frame')
        require(row['f'] <= MAX_FRAME, 'frame too large')
    return rows


def parse_hex40(value):
    require(type(value) is str and _HEX40.fullmatch(value) is not None,
            'exact 40-byte CPU-memory state required')
    return bytes.fromhex(value)


def valid_choosemove(buf):
    if len(buf) != 40 or buf[:4] != b'\x13\0\0\0':
        return False
    for i in range(4):
        move = buf[4 + 2*i] | buf[5 + 2*i] << 8
        current, maximum = buf[12+i], buf[16+i]
        if maximum < current or (move != 0 and maximum == 0) or (move == 0 and (current != 0 or maximum != 0)):
            return False
    return True


def normalize_store(e):
    f = number(e['f'], 'frame')
    pc = number(e['pc'], 'PC')
    base = number(e['base'], 'base')
    dst = number(e['dst'], 'destination')
    width = number(e['width'], 'width')
    require(width in (1, 2, 4) and base <= dst < base+40,
            'misaligned store or invalid width')
    return f, pc, base, dst, parse_hex40(e['before']), parse_hex40(e['after'])


def audit(store_rows, response_rows, pp_rows, pins, *, require_other=True):
    require(isinstance(pins, Pins), 'missing private pin configuration')
    for x in pins.__dict__.values():
        number(x, 'pin')
    require(len({pins.transfer_buffer, pins.player_receive_buffer,
                 pins.other_receive_buffer}) == 3, 'overlapping actor buffers')
    load_rows(store_rows, ('f', 'pc', 'base', 'dst', 'width', 'before', 'after'))
    load_rows(response_rows, ('f', 'pc', 'lr', 'value', 'actor'))
    load_rows(pp_rows, ('f', 'raw_pc', 'address', 'width', 'before', 'after', 'target'))
    stores = [(*normalize_store(e), i) for i, e in enumerate(store_rows)]
    require(all(0 <= stores[i][0] <= stores[i+1][0] for i in range(len(stores)-1)),
            'out-of-order original CPU stores')
    for e in response_rows:
        for k in ('pc','lr','value','actor'): number(e[k], k)
    for e in pp_rows:
        for k in ('raw_pc','address','width','before','after','target'): number(e[k],k)
    response_rows = sorted(response_rows, key=lambda e: e['f'])
    pp_rows = sorted(pp_rows, key=lambda e: e['f'])
    # Require the final store-observed player controller state in the frame;
    # a partially constructed 40-byte buffer can accidentally look valid.
    player_last = {}
    for row in stores:
        f,pc,base,dst,b,a,i = row
        if base == pins.player_receive_buffer and pc == pins.copy_writer_pc:
            player_last[f] = row
    # Every original actor0 Move response in the evidence scope requires one
    # complete player controller request; never silently drop a bad frame.
    fight_frames = [e['f'] for e in response_rows
                   if e['actor'] == 0 and e['pc'] == pins.response_writer_pc
                   and e['lr'] == pins.original_fight_lr and e['value'] == 0]
    move_frames = [e['f'] for e in response_rows
                  if e['actor'] == 0 and e['pc'] == pins.response_writer_pc
                  and e['lr'] == pins.original_move_lr and e['value'] == 10]
    require(move_frames and len(set(move_frames)) == len(move_frames) and
            len(set(fight_frames)) == len(fight_frames) and
            sorted(x+1 for x in fight_frames) == sorted(move_frames),
            'missing, duplicated or unmatched original player0 Fight→Move')
    frames = sorted(move_frames)
    require(all(f in player_last and valid_choosemove(player_last[f][5])
                for f in frames), 'missing/malformed original player controller request')
    found = []
    for j, frame in enumerate(frames):
        segment = [(f,pc,base,dst,b,a,i) for f,pc,base,dst,b,a,i in stores if f == frame]
        terminal = player_last[frame]
        candidate = terminal[5]
        first_full_copy = terminal[6]
        emit = [(i,b,a) for f,pc,base,dst,b,a,i in segment
                if base == pins.transfer_buffer and pc == pins.header_writer_pc
                and dst == pins.transfer_buffer and b[0] != 19 and a[0] == 19]
        require(len(emit) == 1, 'missing or ambiguous original command header emission')
        emitted_at = emit[0][0]
        assembled = [(i,a) for f,pc,base,dst,b,a,i in segment
                     if base == pins.transfer_buffer and pc == pins.payload_writer_pc
                     and emitted_at < i < first_full_copy and a == candidate]
        require(assembled, 'no CPU-authenticated original byte-by-byte payload assembly')
        require(any(e['f'] == frame-1 and e['actor'] == 0 and e['pc'] == pins.response_writer_pc
                    and e['lr'] == pins.original_fight_lr and e['value'] == 0
                    for e in response_rows), 'missing original player Fight response')
        require(any(e['f'] == frame and e['actor'] == 0 and e['pc'] == pins.response_writer_pc
                    and e['lr'] == pins.original_move_lr and e['value'] == 10
                    for e in response_rows), 'missing original player Move response')
        if require_other:
            other = [row for row in segment if row[2] == pins.other_receive_buffer
                     and row[1] == pins.copy_writer_pc]
            require(other and valid_choosemove(other[-1][5]) and
                    other[-1][5] != candidate,
                    'other controller was not independently distinguished')
        next_frame = frames[j+1] if j+1 < len(frames) else frame+MAX_PP_DISTANCE+1
        pp_hits = [e for e in pp_rows
                   if frame < e['f'] < min(frame+MAX_PP_DISTANCE+1,next_frame)
                   and e['raw_pc'] == pins.original_pp_raw_pc
                   and e['width'] == 1 and e['target'] == 0
                   and pins.player_pp_base+0x25 <= e['address'] <= pins.player_pp_base+0x28]
        require(len(pp_hits) == 1, 'missing/duplicate authenticated player PP writer')
        pp = pp_hits[0]
        slot = pp['address'] - (pins.player_pp_base+0x25)
        require(0 <= slot <= 3, 'PP slot outside original four slots')
        require(candidate[12+slot] == pp['before'] and pp['before'] == pp['after']+1,
                'PP not a single corresponding original store decrement')
        require(candidate[4+2*slot] | candidate[5+2*slot] << 8 != 0,
                'PP debit on empty move slot')
        if j+1 < len(frames):
            next_candidate = player_last[frames[j+1]][5]
            require(next_candidate[12+slot] == pp['after'],
                    'next original request does not reflect observed PP debit')
        found.append({'frame':frame, 'pp_writer_frame':pp['f'], 'debited_slot':slot,
                      'original_transfer_to_player_candidate_UNVERIFIED':True,
                      'installed_adapter_executed':False, 'native_accepted':0})
    return {'schema':'sg-original-cpu-request-pp-lineage-r10-source-only',
            'candidates':found, 'formal_native_acceptance':0,
            'native_legality_certified':False,
            'manual_fallback_certified':False,
            'no_forced_switch_certified':False,
            'production_authorized':False}
