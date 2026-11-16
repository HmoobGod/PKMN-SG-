#!/usr/bin/env python3
"""All generated synthetic data; never references private game files."""
import copy
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from audit_private_cpu_pp_store import decode_thumb_strb, evaluate, verify_store


def fixture():
    rom = bytearray(64)
    rom[16:18] = (0x700e).to_bytes(2,'little')  # THUMB STRB r6,[r1,#0]
    e = {'f': 30, 'address':'0x02001234', 'width':1, 'before':20,
         'after':19, 'value':19,'raw_pc':'0x08000014', 'op':'0x00004e82',
         'thumb_flag':1,'r':[0,0x02001234,0,0,0,0,19,0]}
    return rom, e


def candidate():
    return {'event':'pp_candidate','f':21,'base':'0x0200120C',
            'pp':[20,20,20,20]}


class StoreAuditTests(unittest.TestCase):
    def test_exact_real_opcode_fetched_from_rom_not_prefetch(self):
        rom,e=fixture()
        self.assertTrue(verify_store(e,rom,20))
        self.assertEqual(decode_thumb_strb(0x700e,e['r']),(0x02001234,19))
        z=evaluate(rom,[candidate(),e],20)
        self.assertEqual(z['direct_cpu_pp_byte_debit_candidates_UNVERIFIED'],1)
        self.assertEqual(z['candidates'][0]['writer_pc'],'0x08000010')
        for key in ('original_request_owner_certified', 'move_target_legality_certified',
                    'pp_cancel_cause_certified','manual_fallback_certified','production_authorized'):
            self.assertFalse(z[key])
        self.assertEqual(z['original_native_acceptance_scenarios'],0)
    def test_fail_closed_mutations(self):
        rom,e=fixture()
        changes=[('f',20),('f',0),('address','0x02001235'),
                 ('address','0x01001234'),('width',2),('before',19),
                 ('after',18),('after',0),('value',0),('raw_pc','0x08000010'),
                 ('raw_pc','0x08000015'),('thumb_flag',0),('r',[0,0x02001235,0,0,0,0,19,0]),
                 ('r',[0,0x02001234,0,0,0,0,18,0]),('r',[0]*7),
                 ('r',[0,True,0,0,0,0,19,0]),('guest_writes',1),
                 ('production_authorized',True),('native_accepted',True)]
        for key,value in changes:
            with self.subTest(key=key,value=value):
                d=copy.deepcopy(e);d[key]=value
                self.assertFalse(verify_store(d,rom,20))
        for key in ('f','address','width','before','after','value','raw_pc','thumb_flag','r'):
            d=copy.deepcopy(e);del d[key]
            self.assertFalse(verify_store(d,rom,20))
    def test_bad_rom_and_illegal_thumb_variants(self):
        rom,e=fixture()
        for opcode in (0x780e,0x680e,0x600e,0xffff,0x1c06,0x7016):
            corrupted=bytearray(rom)
            corrupted[16:18]=opcode.to_bytes(2,'little')
            self.assertFalse(verify_store(e,corrupted,20),hex(opcode))
        self.assertIsNone(decode_thumb_strb(0x700e,[0]*7))
        self.assertIsNone(decode_thumb_strb(0x10000,e['r']))
    def test_missing_or_after_the_fact_candidate_denied(self):
        rom,e=fixture()
        self.assertEqual(evaluate(rom,[e],20)['direct_cpu_pp_byte_debit_candidates_UNVERIFIED'],0)
        for mutate in ({'f':31}, {'base':'0x02001210'}, {'pp':[0,0,0,0]},
                       {'pp':[20,20,20]}, {'guest_writes':1}):
            d=candidate();d.update(mutate)
            self.assertEqual(evaluate(rom,[d,e],20)['direct_cpu_pp_byte_debit_candidates_UNVERIFIED'],0)
    def test_stale_and_ambiguous_battle_structure_are_not_pp_proof(self):
        rom,e=fixture()
        stale=candidate();stale['f']=1
        old=copy.deepcopy(e);old['f']=400
        self.assertEqual(evaluate(rom,[stale,old],20)['direct_cpu_pp_byte_debit_candidates_UNVERIFIED'],0)
        # Two different plausible PP bases overlapping the same candidate
        # address must not select one arbitrarily.
        ambiguity=candidate()
        ambiguity.update(base='0x0200120D',pp=[20,20,20,20])
        self.assertEqual(evaluate(rom,[candidate(),ambiguity,e],20)
                         ['direct_cpu_pp_byte_debit_candidates_UNVERIFIED'],0)
        # Refreshed snapshots of the same exact base are not distinct bases.
        newer=candidate();newer['f']=25
        self.assertEqual(evaluate(rom,[candidate(),newer,e],20)
                         ['direct_cpu_pp_byte_debit_candidates_UNVERIFIED'],1)

    def test_duplicate_and_non_writer_not_promoted(self):
        rom,e=fixture()
        bad=copy.deepcopy(e);bad['op']='0x0000700e';bad['after']=20
        r=evaluate(rom,[candidate(),e,copy.deepcopy(e),bad],20)
        self.assertEqual(r['direct_cpu_pp_byte_debit_candidates_UNVERIFIED'],1)
        self.assertEqual(r['rejected_or_non_pp_events'],2)
        self.assertFalse(r['original_request_owner_certified'])


if __name__ == '__main__':
    unittest.main()
