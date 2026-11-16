"""Generated-only traces; no original ROM, save, memory or private CPU log."""
import copy
import unittest
from audit_original_transfer_lineage import Pins, EvidenceError, audit

P = Pins(0x02001000,0x02002000,0x02003000,
         0x08001001,0x08001003,0x08001005,
         0x08001007,0x08001111,0x08002223,0x08003335,0x02004000)


def payload(pp=(12,5,6,7),moves=(11,22,33,44)):
    z=bytearray(40)
    z[:4]=bytes((19,0,0,0))
    for i,m in enumerate(moves):
        z[4+2*i:6+2*i]=m.to_bytes(2,'little')
        z[12+i]=pp[i]
        z[16+i]=max(1,pp[i]) if m else 0
    z[20:24]=b'FAKE'
    return bytes(z)


def row(f,pc,base,dst,old,new):
    return dict(f=f,pc=pc,base=base,dst=dst,width=1,
                before=old.hex(),after=new.hex())


def fixture(two=True):
    stores=[];replies=[];pps=[]
    frames=(100,200) if two else (100,)
    for n,f in enumerate(frames):
        current=(12,5,6,7-n)
        b=payload(current)
        old=bytes(40)
        header=bytearray(old);header[0]=19
        stores.append(row(f,P.header_writer_pc,P.transfer_buffer,P.transfer_buffer,old,bytes(header)))
        stores.append(row(f,P.payload_writer_pc,P.transfer_buffer,P.transfer_buffer+39,bytes(header),b))
        stores.append(row(f,P.copy_writer_pc,P.player_receive_buffer,P.player_receive_buffer,old,b))
        other=payload((9,9,9,9),(55,66,77,88))
        stores.append(row(f,P.copy_writer_pc,P.other_receive_buffer,P.other_receive_buffer,old,other))
        replies.append(dict(f=f-1,pc=P.response_writer_pc,lr=P.original_fight_lr,value=0,actor=0))
        replies.append(dict(f=f,pc=P.response_writer_pc,lr=P.original_move_lr,value=10,actor=0))
        pps.append(dict(f=f+7,raw_pc=P.original_pp_raw_pc,
                        address=P.player_pp_base+0x28,width=1,
                        before=current[3],after=current[3]-1,target=0))
    return stores,replies,pps


class PositiveTests(unittest.TestCase):
    def test_two_independent_request_pp_candidates(self):
        out=audit(*fixture(),P)
        self.assertEqual(len(out['candidates']),2)
        self.assertEqual([x['debited_slot'] for x in out['candidates']],[3,3])
        self.assertEqual(out['formal_native_acceptance'],0)
        self.assertIs(out['native_legality_certified'],False)
        self.assertIs(out['manual_fallback_certified'],False)
        self.assertIs(out['no_forced_switch_certified'],False)
        self.assertIs(out['production_authorized'],False)
        for candidate in out['candidates']:
            self.assertIs(candidate['original_transfer_to_player_candidate_UNVERIFIED'],True)
            self.assertIs(candidate['installed_adapter_executed'],False)
            self.assertEqual(candidate['native_accepted'],0)
    def test_one_request(self):
        out=audit(*fixture(two=False),P)
        self.assertEqual(len(out['candidates']),1)
        self.assertEqual(out['candidates'][0]['frame'],100)
    def test_unrelated_writer_does_not_get_attributed(self):
        a,b,c=fixture()
        c.insert(0,dict(f=106,raw_pc=0x08009999,address=P.player_pp_base+0x28,width=1,
                        before=7,after=6,target=0))
        self.assertEqual(len(audit(a,b,c,P)['candidates']),2)
    def test_foe_pp_store_not_counted(self):
        a,b,c=fixture()
        c.insert(0,dict(f=106,raw_pc=P.original_pp_raw_pc,
                 address=P.player_pp_base+0x28,width=1,before=7,after=6,target=1))
        self.assertEqual(len(audit(a,b,c,P)['candidates']),2)
    def test_peer_buffer_optional_when_explicitly_disabled(self):
        a,b,c=fixture()
        a=[x for x in a if x['base']!=P.other_receive_buffer]
        self.assertEqual(len(audit(a,b,c,P,require_other=False)['candidates']),2)
    def test_empty_trailing_move_slot_accepted(self):
        a,b,c=fixture(two=False)
        z=payload((12,5,0,0),(11,22,0,0))
        a[1]['after']=z.hex();a[2]['after']=z.hex()
        c[0]['address']=P.player_pp_base+0x26
        c[0]['before']=5;c[0]['after']=4
        self.assertEqual(audit(a,b,c,P)['candidates'][0]['debited_slot'],1)


class RejectTests(unittest.TestCase):
    def denied(self,transform):
        a,b,c=fixture()
        transform(a,b,c)
        with self.assertRaises(EvidenceError):audit(a,b,c,P)
    def test_original_source_header_missing(self):self.denied(lambda a,b,c:a.pop(0))
    def test_original_body_missing(self):self.denied(lambda a,b,c:a.pop(1))
    def test_original_copy_missing(self):self.denied(lambda a,b,c:a.pop(2))
    def test_original_peer_missing(self):self.denied(lambda a,b,c:a.pop(3))
    def test_original_header_opcode_mismatch(self):self.denied(lambda a,b,c:a[0].update(pc=999))
    def test_original_payload_writer_pc_mismatch(self):self.denied(lambda a,b,c:a[1].update(pc=999))
    def test_original_copy_writer_pc_mismatch(self):self.denied(lambda a,b,c:a[2].update(pc=999))
    def test_original_actor_receiver_mismatch(self):self.denied(lambda a,b,c:a[2].update(base=P.other_receive_buffer))
    def test_source_destination_buffer_drift(self):self.denied(lambda a,b,c:a[1].update(after=payload((12,5,6,4)).hex()))
    def test_wrong_header_not_accepted(self):
        def mut(a,b,c):
            z=bytearray(bytes.fromhex(a[2]['after']));z[1]=1
            a[1]['after']=bytes(z).hex();a[2]['after']=bytes(z).hex()
        self.denied(mut)
    def test_not_40_bytes(self):self.denied(lambda a,b,c:a[2].update(after=a[2]['after'][:-2]))
    def test_wrong_move_id_encoding(self):
        def mut(a,b,c):
            z=bytearray(bytes.fromhex(a[2]['after']));z[4]=0;z[5]=0
            a[1]['after']=bytes(z).hex();a[2]['after']=bytes(z).hex()
        self.denied(mut)
    def test_bad_max_pp_under_current(self):
        def mut(a,b,c):
            z=bytearray(bytes.fromhex(a[2]['after']));z[16]=1
            a[1]['after']=bytes(z).hex();a[2]['after']=bytes(z).hex()
        self.denied(mut)
    def test_zero_maximum_for_populated_move(self):
        def mut(a,b,c):
            z=bytearray(bytes.fromhex(a[2]['after']));z[16]=0;z[12]=0
            a[1]['after']=bytes(z).hex();a[2]['after']=bytes(z).hex()
        self.denied(mut)
    def test_original_fight_missing(self):self.denied(lambda a,b,c:b.pop(0))
    def test_original_move_missing(self):self.denied(lambda a,b,c:b.pop(1))
    def test_wrong_fight_lr(self):self.denied(lambda a,b,c:b[0].update(lr=100))
    def test_wrong_move_lr(self):self.denied(lambda a,b,c:b[1].update(lr=100))
    def test_wrong_response_pc(self):self.denied(lambda a,b,c:b[1].update(pc=100))
    def test_wrong_reply_frame(self):self.denied(lambda a,b,c:b[1].update(f=120))
    def test_missing_pp_writer(self):self.denied(lambda a,b,c:c.pop(0))
    def test_wrong_pp_writer_pc(self):self.denied(lambda a,b,c:c[0].update(raw_pc=100))
    def test_wrong_pp_byte_width(self):self.denied(lambda a,b,c:c[0].update(width=2))
    def test_wrong_pp_owner(self):self.denied(lambda a,b,c:c[0].update(target=1))
    def test_wrong_pp_slot_address(self):self.denied(lambda a,b,c:c[0].update(address=P.player_pp_base+0x24))
    def test_wrong_pp_before(self):self.denied(lambda a,b,c:c[0].update(before=100))
    def test_wrong_pp_delta(self):self.denied(lambda a,b,c:c[0].update(after=5))
    def test_wrong_pp_too_late(self):self.denied(lambda a,b,c:c[0].update(f=198))
    def test_duplicate_player_pp_store(self):
        def mut(a,b,c):c.insert(1,copy.deepcopy(c[0]))
        self.denied(mut)
    def test_next_buffer_pp_not_matching(self):
        def mut(a,b,c):
            z=bytearray(bytes.fromhex(a[6]['after']));z[15]=11;z[19]=11
            a[5]['after']=bytes(z).hex();a[6]['after']=bytes(z).hex()
        self.denied(mut)
    def test_wrong_peer_identical(self):
        def mut(a,b,c):a[3]['after']=a[2]['after'];a[7]['after']=a[6]['after']
        self.denied(mut)
    def test_out_of_order_frames(self):self.denied(lambda a,b,c:a[0].update(f=400))
    def test_invalid_base_type(self):self.denied(lambda a,b,c:a[0].update(base='bogus'))
    def test_invalid_hex_length(self):self.denied(lambda a,b,c:a[0].update(before='ff'))
    def test_empty_rows(self):
        with self.assertRaises(EvidenceError):audit([],[],[],P)
    def test_too_many_rows(self):
        a,b,c=fixture()
        with self.assertRaises(EvidenceError):audit(a*3000,b,c,P)
    def test_wrong_pins_duplicate_buffers(self):
        a,b,c=fixture()
        bad=Pins(P.transfer_buffer,P.player_receive_buffer,P.player_receive_buffer,
            P.header_writer_pc,P.payload_writer_pc,P.copy_writer_pc,P.response_writer_pc,
            P.original_fight_lr,P.original_move_lr,P.original_pp_raw_pc,P.player_pp_base)
        with self.assertRaises(EvidenceError):audit(a,b,c,bad)



class AttributionTests(unittest.TestCase):
    def test_unrelated_nonplayer_action_cannot_supply_player_owner(self):
        a,b,c=fixture()
        b[0]['actor']=1
        with self.assertRaises(EvidenceError):audit(a,b,c,P)
    def test_unrelated_nonplayer_move_cannot_supply_player_move(self):
        a,b,c=fixture()
        b[1]['actor']=1
        with self.assertRaises(EvidenceError):audit(a,b,c,P)
    def test_extra_nonplayer_reply_is_not_a_duplicate_player(self):
        a,b,c=fixture()
        other=copy.deepcopy(b[1]);other['actor']=1
        b.insert(2,other)
        self.assertEqual(len(audit(a,b,c,P)['candidates']),2)
    def test_duplicate_original_player_move_refused(self):
        a,b,c=fixture();b.insert(2,copy.deepcopy(b[1]))
        with self.assertRaises(EvidenceError):audit(a,b,c,P)
    def test_duplicate_original_player_fight_refused(self):
        a,b,c=fixture();b.insert(1,copy.deepcopy(b[0]))
        with self.assertRaises(EvidenceError):audit(a,b,c,P)
    def test_duplicate_command_header_transition_refused(self):
        a,b,c=fixture();a.insert(1,copy.deepcopy(a[0]))
        with self.assertRaises(EvidenceError):audit(a,b,c,P)
    def test_last_epoch_pp_must_debit_exactly_one_independently(self):
        a,b,c=fixture(two=False)
        c[0]['after']=5  # 7→5, with NO later request to supply a second rejection
        with self.assertRaises(EvidenceError):audit(a,b,c,P)
    def test_last_epoch_pp_must_match_source_before(self):
        a,b,c=fixture(two=False)
        c[0]['before']=9;c[0]['after']=8
        with self.assertRaises(EvidenceError):audit(a,b,c,P)

    def test_next_request_continuity_is_independently_pinned(self):
        a,b,c=fixture(two=True)
        later=bytearray(bytes.fromhex(a[6]['after']))
        later[15]=5  # later original request had PP=5, previous writer produced 6
        a[5]['after']=bytes(later).hex()
        a[6]['after']=bytes(later).hex()
        c[1]['before']=5;c[1]['after']=4  # second epoch locally consistent
        with self.assertRaises(EvidenceError):audit(a,b,c,P)

    def test_bad_empty_move_with_pp_refused(self):
        a,b,c=fixture(two=False)
        z=bytearray(payload((12,5,0,0),(11,22,0,0)))
        z[14]=1;z[18]=1
        a[1]['after']=bytes(z).hex();a[2]['after']=bytes(z).hex()
        with self.assertRaises(EvidenceError):audit(a,b,c,P)


if __name__=='__main__':unittest.main()
