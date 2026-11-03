"""Public synthetic unit suite for R8 native controller/own-move report rules.

No emulator or private ROM/save/state is included in source CI.
"""
import copy
import unittest
from test_alternate_mgba_copy import example as old_example
from verify_live_context import verify,EXPECTED,OWN_FIELDS


def own_context():
    return {
        'player_own_moves':[1, 2, 3, 4],
        'player_request_moves':[1, 2, 3, 4],
        'player_own_pp':[5, 6, 7, 8],
        'player_native_restricted_mask_negative_only':0,
        'player_disabled_move':0,'player_encored_move':0,
        'player_encore_timer':0,'player_last_move':1,
        'player_repeat_blocked':0,
    }


def check(obj):
    import hashlib
    return verify(obj,expected_request_sha256=hashlib.sha256(
        bytes.fromhex(example_bytes_hex())).hexdigest())


def example_bytes_hex():
    return (bytes([19])+bytes(range(1,44))).hex()


def example():
    x=old_example()
    # Public synthetic bytes, NOT the private user's battle request.
    raw=bytes([19])+bytes(range(1,44))
    for f in ('source_before_hex','source_after_hex','destination_after_hex','store_values_hex'):
        x[f]=raw.hex()
    x.update(r8_public_context_only=True,
             original_native_installer_seen_this_process=False,
             engine_owned_request_correlated_this_fixture=True,
             postcopy_context={**EXPECTED,**own_context(),'pending_word':0},
             pending_context={**EXPECTED,**own_context(),'pending_word':1})
    return x


class R8NativeContext(unittest.TestCase):
    def test_synthetic_valid(self):
        result=check(example())
        self.assertEqual(result['own_moves_matched'],4)
        self.assertEqual(result['owner_authorization_certificates'],0)

    def test_field_missing_or_wrong_in_either_state(self):
        for place in ('postcopy_context','pending_context'):
            for key,correct in {**EXPECTED,**own_context()}.items():
                obj=example();obj[place].pop(key)
                with self.subTest(place=place,key=key,mutation='removed'),self.assertRaises(ValueError):
                    check(obj)
                obj=example()
                if type(correct) is list:
                    obj[place][key]=list(reversed(correct)) if len(correct)>1 else []
                else:
                    obj[place][key]=correct+1
                with self.subTest(place=place,key=key,mutation='altered'),self.assertRaises(ValueError):
                    check(obj)

    def test_actor_controller_mismatch_and_hidden_data(self):
        for badfield in ('foe_moves','foe_hp','enemy_held_item','enemy_ability','unknown'):
            obj=example();obj['pending_context'][badfield]=1
            with self.subTest(badfield=badfield),self.assertRaises(ValueError):
                check(obj)
        obj=example();obj['pending_context']['controller_kinds']=[3,1]
        with self.assertRaises(ValueError):check(obj)

    def test_premature_pending_and_missing_pending(self):
        for p0,p1 in ((1,1),(0,0),(3,1),(0,3),(-1,1)):
            obj=example();obj['postcopy_context']['pending_word']=p0
            obj['pending_context']['pending_word']=p1
            with self.subTest(p0=p0,p1=p1),self.assertRaises(ValueError):check(obj)

    def test_never_accept_claim_of_auto_permission_or_installer(self):
        for key,val in [('native_auto_moves',1),
                        ('native_automatic_battle_acceptance',1),
                        ('original_native_installer_seen_this_process',True),
                        ('engine_owned_request_correlated_this_fixture',False),
                        ('r8_public_context_only',False)]:
            obj=example();obj[key]=val
            with self.subTest(key=key),self.assertRaises(ValueError):check(obj)

    def test_request_bytes_must_match_prior_independent_trace(self):
        obj=example()
        mutated='13'+'ff'*43
        for field in ('source_before_hex','source_after_hex','destination_after_hex','store_values_hex'):
            obj[field]=mutated
        with self.assertRaises(ValueError):check(obj)

    def test_does_not_mutate_report(self):
        obj=example();base=copy.deepcopy(obj)
        check(obj)
        self.assertEqual(obj,base)

if __name__=='__main__':unittest.main(verbosity=2)