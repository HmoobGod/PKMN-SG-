#!/usr/bin/env python3
"""Synthetic-only actor0 return-path/PP join mutation tests, no private data."""
import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from audit_private_actor0_response_pp_join import evaluate, thumb_bl_target


class VirtualTestRom:
    """Sparse fictitious 32 MiB game image for independent synthetic cases."""
    def __init__(self, mutated=None):
        self.data = dict({0x65F28: 0x05, 0x65F29: 0xF0,
                          0x65F2A: 0x2A, 0x65F2B: 0xFF,
                          0x9E6BA: 0x0E, 0x9E6BB: 0x70}, **(mutated or {}))
    def __len__(self):
        return 0x2000000
    def __getitem__(self, index):
        if not isinstance(index, slice) or index.step is not None:
            raise TypeError('synthetic ROM only supports bounded slices')
        return bytes(self.data.get(i, 0) for i in range(index.start, index.stop))


def fixture():
    base=0x02001000
    pcs=(0x0806BD8A, 0x0806BD8E, 0x0806BD92,0x0806BD98,0x0806BD9E)
    vals=(32,10,256,0,0)
    widths=(1,1,2,1,1)
    offsets=(0,1,2,4,5)
    rows=[]
    for i, pc in enumerate(pcs):
        regs=[0,1,10,256,base,0,32,0]
        rows.append({'f':1000,'pc':f'0x{pc:08x}','raw_pc':f'0x{pc+4:08x}',
                     'dst':f'0x{base+offsets[i]:08x}', 'width':widths[i],
                     'value':vals[i], 'lr':'0x08065f2d', 'sp':'0x03007000', 'r':regs})
    rows.append({'f':1000,'pc':'0x0806261a','raw_pc':'0x0806261e',
                 'dst':'0x02002000','width':4,'value':2,'r':[0]*8})
    rows.append({'f':1001,'pc':'0x0809435a','raw_pc':'0x0809435e',
                 'dst':'0x02002100','width':1,'value':1,'r':[0]*8})
    pp=[{'event':'pp_candidate', 'f':950, 'base':'0x0200120c',
         'pp':[20,10,10,20]},
        {'f':1100,'address':'0x02001231','width':1,'before':20,'after':19,
         'value':19,'raw_pc':'0x0809e6be','thumb_flag':1,'op':'0xff000000',
         'r':[0,0x02001231,0,0,0,0,19,0]}]
    return VirtualTestRom(),rows,pp


class NativeJoinSyntheticTests(unittest.TestCase):
    def output(self,rom,rows,pp):
        return evaluate(rom,rows,pp,900)
    def test_positive_is_never_native_accepted(self):
        rom,rows,pp=fixture()
        self.assertEqual(thumb_bl_target(rom,'0x08065f2d'),0x0806BD80)
        z=self.output(rom,rows,pp)
        self.assertEqual(z['joined_player0_response_pp_candidates_UNVERIFIED'],1)
        self.assertEqual(z['candidates'][0]['slot_index'],0)
        self.assertEqual(z['candidates'][0]['target_candidate'],1)
        for k in ('engine_owned_one_use_request_certified',
                  'dynamic_move_target_legality_certified',
                  'manual_fallback_certified',
                  'unmodified_rom_automatic_move_origin_certified',
                  'production_authorized'):
            self.assertIs(z[k],False)
        self.assertEqual(z['original_native_acceptance_scenarios'],0)
    def test_emitter_mutations_fail_closed(self):
        for idx, key, value in ((0,'lr','0x08065f31'),
                                (0,'width',4),(0,'value',10),
                                (0,'dst','0x02001004'),
                                (0,'pc','0x0806bd8b'),
                                (1,'value',0),(2,'value',257),
                                (3,'width',2),(4,'raw_pc','0x0806bda0'),
                                (0,'guest_writes',1)):
            with self.subTest(idx=idx,key=key,value=value):
                rom,rows,pp=fixture();rows[idx][key]=value
                self.assertEqual(self.output(rom,rows,pp)['joined_player0_response_pp_candidates_UNVERIFIED'],0)
        for i in range(5):
            with self.subTest(dropped=i):
                rom,rows,pp=fixture();rows.pop(i)
                self.assertEqual(self.output(rom,rows,pp)['joined_player0_response_pp_candidates_UNVERIFIED'],0)
    def test_do_not_confuse_enemy_or_other_action_with_player0(self):
        rom,rows,pp=fixture()
        rows[0]['r'][0]=1
        self.assertEqual(self.output(rom,rows,pp)['joined_player0_response_pp_candidates_UNVERIFIED'],0)
        rom,rows,pp=fixture()
        rows[0]['r'][2]=0
        self.assertEqual(self.output(rom,rows,pp)['joined_player0_response_pp_candidates_UNVERIFIED'],0)
        rom,rows,pp=fixture()
        rows[0]['r'][3]=259
        self.assertEqual(self.output(rom,rows,pp)['joined_player0_response_pp_candidates_UNVERIFIED'],0)
        rom,rows,pp=fixture()
        rows.extend(copy.deepcopy(rows[:5]))
        self.assertEqual(self.output(rom,rows,pp)['joined_player0_response_pp_candidates_UNVERIFIED'],0)
    def test_decision_pc_r0_is_not_an_actor_identifier(self):
        rom,rows,pp=fixture()
        rows[-1]['r'][0]=1  # original validator temporary, not battler ID
        self.assertEqual(self.output(rom,rows,pp)
                         ['joined_player0_response_pp_candidates_UNVERIFIED'],1)

    def test_not_a_valid_bl_caller_is_rejected(self):
        rom,rows,pp=fixture()
        rom.data[0x65F29]=0xE0
        self.assertIsNone(thumb_bl_target(rom,'0x08065f2d'))
        self.assertEqual(self.output(rom,rows,pp)['joined_player0_response_pp_candidates_UNVERIFIED'],0)
        for addr in ('0x08065f2c','0x08000000','0x00000000',None):
            self.assertIsNone(thumb_bl_target(rom,addr))
    def test_out_of_order_candidate_cannot_backfill_pp_proof(self):
        rom,rows,pp=fixture()
        pp.reverse()
        self.assertEqual(self.output(rom,rows,pp)
                         ['joined_player0_response_pp_candidates_UNVERIFIED'],0)

    def test_pp_and_decision_gates(self):
        for mut in ('wrong_slot','wrong_pp_writer','early_pp','wrong_source','double_pp',
                    'missing_candidate','missing_decision','missing_completion','long_gap'):
            with self.subTest(mut=mut):
                rom,rows,pp=fixture()
                if mut=='wrong_slot':pp[-1]['address']='0x02001232';pp[-1]['r'][1]+=1
                elif mut=='wrong_pp_writer':pp[-1]['raw_pc']='0x0809e6bc'
                elif mut=='early_pp':pp[-1]['f']=999
                elif mut=='wrong_source':pp[-1]['r'][6]=18
                elif mut=='double_pp':
                    dup=copy.deepcopy(pp[-1]);dup.update(f=1101,before=19,after=18,value=18)
                    dup['r'][6]=18;pp.append(dup)
                elif mut=='missing_candidate':pp.pop(0)
                elif mut=='missing_decision':rows.pop(-1)
                elif mut=='missing_completion':rows.pop(-2)
                elif mut=='long_gap':pp[-1]['f']=1301
                self.assertEqual(self.output(rom,rows,pp)['joined_player0_response_pp_candidates_UNVERIFIED'],0)


if __name__=='__main__':unittest.main()
