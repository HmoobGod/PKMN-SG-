#!/usr/bin/env python3
"""Offline, read-only ROM dispatch/call-edge identity gate.

The caller supplies the ROM through a private local path. No bytes, save data,
RAM records, or absolute filesystem paths are emitted into the public report.
This tool establishes bounded machine-code control flow, NEVER C source identity,
legal moves, engine-owned auto decisions, or manual fallback.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROM_START = 0x08000000
COMMAND_TABLE = 0x08444508
COMMAND_CHOOSE_ACTION = 17
COMMAND_CHOOSE_MOVE = 19
PLAYER_ACTION_HANDLER = 0x08065E9C
PLAYER_MOVE_HANDLER = 0x08065EB4
PLAYER_MOVE_WRAPPER_CALL = 0x08065B1A
ACTION_HELPER_CALL = 0x08065EA4
ACTION_COMPLETE_CALL = 0x08065EAA
MOVE_EMIT_CALL = 0x08065F28
MOVE_COMPLETE_CALL = 0x08065F2E
EXPECTED_EMITTER = 0x0806BD80
EXPECTED_COMPLETE = 0x0806C2EC
AUTO_ACTION_FIGHT_EMIT_CALL = 0x0801720C
AUTO_ACTION_SWITCH_EMIT_CALL = 0x08017236


def read_int(rom, address, width):
    if type(address) is not int or type(width) is not int or width not in (2, 4):
        raise ValueError('unsupported address or width')
    i = address - ROM_START
    if i < 0 or i + width > len(rom):
        raise ValueError('outside ROM')
    return int.from_bytes(rom[i:i + width], 'little')


def thumb_bl(rom, pc):
    """Thumb-1 BL, encoding two halfwords; reject non-BL prefixes and overflow."""
    try:
        a, b = read_int(rom, pc, 2), read_int(rom, pc + 2, 2)
    except ValueError:
        return None
    if a & 0xF800 != 0xF000 or b & 0xF800 != 0xF800:
        return None
    disp = ((a & 0x7FF) << 12) | ((b & 0x7FF) << 1)
    if disp & 0x400000:
        disp -= 0x800000
    return (pc + 4 + disp) & 0xFFFFFFFF


def assess(rom):
    if not isinstance(rom, (bytes, bytearray, memoryview)):
        raise ValueError('ROM must be a bytes-like object')
    if len(rom) != 0x2000000:
        raise ValueError('not a 32 MiB GBA ROM')
    dispatch = {
        'choose_action': read_int(rom, COMMAND_TABLE + 4 * COMMAND_CHOOSE_ACTION, 4),
        'choose_move': read_int(rom, COMMAND_TABLE + 4 * COMMAND_CHOOSE_MOVE, 4),
    }
    checks = {
        'chosen_action_dispatch_pointer': dispatch['choose_action'] == PLAYER_ACTION_HANDLER | 1,
        'chosen_move_dispatch_pointer': dispatch['choose_move'] == PLAYER_MOVE_HANDLER | 1,
        'action_handler_prologue': read_int(rom, PLAYER_ACTION_HANDLER, 2) == 0xB510,
        'move_handler_prologue': read_int(rom, PLAYER_MOVE_HANDLER, 2) == 0xB5F0,
        'action_helper_bl': thumb_bl(rom, ACTION_HELPER_CALL) == 0x080171B8,
        'action0_fight_constant': read_int(rom, 0x08017204, 2) == 0x2200,
        'action0_emit_bl': thumb_bl(rom, AUTO_ACTION_FIGHT_EMIT_CALL) == EXPECTED_EMITTER,
        'action2_switch_branch_constant': read_int(rom, 0x08017230, 2) == 0x2202,
        'action2_emit_bl': thumb_bl(rom, AUTO_ACTION_SWITCH_EMIT_CALL) == EXPECTED_EMITTER,
        'action_handler_complete_bl': thumb_bl(rom, ACTION_COMPLETE_CALL) == EXPECTED_COMPLETE,
        'move_wrapper_bl': thumb_bl(rom, PLAYER_MOVE_WRAPPER_CALL) == PLAYER_MOVE_HANDLER,
        'move_select_cursor_byte_load': read_int(rom, 0x08065ECC, 2) == 0x780E,
        'move_action10_before_emit': read_int(rom, 0x08065F20, 2) == 0x220A,
        'move_direction1_before_emit': read_int(rom, 0x08065F22, 2) == 0x2101,
        'move_emit_bl': thumb_bl(rom, MOVE_EMIT_CALL) == EXPECTED_EMITTER,
        'move_complete_bl': thumb_bl(rom, MOVE_COMPLETE_CALL) == EXPECTED_COMPLETE,
    }
    safe = all(checks.values())
    return {
        'schema': 'sg-offline-private-rom-controller-dispatch-v1',
        'checks': checks,
        'bounded_original_rom_dispatch_candidate': safe,
        'absolute_source_symbol_identity_certified': False,
        'automatic_planner_source_identity_certified': False,
        'dynamic_legality_certified': False,
        'manual_fallback_certified': False,
        'no_automatic_forced_switch_certified':False,
        'native_acceptance_scenarios': 0,
        'production_authorized': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-rom', type=Path, required=True)
    parser.add_argument('--expected-rom-sha256', required=True)
    args = parser.parse_args()
    rom = args.private_rom.read_bytes()
    if hashlib.sha256(rom).hexdigest().lower() != args.expected_rom_sha256.lower():
        raise SystemExit('ROM identity mismatch')
    result = assess(rom)
    print(json.dumps(result, sort_keys=True, indent=2))
    if not result['bounded_original_rom_dispatch_candidate']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
