#!/usr/bin/env python3
"""Generated fake ROM and fake event records ONLY."""
import copy
import unittest

from test_private_rom_controller_lineage import fixture as fake_rom, put
from test_private_actor0_response_pp_join import fixture as fake_move_pp
import audit_private_action_move_pp_chain as audit


def action_rows():
    # A complete independent action-0 response packet, at frame 999.
    return [dict(f=999,pc=f'0x{pc:08x}',raw_pc=f'0x{pc+4:08x}',
                 dst=f'0x{0x02001000+off:08x}',width=w,value=v,
                 lr='0x08017211',r=[0,1,0,256,0,0,0,0])
            for pc,off,w,v in zip((0x0806BD8A,0x0806BD8E,0x0806BD92,
                                   0x0806BD98,0x0806BD9E),
                                  (0,1,2,4,5),(1,1,2,1,1),(32,0,256,0,0))]


def fixture():
    rom=fake_rom()
    put(rom,0x0809E6BA,0x700E)  # generated fake PP STRB instruction
    # Source-only synthetic parent fixture includes the actual move and PP
    # instruction encoding; no private bytes are used here.
    from test_private_actor0_response_pp_join import fixture as fake
    _, move, pp=fake()
    return rom,action_rows()+move,pp


class ActionMovePpTests(unittest.TestCase):
    def call(self,rom,rows,pp):return audit.evaluate(rom,rows,pp,900)
    def test_positive_is_unverified(self):
        r,rows,pp=fixture()
        z=self.call(r,rows,pp)
        self.assertEqual(z['joined_fight_move_pp_candidates_UNVERIFIED'],1)
        for name in ('smart_auto_planner_identity_certified',
                     'original_move_target_legality_certified',
                     'original_manual_fallback_certified',
                     'no_automatic_forced_switch_certified',
                     'production_authorized'):
            self.assertIs(z[name],False)
        self.assertEqual(z['native_acceptance_scenarios'],0)

    def test_no_fight_fails_closed(self):
        r,rows,pp=fixture()
        self.assertEqual(self.call(r,rows[5:],pp)['joined_fight_move_pp_candidates_UNVERIFIED'],0)

    def test_wrong_battler_action_lr_destination_and_payload(self):
        for i,key,value in ((0,'lr','0x08017215'),(0,'value',0),
                            (0,'dst','0x02001020'),(1,'value',10),
                            (2,'width',1),(3,'raw_pc','0x0806bd99'),
                            (4,'guest_writes',True)):
            with self.subTest(key=key,i=i):
                r,rows,pp=fixture();rows[i][key]=value
                self.assertEqual(self.call(r,rows,pp)['joined_fight_move_pp_candidates_UNVERIFIED'],0)
        r,rows,pp=fixture();rows[0]['r'][0]=1
        self.assertEqual(self.call(r,rows,pp)['joined_fight_move_pp_candidates_UNVERIFIED'],0)

    def test_old_and_late_action_fails(self):
        for frame in (990,1000,1001):
            r,rows,pp=fixture()
            for x in rows[:5]:x['f']=frame
            self.assertEqual(self.call(r,rows,pp)['joined_fight_move_pp_candidates_UNVERIFIED'],0)

    def test_duplicated_action_is_ambiguous(self):
        r,rows,pp=fixture();rows=copy.deepcopy(rows[:5])+rows
        self.assertEqual(self.call(r,rows,pp)['joined_fight_move_pp_candidates_UNVERIFIED'],0)

    def test_source_call_boundary_mutation_does_not_promote(self):
        r,rows,pp=fixture()
        put(r,0x08017204,0x2202)
        self.assertEqual(self.call(r,rows,pp)['joined_fight_move_pp_candidates_UNVERIFIED'],0)

    def test_no_move_pp_evidence_fails(self):
        r,rows,pp=fixture()
        self.assertEqual(self.call(r,rows,pp[:1])['joined_fight_move_pp_candidates_UNVERIFIED'],0)


if __name__=='__main__':unittest.main()
