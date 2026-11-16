#!/usr/bin/env python3
"""Synthetic launcher battle-correlator unit tests; no private files used."""
import unittest
from run_private_cursor_probe import cpu_correlated_battle_candidate
from test_private_original_cursor_writer import fixture as raw_fixture

def fixture():
    z=raw_fixture()
    z[1]['target_before']=z[1]['target_after']=0
    return z

def fake_owner():
    return [
        {'pc':'0x0806bd8e','r':[0,0,0,0,0,0,0,0], 'lr':'0x08017211','f':100,'value':0,'width':1},
        {'pc':'0x0806bd8e','r':[0,0,0,0,0,0,0,0], 'lr':'0x08065f2d','f':101,'value':10,'width':1},
    ]

class Tests(unittest.TestCase):
 def test_ui_only_title_like_false_positive(self):
  self.assertFalse(cpu_correlated_battle_candidate([{'event':'battle_ui_candidate'}],[{'event':'cursor_trace_summary','stores':0,'pointer_writes':0,'slot_writes':0,'valid_samples':0}],[]))
 def test_full_original_cpu_candidate_not_certification(self):
  self.assertTrue(cpu_correlated_battle_candidate([{'event':'battle_ui_candidate'}],fixture(),fake_owner()))
 def test_missing_move_response(self):
  self.assertFalse(cpu_correlated_battle_candidate([{'event':'battle_ui_candidate'}],fixture(),fake_owner()[:1]))
 def test_missing_ui(self):
  self.assertFalse(cpu_correlated_battle_candidate([],fixture(),fake_owner()))
 def test_unknown_actor_response_fail_closed(self):
  e=fake_owner();e.append(dict(e[-1],lr='0x08010101'))
  self.assertFalse(cpu_correlated_battle_candidate([{'event':'battle_ui_candidate'}],fixture(),e))
 def test_missing_cursor_lifecycle_denied(self):
  self.assertFalse(cpu_correlated_battle_candidate([{'event':'battle_ui_candidate'}],fixture()[:-2],fake_owner()))
if __name__=='__main__':unittest.main()
