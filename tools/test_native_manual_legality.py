"""Public synthetic R9 regression: no private ROM/save/reports or auto moves."""
import copy
import hashlib
import unittest
from test_live_context import example as r8_example, example_bytes_hex
from verify_native_manual_legality import verify,PCS,ORDER

SYNTHETIC_HASH=hashlib.sha256(bytes.fromhex(example_bytes_hex())).hexdigest()

def example(slot=1):
    parent=r8_example()
    move_id=(1,2)[slot]
    payload=256+slot
    press_frame=14377 if slot==0 else 14375
    kinds=list(ORDER)
    fields=[
      {'emit_actor':0,'subcmd':10,'encoded_choice':payload},
      {'reply_actor':0,'direction':1,'bytes':6,'reply_header':0x0A20,
       'reply_payload':payload,'reply_ewram_valid':True},
      {'completion_actor':0},
      {'consumer_actor':0},
      {'consumer_actor':0,'original_native_result':0},
      {'consumer_actor':0,'committed_move_slot':slot},
      {'consumer_actor':0,'committed_move_id':move_id},
      {'consumer_actor':0},
    ]
    events=[dict(kind=k,original_pc=hex(PCS[i]),frame=press_frame if i<3 else press_frame+1,
            pending_word=1 if i<2 else 0,**fields[i]) for i,k in enumerate(kinds)]
    return dict(schema='sg16266-native-human-legality-v1',
        scope='one original human-confirmed wild single; no auto submission, no complete legality or owner certificate',
        underlying_live_request=parent,original_manual_menu_frame=14373,
        original_user_input='LEFT then A' if slot==0 else 'A',native_player_events=events,
        selected_move_slot=slot,selected_move_id=move_id,selected_target_position=1,
        manual_native_validation_accepted=True,original_native_emitter_untouched=True,
        automatic_moves=0,automatic_battle_acceptance=0,
        general_move_legality_certified=False,
        exclusive_player_ownership_certified=False,other_encounters_certified=False)

def check(report):
    return verify(report,expected_request_sha256=SYNTHETIC_HASH,
                  expected_selected_move_ids=(1,2))

class NativeManualR9(unittest.TestCase):
    def test_valid_synthetic_one_manual_choice(self):
        for slot in (0,1):
            with self.subTest(slot=slot):
                x=check(example(slot));self.assertEqual(x['original_native_accepted_manual_lifetimes'],1)
                self.assertEqual(x['automatic_battle_acceptance'],0)
    def test_wrong_sequence_missing_or_duplicate(self):
        for index in range(8):
            r=example();r['native_player_events'].pop(index)
            with self.subTest(mutation='delete',index=index),self.assertRaises(ValueError):check(r)
            r=example();r['native_player_events'].insert(index,copy.deepcopy(r['native_player_events'][index]))
            with self.subTest(mutation='duplicate',index=index),self.assertRaises(ValueError):check(r)
        r=example();r['native_player_events'][3],r['native_player_events'][4]=r['native_player_events'][4],r['native_player_events'][3]
        with self.assertRaises(ValueError):check(r)
    def test_pc_frame_phase_actor_mutations(self):
        for index in range(8):
            for field,bad in (('original_pc','0x12345'),('frame',14400),
                              ('pending_word',0 if index<2 else 1)):
                r=example();r['native_player_events'][index][field]=bad
                with self.subTest(index=index,field=field),self.assertRaises(ValueError):check(r)
            r=example();e=r['native_player_events'][index]
            actor='emit_actor' if index==0 else 'reply_actor' if index==1 else 'completion_actor' if index==2 else 'consumer_actor'
            e[actor]=1
            with self.subTest(index=index,field=actor),self.assertRaises(ValueError):check(r)
    def test_reply_emitter_and_original_validation(self):
        for index,field,bad in ((0,'subcmd',9),(0,'encoded_choice',0),
              (1,'direction',0),(1,'bytes',4),(1,'reply_header',0x0A21),
              (1,'reply_payload',258),(1,'reply_ewram_valid',False),
              (4,'original_native_result',1),(5,'committed_move_slot',0),
              (6,'committed_move_id',3)):
            r=example();r['native_player_events'][index][field]=bad
            with self.subTest(index=index,field=field),self.assertRaises(ValueError):check(r)
    def test_no_auto_or_general_ownership_claims(self):
        for field,bad in (('automatic_moves',1),('automatic_battle_acceptance',1),
            ('general_move_legality_certified',True),
            ('exclusive_player_ownership_certified',True),
            ('other_encounters_certified',True),
            ('original_native_emitter_untouched',False),
            ('original_user_input','AI'),('selected_move_slot',2),
            ('selected_target_position',3),('selected_move_id',3)):
            r=example();r[field]=bad
            with self.subTest(field=field),self.assertRaises(ValueError):check(r)
    def test_original_negative_restrictions_fail(self):
        for field,val in (('player_own_pp',[5,0,7,8]),
            ('player_native_restricted_mask_negative_only',2),
            ('player_disabled_move',2),
            ('player_encore_timer',1),
            ('player_repeat_blocked',1)):
            r=example()
            if field=='player_repeat_blocked':
                for stage in ('postcopy_context','pending_context'):
                    r['underlying_live_request'][stage]['player_last_move']=2
            r['underlying_live_request']['postcopy_context'][field]=copy.deepcopy(val)
            r['underlying_live_request']['pending_context'][field]=copy.deepcopy(val)
            with self.subTest(field=field),self.assertRaises(ValueError):check(r)
    def test_parent_guard_unmodified(self):
        for field in ('native_auto_moves','original_native_installer_seen_this_process'):
            r=example();r['underlying_live_request'][field]=True
            with self.subTest(field=field),self.assertRaises(ValueError):check(r)
    def test_no_mutation(self):
        r=example();original=copy.deepcopy(r)
        check(r);self.assertEqual(r,original)

if __name__=='__main__':unittest.main(verbosity=2)