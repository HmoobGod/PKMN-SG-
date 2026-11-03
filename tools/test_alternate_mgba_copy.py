"""Negative checks using an exact synthetic R7-shaped report.

CI does not include the private ROM, save, state, or emulator executable.
"""
import copy
import unittest
from verify_alternate_mgba_copy import verify, EXPECTED


def example():
    raw = bytes([19]) + bytes(range(1,44))
    d = dict(EXPECTED)
    d.update({
        'schema': 'sg16266-alt-mgba-observer-v1',
        'case': 'manual_confirm_then_next_actor0_move_request',
        'cpu_thumb_prefetch_refreshed': True,
        'prefetch_before': ['0x20','0xf000'],
        'prefetch_after': ['0x4b00','0x4718'],
        'human_confirm_frame':14246,
        'human_confirm_original_payload':257,
        'entry_frame':14369, 'post_frame':14369,
        'actor':0,'direction':0,'length':44,
        'entry_pc':'0x0806b370','store_pc':'0x0806b3be',
        'post_pc':'0x0806b3c6',
        'source_address':0x0201CF14,'destination_address':0x0201BF14,
        'entry_sp':0x03007D3C,'post_sp':0x03007D34,
        'entry_lr':0x0806BB13,'post_lr':0x0806BB13,
        'pending_at_copy_entry':0,'pending_at_post_copy':0,
        'opcode_at_post_copy':19,
        'pending_set_after_post_guest_steps':23,
        'pending_transition_pc':'0x80d4ca4',
        'pending_transition_frame':14369,
        'pending_word_after_transition':1,
        'pending_request_opcode_after_transition':19,
        'native_auto_moves':0,'native_automatic_battle_acceptance':0,
        'user_ownership_certified':False,
        'move_and_target_legality_certified':False,
        'real_mobile_gameplay_certified':False,
        'savestate_version_warning':'emulator reported warning; acknowledged, not cleared',
        'store_indices':list(range(44)),
        'source_before_hex':raw.hex(),'source_after_hex':raw.hex(),
        'destination_after_hex':raw.hex(),'store_values_hex':raw.hex(),
    })
    return d


class AlternateCopyVerifier(unittest.TestCase):
    def test_valid_synthetic(self):
        self.assertEqual(verify(example())['copy_bytes'], 44)

    def test_fail_closed_on_missing_and_altered_required_fields(self):
        d = example()
        for key in list(d):
            bad = copy.deepcopy(d)
            bad.pop(key)
            with self.subTest(key=key, mutation='missing'),self.assertRaises(ValueError):
                verify(bad)
            bad = copy.deepcopy(d)
            if isinstance(d[key], bool): bad[key] = not d[key]
            elif isinstance(d[key], int): bad[key] = d[key]+1
            elif isinstance(d[key], list): bad[key] = d[key][:-1]
            else: bad[key] = 'X' + d[key][1:]
            with self.subTest(key=key, mutation='changed'),self.assertRaises(ValueError):
                verify(bad)

    def test_wrong_reordered_and_duplicate_store_index(self):
        for index in [[],[0]*44,list(range(43,-1,-1)),list(range(43)),list(range(45))]:
            d=example();d['store_indices']=index
            with self.subTest(index=index[:4]),self.assertRaises(ValueError):
                verify(d)

    def test_untrusted_bytes_and_nonmove_opcode(self):
        for field in ('source_before_hex','source_after_hex','destination_after_hex','store_values_hex'):
            for value in ('f','!','00'*44,'ff'*44, '13'+'00'*43):
                d=example();d[field]=value
                with self.subTest(field=field,value=value[:4]),self.assertRaises(ValueError):
                    verify(d)

    def test_no_report_mutation(self):
        d=example();before=copy.deepcopy(d);verify(d);self.assertEqual(d,before)


if __name__=='__main__': unittest.main(verbosity=2)