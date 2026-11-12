#!/usr/bin/env python3
"""Public synthetic deny tests only. No private ROM, save, savestate, request."""
import unittest
import verify_exact_modified_autoplay as mod

def event(pc, frame, **kwargs):
    obj = dict(pc=pc, frame=frame, r0=0, r1=0, r2=0, r3=0,
               reply_valid=0, reply_header=0, reply_payload=0)
    obj.update(kwargs)
    return obj

def fixture():
    events = []
    for frame, slot, move in ((4179, 3, 269), (4318, 1, 157), (4462, 1, 157)):
        payload = slot | 256
        events.extend([
            event('0x9f1f000', frame),
            event('0x8065eb4', frame),
            event('0x806bd80', frame, r0=0, r2=10, r3=payload),
            event('0x806b370', frame, r0=0, r1=1, r3=6,
                  reply_valid=1, reply_header=0x0A20, reply_payload=payload),
            event('0x806261c', frame, r0=0),
            event('0x8094330', frame+1, r0=0),
            event('0x809435c', frame+1, r0=slot),
            event('0x8094374', frame+1, r0=move),
            event('0x8094380', frame+1, r2=1),
        ])
    return dict(schema=mod.SCHEMA, rom_sha256=mod.ROM_SHA,
                save_sha256=mod.SAVE_SHA, state_sha256=mod.STATE_SHA,
                host_move_menu_buttons_sent=0, emulator_rom_writes=0,
                installed_new_hook=False,
                provenance=dict(preconstructor_state_sha256=mod.PRECONSTRUCTOR_SHA,
                                request_copy_sha256=mod.PRIVATE_REQUEST_SHA,
                                actor0_installer=1, opponent_installer=1,
                                request_copy_stores=44,
                                pending_set_guest_steps=23, current_flags='0x4',
                                actor0_controller_kind=1,
                                actor1_controller_kind=3,
                                player_move_request_same_as_own=True),
                status=1, trace_start_frame=4179, trace_end_frame=4529,
                guest_steps=24056369, player_moves_before=[325,157,92,269],
                player_pp_before=[20,10,10,20], player_pp_after=[20,8,10,19],
                events=events)

class OriginalExactAuto(unittest.TestCase):
    def test_synthetic_three_native_moves(self):
        result = mod.audit(fixture())
        self.assertEqual(result['original_player_native_reply_accept_commit'], 3)
        self.assertFalse(result['production_rom_promotion_authorized'])
    def reject(self, callback):
        report = fixture(); callback(report)
        with self.assertRaises(ValueError): mod.audit(report)
    def test_wrong_rom(self): self.reject(lambda r:r.update(rom_sha256='bad'))
    def test_wrong_save(self): self.reject(lambda r:r.update(save_sha256='bad'))
    def test_wrong_state(self): self.reject(lambda r:r.update(state_sha256='bad'))
    def test_bad_copy(self): self.reject(lambda r:r['provenance'].update(request_copy_stores=43))
    def test_no_player_installer(self): self.reject(lambda r:r['provenance'].update(actor0_installer=0))
    def test_no_enemy_installer(self): self.reject(lambda r:r['provenance'].update(opponent_installer=0))
    def test_wrong_request_sha(self): self.reject(lambda r:r['provenance'].update(request_copy_sha256='bad'))
    def test_wrong_battle(self): self.reject(lambda r:r['provenance'].update(current_flags='0x8'))
    def test_wrong_owner(self): self.reject(lambda r:r['provenance'].update(actor0_controller_kind=3))
    def test_wrong_enemy_kind(self): self.reject(lambda r:r['provenance'].update(actor1_controller_kind=1))
    def test_no_pending(self): self.reject(lambda r:r['provenance'].update(pending_set_guest_steps=0))
    def test_host_menu_button(self): self.reject(lambda r:r.update(host_move_menu_buttons_sent=1))
    def test_guest_rom_write(self): self.reject(lambda r:r.update(emulator_rom_writes=1))
    def test_new_hook_claim(self): self.reject(lambda r:r.update(installed_new_hook=True))
    def test_missing_emitter(self): self.reject(lambda r:r['events'].pop(2))
    def test_player_item_action(self): self.reject(lambda r:r['events'][2].update(r2=9))
    def test_wrong_payload_target(self): self.reject(lambda r:r['events'][2].update(r3=515))
    def test_no_reply(self): self.reject(lambda r:r['events'].pop(3))
    def test_wrong_reply_header(self): self.reject(lambda r:r['events'][3].update(reply_header=0))
    def test_missing_completion(self): self.reject(lambda r:r['events'].pop(4))
    def test_rejection_by_validator(self): self.reject(lambda r:r['events'][5].update(r0=1))
    def test_wrong_slot(self): self.reject(lambda r:r['events'][6].update(r0=0))
    def test_wrong_move(self): self.reject(lambda r:r['events'][7].update(r0=123))
    def test_wrong_target(self): self.reject(lambda r:r['events'][8].update(r2=0))
    def test_missing_callback(self): self.reject(lambda r:r['events'].pop(0))
    def test_missing_preflight(self): self.reject(lambda r:r['events'].pop(1))
    def test_unchanged_pp(self): self.reject(lambda r:r['player_pp_after'].__setitem__(1,10))
    def test_overconsumed_pp(self): self.reject(lambda r:r['player_pp_after'].__setitem__(1,7))
    def test_manual_menu(self): self.reject(lambda r:r['events'].append(event('0x806449e',4529)))
    def test_incomplete(self): self.reject(lambda r:r.update(status=2))
    def test_forbidden_raw_field(self): self.reject(lambda r:r['events'][0].update(game_bytes='private'))

if __name__ == '__main__': unittest.main()
