#!/usr/bin/env python3
"""Thirty synthetic regressions; no real private game bytes or trace."""
import unittest
import verify_second_wild_auto as v

def ev(pc,frame,**kw):
    r=dict(pc=pc,frame=frame,r0=0,r1=0,r2=0,r3=0,pending=0,
           reply_valid=0,reply_header=0,reply_payload=0)
    r.update(kw);return r

def fixture():
    events=[]; times=[4692,4820,4951,5095,5263,5449,5613,5795]
    for n,(t,slot) in enumerate(zip(times,v.SLOTS)):
        payload=256|slot
        if n:events.append(ev('0x806bd80',t,r0=0,r2=0,r3=256))
        events.extend([ev('0x9f1f000',t),ev('0x8065eb4',t),
            ev('0x806bd80',t,r0=0,r2=10,r3=payload),
            ev('0x806b370',t,r0=0,r1=1,r3=6,reply_valid=1,
               reply_header=0x0a20,reply_payload=payload),
            ev('0x806261c',t,r0=0),ev('0x8094330',t+1,r0=0),
            ev('0x809435c',t+1,r0=slot),
            ev('0x8094374',t+1,r0=v.MOVE_IDS[slot]),
            ev('0x8094380',t+1,r2=1)])
    pp=[[20,9,10,19],[20,9,10,18],[20,8,9,18],[20,7,9,18],
        [20,7,9,18],[20,7,9,18]]
    chunks=[]
    for i in range(6):
        beg=4692+i*350;end=beg+350
        chunks.append(dict(chunk=i,begin=beg,end=end,steps=20000000,
            events=sum(beg<=e['frame']<end for e in events),
            auto=[[t,256|slot] for t,slot in zip(times,v.SLOTS) if beg<=t<end],
            pp=pp[i],flags='0x4',pending='0x0',manual_menu=0))
    return dict(schema=v.SCHEMA,rom_sha256=v.ROM_SHA,save_sha256=v.SAVE_SHA,
        preconstructor_sha256=v.PRE_SHA,pending_state_sha256=v.PENDING_SHA,
        request_sha256=v.REQUEST_SHA,request_copy_stores=44,
        pending_after_copy_steps=23,actor0_installer=1,foe_installer=1,
        player_kind=1,foe_kind=3,battle_flags=4,battlers=2,
        host_move_menu_inputs=0,guest_memory_writes=0,new_native_hook_installed=False,
        samples=chunks,events=events)

class SecondWild(unittest.TestCase):
    def reject(self,change):
        r=fixture();change(r)
        with self.assertRaises(ValueError):v.attest(r)
    def test_valid_synthetic(self):
        z=v.attest(fixture());self.assertEqual(z['second_wild_player_native_move_submissions'],8)
        self.assertEqual(z['second_wild_observed_player_PP_decrements'],6)
        self.assertFalse(z['whole_battle_terminal_certified'])
    def test_bad_rom(self):self.reject(lambda x:x.update(rom_sha256='bad'))
    def test_bad_save(self):self.reject(lambda x:x.update(save_sha256='bad'))
    def test_same_state(self):self.reject(lambda x:x.update(pending_state_sha256=v.FIRST_PENDING_SHA))
    def test_preconstructor(self):self.reject(lambda x:x.update(preconstructor_sha256='bad'))
    def test_bad_request_sha(self):self.reject(lambda x:x.update(request_sha256='bad'))
    def test_copy_length(self):self.reject(lambda x:x.update(request_copy_stores=43))
    def test_no_player_installer(self):self.reject(lambda x:x.update(actor0_installer=0))
    def test_no_enemy_installer(self):self.reject(lambda x:x.update(foe_installer=0))
    def test_wrong_enemy_controller(self):self.reject(lambda x:x.update(foe_kind=1))
    def test_trainer(self):self.reject(lambda x:x.update(battle_flags=8))
    def test_host_menu_input(self):self.reject(lambda x:x.update(host_move_menu_inputs=1))
    def test_guest_write(self):self.reject(lambda x:x.update(guest_memory_writes=1))
    def test_new_hook_claim(self):self.reject(lambda x:x.update(new_native_hook_installed=True))
    def test_payload_target(self):self.reject(lambda x:x['events'][2].update(r3=515))
    def test_action_not_move(self):self.reject(lambda x:x['events'][2].update(r2=9))
    def test_missing_reply(self):self.reject(lambda x:x['events'].pop(3))
    def test_wrong_reply_header(self):self.reject(lambda x:x['events'][3].update(reply_header=0))
    def test_missing_completion(self):self.reject(lambda x:x['events'].pop(4))
    def test_missing_validator(self):self.reject(lambda x:x['events'].pop(5))
    def test_wrong_slot(self):self.reject(lambda x:x['events'][6].update(r0=0))
    def test_wrong_move(self):self.reject(lambda x:x['events'][7].update(r0=123))
    def test_wrong_target(self):self.reject(lambda x:x['events'][8].update(r2=0))
    def test_missing_preflight(self):self.reject(lambda x:x['events'].pop(1))
    def test_extra_player_item(self):self.reject(lambda x:x['events'].append(ev('0x806bd80',6792,r0=0,r2=9)))
    def test_unchanged_pp(self):self.reject(lambda x:x['samples'][-1].update(pp=[20,10,10,20]))
    def test_overdebit_pp(self):self.reject(lambda x:x['samples'][-1].update(pp=[20,0,10,10]))
    def test_no_quiet_tail(self):self.reject(lambda x:x['samples'][-1].update(events=1))
    def test_bad_frame_gap(self):self.reject(lambda x:x['samples'][3].update(begin=0))
    def test_unexpected_private_field(self):self.reject(lambda x:x['events'][0].update(game_bytes='raw'))
    def test_out_of_order(self):self.reject(lambda x:x['events'][5].update(frame=0))
    def test_missing_events(self):self.reject(lambda x:x.update(events=[]))

if __name__=='__main__':unittest.main()
