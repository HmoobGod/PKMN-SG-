"""Fully synthetic copy-pair consistency tests, no ROM/save or emulator required."""
from copy import deepcopy
import unittest
from verify_native_copy_pairs import validate_trace,IncompleteTrace,ENTRY,STORE,POST,ROM_SHA,SAVE_SHA,STATE_SHA,BRIDGE_SHA,RUNTIME_SHA

def fixture():
    source=0x02014000; dest=0x0201C000
    payload=(bytes([19])+bytes(range(1,44))).hex()
    frame=14310; sp=0x03007F00; lr=0x08061111
    entry={'hit':1,'pc':ENTRY,'frame':frame,'actor':0,'direction':0,'count':44,'link_flag':False,
           'source':source,'destination':dest,'sp':sp,'lr':lr,'source_bytes_hex':payload}
    stores=[{'hit':i+2,'pc':STORE,'frame':frame,'index':i,'dest':dest,'source':source,
             'value':b,'sp':sp-8,'lr':lr} for i,b in enumerate(bytes.fromhex(payload))]
    post={'hit':46,'pc':POST,'frame':frame,'source':source,'dest':dest,'copied':44,'count':44,
          'sp':sp-8,'lr':lr,'source_bytes_hex':payload,'dest_bytes_hex':payload}
    return {'hashes':{'rom':ROM_SHA,'save':SAVE_SHA,'state':STATE_SHA,
                      'bridge':BRIDGE_SHA,'runtime':RUNTIME_SHA},
            'observer_only':True,'auto_dispatch':False,
            'attempts':[{'entry':entry,'stores':stores,'post':post}], 'reported_pairs':1,
            'player_ownership_proven':False,'move_target_authorized':False}

class TestCopyPairs(unittest.TestCase):
    def test_complete_pair_is_only_observation(self):
        r=fixture();self.assertEqual(validate_trace(r)['complete_instruction_path_pairs'],1)
        self.assertEqual(validate_trace(r)['automatic_moves_authorized'],0)
    def test_distinct_attempts_may_share_payload(self):
        r=fixture();next_one=deepcopy(r['attempts'][0]);next_one['entry']['hit'] += 46
        for e in next_one['stores']:e['hit'] += 46
        next_one['post']['hit'] += 46
        r['attempts'].append(next_one);r['reported_pairs']=2
        self.assertEqual(validate_trace(r)['complete_instruction_path_pairs'],2)
    def test_adversarial_denials(self):
        mutations={
        'bad_rom':lambda x:x['hashes'].update(rom='0'*64),
        'bad_save':lambda x:x['hashes'].update(save='0'*64),
        'missing_runtime':lambda x:x['hashes'].pop('runtime'),
        'auto_mode':lambda x:x.update(auto_dispatch=True),
        'no_read_only':lambda x:x.update(observer_only=False),
        'no_attempts':lambda x:x['attempts'].clear(),
        'not_a_copy':lambda x:x['attempts'][0]['entry'].update(pc=POST),
        'duplicate_event_hit':lambda x:x['attempts'][0]['stores'][12].update(hit=13),
        'post_order_drift':lambda x:x['attempts'][0]['post'].update(hit=12),
        'wrong_actor':lambda x:x['attempts'][0]['entry'].update(actor=2),
        'wrong_direction':lambda x:x['attempts'][0]['entry'].update(direction=1),
        'wrong_length':lambda x:x['attempts'][0]['entry'].update(count=43),
        'link':lambda x:x['attempts'][0]['entry'].update(link_flag=True),
        'sp_bad':lambda x:x['attempts'][0]['entry'].update(sp=0),
        'sp_misaligned':lambda x:x['attempts'][0]['entry'].update(sp=0x03007F02),
        'wrong_lr':lambda x:x['attempts'][0]['entry'].update(lr=0x08061110),
        'overlap':lambda x:x['attempts'][0]['entry'].update(destination=0x02014001),
        'source_overflow':lambda x:x['attempts'][0]['entry'].update(source=0x0203FFF0),
        'bad_opcode':lambda x:x['attempts'][0]['entry'].update(source_bytes_hex='01'+x['attempts'][0]['entry']['source_bytes_hex'][2:]),
        'missing_store':lambda x:x['attempts'][0]['stores'].pop(),
        'repeated_store':lambda x:x['attempts'][0]['stores'].__setitem__(1,deepcopy(x['attempts'][0]['stores'][0])),
        'wrong_store_pc':lambda x:x['attempts'][0]['stores'][10].update(pc=ENTRY),
        'wrong_store_value':lambda x:x['attempts'][0]['stores'][8].update(value=50),
        'wrong_dest':lambda x:x['attempts'][0]['stores'][5].update(dest=0x0201B000),
        'wrong_source':lambda x:x['attempts'][0]['stores'][5].update(source=0x02018000),
        'nested_frame':lambda x:x['attempts'][0]['stores'][5].update(frame=14311),
        'intervening_sp':lambda x:x['attempts'][0]['stores'][5].update(sp=0x03007E00),
        'changed_lr':lambda x:x['attempts'][0]['stores'][5].update(lr=0x08061113),
        'wrong_post_pc':lambda x:x['attempts'][0]['post'].update(pc=0x0806B3A6),
        'post_count':lambda x:x['attempts'][0]['post'].update(copied=43),
        'post_dest':lambda x:x['attempts'][0]['post'].update(dest=0x0201C001),
        'post_mem':lambda x:x['attempts'][0]['post'].update(dest_bytes_hex='00'*44),
        'source_changed':lambda x:x['attempts'][0]['post'].update(source_bytes_hex='00'*44),
        'post_frame':lambda x:x['attempts'][0]['post'].update(frame=14311),
        'claim_owner':lambda x:x.update(player_ownership_proven=True),
        'claim_legality':lambda x:x.update(move_target_authorized=True),
        'false_total':lambda x:x.update(reported_pairs=2),
        }
        for name,mutation in mutations.items():
            with self.subTest(name=name):
                r=fixture();mutation(r)
                with self.assertRaises(IncompleteTrace):validate_trace(r)
    def test_is_pure(self):
        r=fixture();old=deepcopy(r);validate_trace(r);self.assertEqual(r,old)

if __name__=='__main__':unittest.main(verbosity=2)