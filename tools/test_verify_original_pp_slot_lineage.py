"""All tests synthetic: do not load personal ROM, game save, or savestate."""
import copy
import unittest
import verify_original_pp_slot_lineage as p

LOG = 'HOST_DIAGNOSTIC_BATTLE_NARRATION_ACK_NOT_UNATTENDED\nKEY x 44.0'


def specimen(actor=0, slot=1, single_step=True):
    base = 0x02001ECC + actor * 0x98
    address = base + slot + 0x25
    before, cost = 15, 1
    fixed = {'r0':hex(actor),'sp':'0x3007cc4','main':2,'r8':'0x2001ecc'}
    def ev(i, pc, **kwargs): return {'t':i+1.,'pc':pc,**fixed,**kwargs}
    events = [
        ev(0,p.ORDER[0],r3=hex(address),old_pp_byte=before),
        ev(1,p.ORDER[1],r3=hex(before),requested_decrement=cost,effective_pp_before=before),
        ev(2,p.ORDER[2],stack_slot_word=slot,stack_new_pp_word=before-cost),
        ev(3,p.ORDER[3],r3=hex(base),r7=hex(slot),stack_new_pp_word=before-cost),
        ev(4,p.ORDER[4],r3=hex(base),r1=hex(base+slot),candidate_pp_address=hex(address),candidate_new_pp=before-cost),
    ]
    if single_step:
        events[-1].update(verified_pp_before_store=before,verified_pp_after_store=before-cost,
            verified_pp_pre_store_address=hex(address),actual_instruction_before_store='0x809e6ba',actual_strb_next_pc='0x809e6bc')
    return {'rom_sha256':p.EXACT,'original_cpu_events':events}


class Tests(unittest.TestCase):
    def test_stepped_player_pp(self):
        result=p.verify(specimen(),LOG)
        self.assertEqual(result['cpu_step_verified_pp_writes'],1)
        self.assertEqual(result['actor0_cpu_chains'],1)
        self.assertTrue(result['disqualifies_unattended_native_test'])
        self.assertEqual(result['historical_pp_unmatched_1'],'UNCLASSIFIED')
    def test_stepped_foe_pp(self):
        result=p.verify(specimen(1,3),LOG)
        self.assertEqual(result['chains'][0]['pp_address'],hex(0x02001ECC+0x98+3+0x25))
    def test_pre_store_only_never_counts_verified_store(self):
        result=p.verify(specimen(single_step=False),LOG)
        self.assertEqual(result['cpu_step_verified_pp_writes'],0)
    def test_missing_host_diagnostic_provenance(self):
        with self.assertRaisesRegex(ValueError,'host diagnostic'):p.verify(specimen(),'KEY Left 1')
    def test_wrong_rom_metadata(self):
        f=specimen(); f['rom_sha256']=p.CURRENT
        with self.assertRaisesRegex(ValueError,'identity'):p.verify(f,LOG)
    def test_incorrect_slot(self):
        f=specimen();f['original_cpu_events'][2]['stack_slot_word']=4
        with self.assertRaisesRegex(ValueError,'slot'):p.verify(f,LOG)
    def test_wrong_actor_stride(self):
        f=specimen(1);f['original_cpu_events'][3]['r3']='0x2001ecc'
        with self.assertRaisesRegex(ValueError,'address'):p.verify(f,LOG)
    def test_wrong_computed_pp(self):
        f=specimen();f['original_cpu_events'][4]['candidate_new_pp']=11
        with self.assertRaisesRegex(ValueError,'stack output'):p.verify(f,LOG)
    def test_wrong_actual_store_after(self):
        f=specimen();f['original_cpu_events'][4]['verified_pp_after_store']=15
        with self.assertRaisesRegex(ValueError,'final STRB'):p.verify(f,LOG)
    def test_wrong_final_store_pc(self):
        f=specimen();f['original_cpu_events'][4]['actual_strb_next_pc']='0x809e6ba'
        with self.assertRaisesRegex(ValueError,'final STRB'):p.verify(f,LOG)
    def test_duplicate_or_decreasing_time(self):
        f=specimen();f['original_cpu_events'][4]['t']=2
        with self.assertRaisesRegex(ValueError,'chronology'):p.verify(f,LOG)
    def test_interleaved_actor(self):
        f=specimen();f['original_cpu_events'][3]['r0']='0x1'
        with self.assertRaisesRegex(ValueError,'actor'):p.verify(f,LOG)
    def test_reversed_cpu_order(self):
        f=specimen();f['original_cpu_events'][1]['pc']=p.ORDER[3]
        with self.assertRaisesRegex(ValueError,'instruction order'):p.verify(f,LOG)
    def test_no_chain(self):
        f=specimen();f['original_cpu_events']=[]
        with self.assertRaisesRegex(ValueError,'empty'):p.verify(f,LOG)
    def test_unfinished_not_counted(self):
        f=specimen();f['original_cpu_events'].append({'t':9.,'pc':p.ORDER[0],'main':2,'r0':'0x0','sp':'0x3007cc4','r3':'0x2001ef1','old_pp_byte':20})
        out=p.verify(f,LOG)
        self.assertEqual(out['trailing_incomplete_pp_chain_events'],1)
        self.assertEqual(out['original_cpu_chains'],1)
    def test_meta_markers_do_not_certify_request(self):
        f=specimen();f['original_cpu_events']=[
          {'t':0.1,'pc':p.EMITTER,'main':2,'r0':'0x0','r2':'0xa'},
          {'t':0.2,'pc':p.COPIER,'main':2,'r0':'0x0','r1':'0x1','r3':'0x6'},
          {'t':0.3,'pc':p.POST_A,'main':2},
          {'t':0.4,'pc':p.COMPLETE,'main':2,'r0':'0x0'},
        ]+f['original_cpu_events']
        out=p.verify(f,LOG)
        self.assertEqual(out['original_engine_owned_one_use_request_reply'],'UNPROVEN')
        self.assertEqual(out['observed_original_pc_markers']['original_copy_A_postloop_candidate_hits'],1)

if __name__ == '__main__':unittest.main()
