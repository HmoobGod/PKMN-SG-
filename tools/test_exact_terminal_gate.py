#!/usr/bin/env python3
"""Synthetic terminal false-positive denials; no ROM/save/trace in CI."""
import unittest
import verify_exact_terminal_gate as v

def fixture():
    return {
        "schema":v.SCHEMA,"rom_sha256":v.ROM_SHA,"save_sha256":v.SAVE_SHA,
        "host_move_menu_inputs":0,"guest_writes":0,"new_hook_installed":False,
        "samples":[{"frame":3189+350*i,"flags":4,"battlers":2,"pending":0,
                    "events":0 if i>=1 else 22,"auto":0 if i>=1 else 1,
                    "pp":[19,10,10,20],"manual":0} for i in range(5)]
    }

class NativeTerminalSafety(unittest.TestCase):
    def test_quiet_battle_not_terminal(self):
        result=v.audit(fixture())
        self.assertTrue(result["no_input_original_battle_state_still_active"])
        self.assertFalse(result["terminal_or_cancellation_certified"])
        self.assertFalse(result["production_promotion_authorized"])
        self.assertGreaterEqual(result["quiet_frames_at_least"],1050)
    def test_even_zero_flags_not_sufficient(self):
        r=fixture()
        r["samples"][-1]["flags"]=0
        r["samples"][-1]["battlers"]=0
        x=v.audit(r)
        self.assertFalse(x["terminal_or_cancellation_certified"])
    def reject(self,fn):
        r=fixture();fn(r)
        with self.assertRaises(ValueError):v.audit(r)
    def test_bad_rom(self):self.reject(lambda r:r.update(rom_sha256="other"))
    def test_bad_save(self):self.reject(lambda r:r.update(save_sha256="other"))
    def test_host_key(self):self.reject(lambda r:r.update(host_move_menu_inputs=1))
    def test_guest_write(self):self.reject(lambda r:r.update(guest_writes=1))
    def test_hook_claim(self):self.reject(lambda r:r.update(new_hook_installed=True))
    def test_wrong_battle(self):self.reject(lambda r:r["samples"][0].update(flags=8))
    def test_wrong_battlers(self):self.reject(lambda r:r["samples"][0].update(battlers=4))
    def test_bad_window_gap(self):self.reject(lambda r:r["samples"][2].update(frame=0))
    def test_manual_menu(self):self.reject(lambda r:r["samples"][-1].update(manual=1))
    def test_unverified_extra_bytes(self):self.reject(lambda r:r["samples"][-1].update(raw_guest_ram="private"))
    def test_no_quiet_tail(self):self.reject(lambda r:r["samples"][-1].update(events=2))
    def test_non_int_frame(self):self.reject(lambda r:r["samples"][-1].update(frame="bad"))
    def test_truncated(self):self.reject(lambda r:r.update(samples=r["samples"][:3]))
    def test_wrong_pending_type(self):self.reject(lambda r:r["samples"][-1].update(pending="0"))

if __name__=="__main__":unittest.main()
