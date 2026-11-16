"""Fully synthetic unit records; no original ROM/save or private traces."""
import copy
import unittest
from audit_real_original_cpu_chain import evaluate


def fixture():
    fr=[{'event':'pp_hook_installed'},{'event':'save_load','loaded':True,'full_128kb_match':True},
        {'event':'completed','frames':8000,'exit_code':0}]
    def emit(f,lr,value,actor=0):
        return dict(f=f,pc='0x0806bd8e',lr=lr,value=value,width=1,r=[actor]+[0]*7)
    owner=[emit(30,'0x08017211',0),emit(31,'0x08065f2d',10),emit(31,'0x080615ef',10,1)]
    pp=[dict(f=80,raw_pc='0x0809e6be',before=20,after=19,value=19,width=1,
             thumb_flag=1,target=0,r=[0]+[0]*7)]
    return fr,owner,pp

class OriginalCpuCandidate(unittest.TestCase):
    def check(self,f=fixture(),want=True):
        result=evaluate(*f)
        self.assertIs(result['cpu_chain_candidate_UNVERIFIED'],want)
        self.assertEqual(result['formal_native_acceptance'],0)
        for field in ('input_free_auto_battle_certified','original_request_buffer_abi_certified',
                      'player0_request_and_legality_certified','original_manual_menu_fallback_certified',
                      'no_forced_switch_safety_certified','new_smart_auto_patch_executed','production_authorized'):
            self.assertIs(result[field],False)
        return result
    def test_genuine_synthetic_shape(self):
        x=self.check();self.assertEqual((x['fight_frame'],x['move_frame'],x['pp_frame']),(30,31,80))
        self.assertEqual((x['observed_pp_before'],x['observed_pp_after']),(20,19))
    def test_foe_emitter_ignored(self):
        f=fixture();f[1].append(dict(f=31,pc='0x0806bd8e',lr='0x0801723b',value=2,width=1,r=[1]+[0]*7));self.check(f)
    def test_duplicate_player_pp_denied(self):
        f=fixture();f[2].append(copy.deepcopy(f[2][0]));self.check(f,False)
    def test_duplicate_fight_denied(self):
        f=fixture();f[1].append(copy.deepcopy(f[1][0]));self.check(f,False)
    def test_duplicate_move_denied(self):
        f=fixture();f[1].append(copy.deepcopy(f[1][1]));self.check(f,False)
    def test_wrong_original_pp_opcode_denied(self):
        f=fixture();f[2][0]['raw_pc']='0x0809e6bc';self.check(f,False)
    def test_wrong_original_fight_lr_denied(self):
        f=fixture();f[1][0]['lr']='0x08017213';self.check(f,False)
    def test_wrong_original_move_lr_denied(self):
        f=fixture();f[1][1]['lr']='0x08065f2f';self.check(f,False)
    def test_wrong_pp_actor_denied(self):
        f=fixture();f[2][0]['r'][0]=1;self.check(f,False)
    def test_pp_opcode_thumb_and_width_denied(self):
        for field,value in [('thumb_flag',0),('width',2),('target',1)]:
            with self.subTest(field=field):
                f=fixture();f[2][0][field]=value;self.check(f,False)
    def test_pp_double_debit_denied(self):
        f=fixture();f[2][0]['after']=18;self.check(f,False)
    def test_pp_zero_before_denied(self):
        f=fixture();f[2][0].update(before=0,after=-1,value=-1);self.check(f,False)
    def test_ordering_denied(self):
        for fight,move,pp in [(31,30,80),(30,81,80),(30,30,30)]:
            with self.subTest(frames=(fight,move,pp)):
                f=fixture();f[1][0]['f']=fight;f[1][1]['f']=move;f[2][0]['f']=pp;self.check(f,False)
    def test_switch_and_unknown_action_denied(self):
        for lr,val in [('0x0801723b',2),('0x080615ef',10)]:
            f=fixture();f[1].append(dict(f=40,pc='0x0806bd8e',lr=lr,value=val,width=1,r=[0]+[0]*7));self.check(f,False)
    def test_save_and_emulator_witness_required(self):
        cases=[('save_load','loaded',False),('save_load','full_128kb_match',False),('completed','exit_code',1)]
        for ev,key,val in cases:
            with self.subTest(key=key):
                f=fixture();next(x for x in f[0] if x['event']==ev)[key]=val
                with self.assertRaises(ValueError):evaluate(*f)
    def test_no_hook_denied(self):
        f=list(fixture());f[0]=[x for x in f[0] if x['event']!='pp_hook_installed']
        with self.assertRaises(ValueError):evaluate(*f)
    def test_wrong_nonplayer_emitter_never_counts(self):
        f=fixture();f[1][0]['r'][0]=1;self.check(f,False)
    def test_malformed_rows_denied(self):
        f=fixture();f[2][0]['r']='spoof';
        with self.assertRaises(ValueError):evaluate(*f)
    def test_wrong_after_value_denied(self):
        f=fixture();f[2][0]['value']=18;self.check(f,False)
    def test_no_source_cpu_writer_denied(self):
        f=list(fixture());f[2]=[];self.check(f,False)
    def test_unbounded_denied(self):
        f=list(fixture());f[1]=f[1]*40000
        with self.assertRaises(ValueError):evaluate(*f)

if __name__=='__main__':unittest.main()
