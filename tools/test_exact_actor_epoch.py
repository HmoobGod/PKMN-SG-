#!/usr/bin/env python3
"""Synthetic denial suite only; no authentic modified-ROM gameplay trace."""
import copy
import unittest
import verify_exact_actor_epoch as v
import verify_exact_outcome_pp_edges as base


def edge(kind,step,pc,**fields):
    row={k:0 for k in base.FIELDS}
    row.update(frame=4000+step//3,step=step,pc=pc,kind=kind,
               slot=255,flags=4,battlers=2,inbattle=2,
               callback1=0x0808CBDD,callback2=0x0808F225)
    row.update(fields)
    return row


def chain(start,slot=0,with_pp=True):
    packed=256+slot
    r=[
        edge(6,start,0x0806BD80,r0=0,r2=10,r3=packed),
        edge(7,start+1,0x0806B370,r0=0,r1=1,r3=6),
        edge(12,start+2,0x0806261C,r0=0),
        edge(13,start+3,0x08094330,r0=0),
        edge(14,start+4,0x0809435C,r0=slot),
        edge(15,start+5,0x08094374,r0=v.MOVE_IDS[slot]),
        edge(16,start+6,0x08094380,r2=1)]
    if with_pp:
        r.append(edge(5,start+8,0x0809E6BA,address=base.PP+slot,
                      slot=slot,before=20,after=19,r1=base.PP+slot))
    return r


def fixture():
    return dict(schema=base.SCHEMA,current_sha256=base.CURRENT,
                modified_sha256=base.MODIFIED,save_sha256=base.SAVE,
                guest_writes=0,host_move_menu_inputs=0,new_hook_installed=False,
                candidate_outcome_byte_address=0,status=1,steps=300,
                events=chain(1)+chain(20,1,False))


class ActorEpochTests(unittest.TestCase):
    def test_realistic_synthetic_two_commands_one_pp(self):
        r=v.correlate(fixture())
        self.assertEqual(r["candidate_player_submissions"],2)
        self.assertEqual(r["complete_reply_commit_chains"],2)
        self.assertEqual(r["original_pp_writer_debits"],1)
        self.assertEqual(r["original_submissions_without_matched_writer"],1)
        self.assertFalse(r["unmatched_submissions_reason_certified"])
        self.assertFalse(r["production_promotion_authorized"])
    def denied(self,change):
        d=fixture();change(d)
        with self.assertRaises(ValueError):v.correlate(d)
    def test_bad_target(self):self.denied(lambda d:d["events"][0].update(r3=0))
    def test_enemy_emitter(self):self.denied(lambda d:d["events"][0].update(r0=1))
    def test_non_move_emitter(self):self.denied(lambda d:d["events"][0].update(r2=9))
    def test_invalid_slot(self):self.denied(lambda d:d["events"][0].update(r3=260))
    def test_wrong_battle_flags(self):self.denied(lambda d:d["events"][0].update(flags=8))
    def test_wrong_battlers(self):self.denied(lambda d:d["events"][0].update(battlers=4))
    def test_main_not_in_battle(self):self.denied(lambda d:d["events"][0].update(inbattle=0))
    def test_duplicate_reply(self):self.denied(lambda d:d["events"].insert(2,copy.deepcopy(d["events"][1])))
    def test_missing_reply(self):self.denied(lambda d:d["events"].pop(1))
    def test_missing_completion(self):self.denied(lambda d:d["events"].pop(2))
    def test_missing_validator(self):self.denied(lambda d:d["events"].pop(3))
    def test_wrong_slot_commit(self):self.denied(lambda d:d["events"][4].update(r0=1))
    def test_wrong_move_commit(self):self.denied(lambda d:d["events"][5].update(r0=92))
    def test_wrong_target_commit(self):self.denied(lambda d:d["events"][6].update(r2=0))
    def test_writer_before_target(self):self.denied(lambda d:d["events"].insert(6,d["events"].pop(7)))
    def test_wrong_pp_slot(self):self.denied(lambda d:d["events"][7].update(slot=1,address=base.PP+1,r1=base.PP+1))
    def test_wrong_writer_pointer(self):self.denied(lambda d:d["events"][7].update(r1=base.PP+1))
    def test_double_debit(self):
        def change(d):
            x=copy.deepcopy(d["events"][7]);x.update(step=10,frame=4003,before=19,after=18)
            d["events"].insert(8,x)
        self.denied(change)
    def test_after_exit_debit(self):self.denied(lambda d:d["events"][7].update(inbattle=0))
    def test_backward_frame(self):self.denied(lambda d:d["events"][7].update(frame=1))
    def test_guest_write(self):self.denied(lambda d:d.update(guest_writes=1))
    def test_incomplete_trace(self):self.denied(lambda d:d.update(status=2))
    def test_invalid_original_rom(self):self.denied(lambda d:d.update(current_sha256="fake"))
    def test_confounding_write_not_a_debit(self):
        d=fixture();d["events"][7].update(pc=0x081FB8DA)
        x=v.correlate(d)
        self.assertEqual(x["original_pp_writer_debits"],0)
        self.assertEqual(x["non_writer_pp_byte_mutations"],1)
        self.assertEqual(x["original_submissions_without_matched_writer"],2)
    def test_no_pp_is_not_proof_of_cancellation(self):
        d=fixture();d["events"].pop(7)
        x=v.correlate(d)
        self.assertEqual(x["original_submissions_without_matched_writer"],2)
        self.assertFalse(x["manual_fallback_or_full_terminal_certified"])
    def test_missing_chain_without_writer_stays_unproven(self):
        d=fixture();d["events"].pop(-1)
        x=v.correlate(d)
        self.assertEqual(x["complete_reply_commit_chains"],1)
        self.assertFalse(x["dynamic_legality_or_one_use_ownership_certified"])


    @staticmethod
    def main_bit_edge(step, before, after):
        # Actual C observer kind2 watcher (Main.inBattle), including bit0
        # updates. This is a source-only synthetic event, not private CPU.
        return edge(2, step, 0x081C1234, address=base.MAIN+0x439,
                    before=before, after=after, inbattle=after)

    @staticmethod
    def native_writer(step, slot=0):
        return edge(5, step, 0x0809E6BA, address=base.PP+slot,
                    slot=slot, before=20, after=19, r1=base.PP+slot)

    def test_main_clear_closes_incomplete_candidate_without_cancellation_claim(self):
        d=fixture()
        d["events"]=chain(1,0,False)+[self.main_bit_edge(10,2,0)]
        report=v.correlate(d)
        self.assertEqual(report["candidate_player_submissions"],1)
        self.assertEqual(report["original_submissions_without_matched_writer"],1)
        self.assertFalse(report["unmatched_submissions_reason_certified"])
        self.assertFalse(report["manual_fallback_or_full_terminal_certified"])

    def test_main_clear_then_set_cannot_rearm_stale_player0_request(self):
        d=fixture()
        d["events"]=(chain(1,0,False)
                     +[self.main_bit_edge(10,2,0),
                       self.main_bit_edge(12,0,2),
                       self.native_writer(15,0)])
        self.denied(lambda original: original.update(events=d["events"]))

    def test_main_clear_without_reentry_does_not_reuse_writer(self):
        d=fixture()
        d["events"]=(chain(1,0,False)+
                     [self.main_bit_edge(10,2,0),self.native_writer(12,0)])
        self.denied(lambda original: original.update(events=d["events"]))

    def test_new_original_emitter_after_reentry_may_start_distinct_candidate(self):
        d=fixture()
        d["events"]=(chain(1,0,False)
                     +[self.main_bit_edge(10,2,0),
                       self.main_bit_edge(12,0,2)]
                     +chain(20,1,True))
        report=v.correlate(d)
        self.assertEqual(report["candidate_player_submissions"],2)
        self.assertEqual(report["complete_reply_commit_chains"],2)
        self.assertEqual(report["original_pp_writer_debits"],1)
        self.assertEqual(report["original_submissions_without_matched_writer"],1)
        self.assertFalse(report["unmatched_submissions_reason_certified"])
        self.assertFalse(report["dynamic_legality_or_one_use_ownership_certified"])

    def test_main_bit0_only_does_not_cancel_live_candidate(self):
        d=fixture()
        d["events"]=(chain(1,0,False)
                     +[self.main_bit_edge(10,2,3),self.native_writer(12,0)])
        report=v.correlate(d)
        self.assertEqual(report["candidate_player_submissions"],1)
        self.assertEqual(report["original_pp_writer_debits"],1)
        self.assertEqual(report["original_submissions_without_matched_writer"],0)
        self.assertFalse(report["production_promotion_authorized"])

    def test_main_clear_followed_by_manual_marker_is_not_auto_certification(self):
        d=fixture()
        d["events"]=(chain(1,0,False)
                     +[self.main_bit_edge(10,2,0),
                       edge(8,12,0x0806449C)])
        result=v.correlate(d)
        self.assertEqual(result["original_pp_writer_debits"],0)
        self.assertFalse(result["manual_fallback_or_full_terminal_certified"])


if __name__=="__main__":unittest.main()
