#!/usr/bin/env python3
"""Source-only and synthetic-CPU tests; NEVER open ROM/SAV.

Run: python3 -m unittest -v test_r4_source_only_repairs.py
All binary bytes manufactured by fixtures are NEW synthetic test values.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import os
import tempfile
import unittest

HERE=Path(__file__).resolve().parent

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    module=importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

b=load('r4_b','build_r4_disposable_failclosed.py')
a=load('r4_c','audit_r4_cfg_v2.py')
l=load('r4_l','verify_r4_source_layout.py')


class Builder(unittest.TestCase):
    def test_01_source_hash_matches_exact_approval(self):
        self.assertEqual(b.sha(b.SOURCE.read_bytes()), b.SOURCE_SHA256)

    def test_02_binary_rebuild_hash_pinned(self):
        with tempfile.TemporaryDirectory() as d:
            code=b.build_assembly('clang','llvm-objcopy',Path(d))
            self.assertEqual(len(code),252)
            self.assertEqual(b.sha(code),b.GUARD_SHA256)

    def test_03_mutated_source_aborts_before_build_directory(self):
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            bad=home/'mutated.s';bad.write_bytes(b.SOURCE.read_bytes()+b'\n@tampered\n')
            work=home/'not-created'
            with self.assertRaisesRegex(RuntimeError,'source hash mismatch'):
                b.build_assembly('clang','llvm-objcopy',work,bad)
            self.assertFalse(work.exists())

    def test_04_bad_binary_hash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            wrapper=home/'mutator.sh'
            wrapper.write_text('#!/bin/sh\n'
                  'llvm-objcopy "$@" || exit $?\n'
                  'python3 - "$@" <<\'PY\'\n'
                  'import pathlib,sys\n'
                  'p=pathlib.Path(sys.argv[-1]);data=bytearray(p.read_bytes());data[12]^=1;p.write_bytes(data)\n'
                  'PY\n')
            wrapper.chmod(0o755)
            with self.assertRaisesRegex(RuntimeError,'guard binary hash mismatch'):
                b.build_assembly('clang',str(wrapper),home/'build')

    def test_05_rom_output_must_be_gba(self):
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            for ext in ['sav','bin','txt']:
                with self.subTest(ext=ext),self.assertRaisesRegex(RuntimeError,'must be .gba'):
                    b.verify_output_paths(home/'source.gba',home/'save.sav',home/('test.'+ext))

    def test_06_sidecar_collision_blocks_before_rom_output(self):
        with tempfile.TemporaryDirectory() as d:
            home=Path(d);(home/'candidate.sav').write_bytes(b'old-save')
            with self.assertRaisesRegex(RuntimeError,'output exists'):
                b.verify_output_paths(home/'source.gba',home/'save.sav',home/'candidate.gba')
            self.assertFalse((home/'candidate.gba').exists())
            self.assertEqual((home/'candidate.sav').read_bytes(),b'old-save')

    def test_07_symlink_output_refused(self):
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            src=home/'source.gba';src.write_bytes(b'SYNTH')
            (home/'candidate.gba').symlink_to(src)
            with self.assertRaises(RuntimeError):
                b.verify_output_paths(src,home/'source.sav',home/'candidate.gba')
            self.assertEqual(src.read_bytes(),b'SYNTH')

    def test_08_exclusive_commit_rejects_preexisting_sidecar(self):
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            (home/'candidate.sav').write_bytes(b'older fixture')
            with self.assertRaises(RuntimeError):
                b.commit_exclusive(home/'candidate.gba',b'SYNTHETIC_GBA',home/'candidate.sav',b'SYNTHETIC_SAV')
            self.assertFalse((home/'candidate.gba').exists())
            self.assertEqual((home/'candidate.sav').read_bytes(),b'older fixture')

    def test_09_exclusive_commit_installs_two_synthetic_files(self):
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            b.commit_exclusive(home/'candidate.gba',b'FAKE_TEST_GBA',home/'candidate.sav',b'FAKE_TEST_SAV')
            self.assertEqual((home/'candidate.gba').read_bytes(),b'FAKE_TEST_GBA')
            self.assertEqual((home/'candidate.sav').read_bytes(),b'FAKE_TEST_SAV')
            with self.assertRaises(RuntimeError):
                b.commit_exclusive(home/'candidate.gba',b'FAKE_NEW',home/'candidate.sav',b'FAKE_NEW')
            self.assertEqual((home/'candidate.gba').read_bytes(),b'FAKE_TEST_GBA')

    def test_10_invalid_rom_or_sav_identity_fails_closed(self):
        with self.assertRaises(RuntimeError):
            b.validate_inputs(b'NOT_A_ROM',b'NOT_A_SAVE',252)


class R7Dataflow(unittest.TestCase):
    def assert_rw(self,op,args,read,write):
        self.assertEqual(a.rw_r7(a.Ins(0,op,args)),(read,write))

    def test_11_mov_r7_r11_is_pure_definition(self):
        self.assert_rw('mov','r7, r11',False,True)
    def test_12_mov_r7_r7_reads_old_value(self):
        self.assert_rw('mov','r7, r7',True,True)
    def test_13_ldr_r7_from_its_own_address_reads_old_value(self):
        self.assert_rw('ldr','r7, [r7]',True,True)
    def test_14_lsls_r7_r7_reads_old_value(self):
        self.assert_rw('lsls','r7, r7, #1',True,True)
    def test_15_adds_r7_r7_reads_old_value(self):
        self.assert_rw('adds','r7, r7, #1',True,True)
    def test_16_implicit_two_operand_add_reads_old_value(self):
        self.assert_rw('adds','r7, #1',True,True)
    def test_17_ldr_r7_from_r2_is_pure_definition(self):
        self.assert_rw('ldrb','r7, [r2]',False,True)
    def test_18_push_and_pop_correctly_model_save_restore(self):
        self.assert_rw('push','{r4,r7,lr}',True,False)
        self.assert_rw('pop','{r4,r7}',False,True)
    def test_19a_implicit_two_operand_register_shifts_read_r7(self):
        for op in ('lsls','lsrs','asrs','rors'):
            with self.subTest(op=op):
                self.assert_rw(op,'r7, r0',True,True)

    def test_19b_three_operand_shift_writes_without_old_r7(self):
        for op in ('lsls','lsrs','asrs'):
            with self.subTest(op=op):
                self.assert_rw(op,'r7, r0, #1',False,True)

    def test_19_r7_source_read_detected_in_store(self):
        self.assert_rw('str','r7, [r1]',True,False)

    def caller_fixture(self,unsafe=None):
        base=a.CALLER_RESUME
        return {
            base:a.Ins(base,'ldr','r3, [r0]'),
            base+2:a.Ins(base+2,'cmp','r3, #0'),
            base+4:a.Ins(base+4,'bl','0x000e0748',4),
            base+8:a.Ins(base+8,'beq',hex(a.CALLER_RESUME+0x20)),
            base+10:a.Ins(base+10,'mov','r3, r5'),
            base+12:a.Ins(base+12,'b',hex(0x65F04)),
            base+0x20:a.Ins(base+0x20,'lsrs','r7, r3, #0x18'),
            0x65F04:a.Ins(0x65F04,'ldrb','r7, [r2]'),
        }

    def test_20_predef_valid_synthetic_cfg(self):
        visited,defs,calls=a.predef_caller(self.caller_fixture())
        self.assertEqual(defs,{0x65F04,0x65F00})
        self.assertEqual(calls,{0x65EE4})

    def test_21_caller_fails_if_r7_read_before_definition(self):
        ins=self.caller_fixture()
        ins[0x65F00]=a.Ins(0x65F00,'mov','r7, r7')
        with self.assertRaisesRegex(a.UnsafeCFG,'r7 READ'):
            a.predef_caller(ins)


class CalleeCFG(unittest.TestCase):
    def callee(self):
        base=a.CALLEE_ENTRY
        return {
            base:a.Ins(base,'push','{r4, r5, r6, r7, lr}'),
            base+2:a.Ins(base+2,'mov','r7, r11'),
            base+4:a.Ins(base+4,'beq',hex(base+14)),
            base+6:a.Ins(base+6,'pop','{r4, r5, r6, r7}'),
            base+8:a.Ins(base+8,'pop','{r1}'),
            base+10:a.Ins(base+10,'bx','r1'),
            base+14:a.Ins(base+14,'pop','{r4, r5, r6, r7}'),
            base+16:a.Ins(base+16,'pop','{r1}'),
            base+18:a.Ins(base+18,'bx','r1'),
        }

    def test_22_two_synthetic_return_paths_restore_r7(self):
        result=a.callee_r7_all_returns(self.callee(),a.CALLEE_ENTRY)
        self.assertEqual(len(result['return_addresses']),2)

    def test_23_missing_restore_on_one_branch_fails(self):
        m=self.callee()
        at=a.CALLEE_ENTRY+14
        m[at]=a.Ins(at,'pop','{r4, r5, r6}')
        with self.assertRaisesRegex(a.UnsafeCFG,'restoration|unbalanced|original LR'):
            a.callee_r7_all_returns(m,a.CALLEE_ENTRY)

    def test_24_unparsed_callee_escape_fails_closed(self):
        m=self.callee()
        at=a.CALLEE_ENTRY+14
        m[at]=a.Ins(at,'b',hex(0xE1000))
        with self.assertRaisesRegex(a.UnsafeCFG,'callee escape'):
            a.callee_r7_all_returns(m,a.CALLEE_ENTRY)

    def test_25_unsafe_callee_r7_read_is_detected(self):
        m=self.callee()
        at=a.CALLEE_ENTRY+2
        m[at]=a.Ins(at,'ldr','r7, [r7]')
        with self.assertRaisesRegex(a.UnsafeCFG,'callee writes r7 but reads old value'):
            a.callee_r7_all_returns(m,a.CALLEE_ENTRY)

    def test_36_nested_r7_push_pop_does_not_fake_original_restore(self):
        base=a.CALLEE_ENTRY
        m={base:a.Ins(base,'push','{r4,r5,r6,r7,lr}'),
           base+2:a.Ins(base+2,'mov','r7, r11'),
           base+4:a.Ins(base+4,'push','{r7}'),
           base+6:a.Ins(base+6,'pop','{r7}'),
           base+8:a.Ins(base+8,'pop','{r4,r5,r6}'),
           base+10:a.Ins(base+10,'pop','{r1}'),
           base+12:a.Ins(base+12,'bx','r1')}
        with self.assertRaises(a.UnsafeCFG): a.callee_r7_all_returns(m,base)

    def test_37_unbalanced_pop_r7_must_not_pass(self):
        base=a.CALLEE_ENTRY
        m={base:a.Ins(base,'push','{r4,r5,r6,r7,lr}'),
           base+2:a.Ins(base+2,'mov','r7, r11'),
           base+4:a.Ins(base+4,'pop','{r7}'),
           base+6:a.Ins(base+6,'bx','lr')}
        with self.assertRaises(a.UnsafeCFG):a.callee_r7_all_returns(m,base)

    def test_38_bx_r3_not_a_return(self):
        m=self.callee();m[a.CALLEE_ENTRY+10]=a.Ins(a.CALLEE_ENTRY+10,'bx','r3')
        with self.assertRaisesRegex(a.UnsafeCFG,'unsupported BX target'):
            a.callee_r7_all_returns(m,a.CALLEE_ENTRY)

    def test_39_r1_from_wrong_stack_slot_is_not_lr_proof(self):
        m=self.callee();at=a.CALLEE_ENTRY+8
        m[at]=a.Ins(at,'pop','{r2}')
        with self.assertRaisesRegex(a.UnsafeCFG,'LR provenance'):
            a.callee_r7_all_returns(m,a.CALLEE_ENTRY)

    def test_40_pop_saved_lr_then_clobber_r1_is_not_return_proof(self):
        m=self.callee()
        at=a.CALLEE_ENTRY+10
        m[at]=a.Ins(at,'mov','r1, #0')
        m[at+2]=a.Ins(at+2,'bx','r1')
        with self.assertRaisesRegex(a.UnsafeCFG,'LR provenance'):
            a.callee_r7_all_returns(m,a.CALLEE_ENTRY)

    def test_41_sp_arithmetic_not_modeled_and_rejected(self):
        m=self.callee();m[a.CALLEE_ENTRY+2]=a.Ins(a.CALLEE_ENTRY+2,'sub','sp, #4')
        with self.assertRaisesRegex(a.UnsafeCFG,'SP/stack'):
            a.callee_r7_all_returns(m,a.CALLEE_ENTRY)

    def test_42_nested_bl_requires_more_proof(self):
        m=self.callee();m[a.CALLEE_ENTRY+2]=a.Ins(a.CALLEE_ENTRY+2,'bl','0x000e1000',4)
        with self.assertRaisesRegex(a.UnsafeCFG,'nested callee BL'):
            a.callee_r7_all_returns(m,a.CALLEE_ENTRY)

    def test_43_pop_pc_is_not_unchecked_return(self):
        m=self.callee();m[a.CALLEE_ENTRY+8]=a.Ins(a.CALLEE_ENTRY+8,'pop','{pc}')
        with self.assertRaisesRegex(a.UnsafeCFG,'POP into PC'):
            a.callee_r7_all_returns(m,a.CALLEE_ENTRY)


class BranchTargets(unittest.TestCase):
    def test_26_thumb16_unconditional_target(self):
        src=0x65EA0;dest=a.HOOK;delta=(dest-(src+4))//2
        self.assertEqual(a.thumb16_branch_target(0xE000|delta,src),dest)

    def test_27_thumb16_conditional_target(self):
        self.assertEqual(a.thumb16_branch_target(0xD001,0x200),0x206)

    def test_28_thumb16_negative_displacement(self):
        self.assertEqual(a.thumb16_branch_target(0xE7FD,0x200),0x1FE)

    def test_29_thumb_bl_forward_and_back(self):
        for diff in (0,2,0x7fe,-2,-0x800,0x10000,-0x10000):
            src=0x20000;dest=src+4+diff
            raw=diff & ((1<<23)-1)
            h1=0xF000|((raw>>12)&0x7ff)
            h2=0xF800|((raw>>1)&0x7ff)
            self.assertEqual(a.thumb_bl_target(h1,h2,src),dest)

    def test_30_raw_branch_scan_detects_entry_and_middle(self):
        start=a.HOOK-0x30
        buff=bytearray(b'\x00'*0x30)
        for loc,target in [(0,a.HOOK),(4,0x65EDA)]:
            src=start+loc;delta=(target-(src+4))//2
            buff[loc:loc+2]=(0xE000|delta).to_bytes(2,'little')
        found=a.raw_incoming_hits(bytes(buff),start,{a.HOOK}|a.MIDDLE)
        self.assertIn((start,a.HOOK,'thumb16-raw'),found)
        self.assertIn((start+4,0x65EDA,'thumb16-raw'),found)

    def test_31_direct_cfg_branch_scan_detects_hook_entry(self):
        ins={0x100:a.Ins(0x100,'b',hex(a.HOOK)),0x102:a.Ins(0x102,'beq',hex(0x65EDC))}
        found=a.direct_cfg_incoming(ins,{a.HOOK}|a.MIDDLE)
        self.assertEqual([(x,y) for x,y,_ in found],[(0x100,a.HOOK),(0x102,0x65EDC)])

    def test_31b_hook_entry_is_fail_closed_without_register_provenance(self):
        with self.assertRaisesRegex(a.UnsafeCFG,'r4/r6 provenance unproved'):
            a.require_no_unvetted_hook_branches([(0x65E10,a.HOOK,'b')])

    def test_31c_branch_to_veneer_middle_is_fail_closed(self):
        with self.assertRaisesRegex(a.UnsafeCFG,'veneer middle'):
            a.require_no_unvetted_hook_branches([(0x65E10,0x65EDC,'beq')])

    def test_31d_hook_fallthrough_is_not_direct_branch(self):
        a.require_no_unvetted_hook_branches([])

    def test_32_indirect_branch_is_not_mistaken_for_direct(self):
        with self.assertRaisesRegex(a.UnsafeCFG,'caller exits before defining r7'):
            a.predef_caller({a.CALLER_RESUME:a.Ins(a.CALLER_RESUME,'bx','r4')})

    def test_33_bad_instruction_branch_target_fails(self):
        with self.assertRaises(a.UnsafeCFG):
            a.edges(a.Ins(0x100,'beq','r5'))


class CFGEndToEnd(unittest.TestCase):
    def fixture(self):
        b=a.CALLER_RESUME; c=a.CALLEE_ENTRY
        caller={b:a.Ins(b,'ldr','r2, [pc, #12]'),
                b+2:a.Ins(b+2,'add','r3, pc, #4'),
                b+4:a.Ins(b+4,'bl','0x000e0748',4),
                b+8:a.Ins(b+8,'beq',hex(b+14)),
                b+10:a.Ins(b+10,'mov','r7, r11'),
                b+14:a.Ins(b+14,'mov','r7, r11')}
        callee={c:a.Ins(c,'push','{r4,r7,lr}'),
                c+2:a.Ins(c+2,'mov','r7, r11'),
                c+4:a.Ins(c+4,'pop','{r4,r7}'),
                c+6:a.Ins(c+6,'pop','{r1}'),
                c+8:a.Ins(c+8,'bx','r1')}
        return caller,callee

    def test_44_literal_ldr_and_pc_add_are_not_jumps(self):
        for op,args in [('ldr','r0, [pc, #12]'), ('add','r0, pc, #8'),
                        ('adds','r2, pc, #4'), ('adr','r0, pc, #0')]:
            with self.subTest(op=op,args=args):
                self.assertEqual(a.edges(a.Ins(0x100,op,args)),([0x102],False))

    def test_45_real_pc_write_is_still_rejected(self):
        with self.assertRaisesRegex(a.UnsafeCFG,'write to PC'):
            a.edges(a.Ins(0x100,'ldr','pc, [r0]'))

    def test_46_complete_synthetic_pipeline_succeeds(self):
        caller,callee=self.fixture()
        result=a.analyze_bounded_fixture(caller,callee,b'\x00'*0x100)
        self.assertEqual(result['branches'],{'parsed_direct_count':0,'raw_candidate_count':0})
        self.assertEqual(result['calls'],[a.CALLER_RESUME+4])
        self.assertEqual(result['callee']['return_addresses'],[a.CALLEE_ENTRY+8])
        self.assertEqual(len(result['visited_digest']),64)

    def test_47_pipeline_rejects_raw_unconditional_hook_entry(self):
        caller,callee=self.fixture()
        start=a.HOOK-0x20;delta=(a.HOOK-(start+4))//2
        buf=bytearray(b'\x00'*0x20);buf[0:2]=(0xe000|delta).to_bytes(2,'little')
        with self.assertRaisesRegex(a.UnsafeCFG,'directly enters hook'):
            a.analyze_bounded_fixture(caller,callee,bytes(buf),start)

    def test_48_pipeline_rejects_raw_conditional_veneer_middle(self):
        caller,callee=self.fixture()
        start=a.HOOK-0x20;delta=(0x65EDC-(start+4))//2
        buf=bytearray(b'\x00'*0x20);buf[0:2]=(0xd000|(delta & 0xff)).to_bytes(2,'little')
        with self.assertRaisesRegex(a.UnsafeCFG,'veneer middle'):
            a.analyze_bounded_fixture(caller,callee,bytes(buf),start)

    def test_49_pipeline_rejects_raw_BL_veneer_entry(self):
        caller,callee=self.fixture()
        start=a.HOOK-0x60;diff=a.HOOK-(start+4)
        raw=diff&((1<<23)-1)
        hi=0xf000|((raw>>12)&0x7ff);lo=0xf800|((raw>>1)&0x7ff)
        buf=bytearray(b'\x00'*0x60);buf[0:4]=hi.to_bytes(2,'little')+lo.to_bytes(2,'little')
        with self.assertRaisesRegex(a.UnsafeCFG,'directly enters hook'):
            a.analyze_bounded_fixture(caller,callee,bytes(buf),start)

    def test_50_pipeline_rejects_parsed_hook_entry_even_with_safe_raw(self):
        caller,callee=self.fixture()
        caller[a.CALLER_RESUME+8]=a.Ins(a.CALLER_RESUME+8,'beq',hex(a.HOOK))
        with self.assertRaises(a.UnsafeCFG):
            a.analyze_bounded_fixture(caller,callee,b'\x00'*0x100)

    def test_51_full_window_bound_covers_visited_list_beyond_f60(self):
        # Synthetic values only: no ROM read. 0x65FDE was present in the
        # previously reported 66-address metadata and outside old 0x65F60.
        self.assertTrue(0x65FDE<0x66000)
        self.assertFalse(0x65FDE<0x65F60)
        import inspect
        self.assertIn('CALLER_ENTRY,0x66000',inspect.getsource(a.private_rom_analysis))

    def test_51a_synthetic_disassembler_decodes_beyond_old_window(self):
        # Manufacture an all-synthetic byte buffer and disassemble the
        # full corrected window; no protected game data is loaded.
        with tempfile.TemporaryDirectory() as d:
            blob=bytearray(b'\x00'*0x66000)
            blob[0x65FDE:0x65FE0]=bytes.fromhex('7047') # BX LR
            decoded=a.disassemble_thumb_private(bytes(blob),a.CALLER_ENTRY,
                                                   0x66000,'clang','llvm-objdump',Path(d))
            self.assertIn(0x65FDE,decoded)
            self.assertEqual(decoded[0x65FDE].op,'bx')

    def test_51b_synthetic_thumb_decode_pipeline_handles_literal_and_bl(self):
        with tempfile.TemporaryDirectory() as d:
            data=bytes.fromhex('0048 01a1 00f000f8 7047')
            decoded=a.disassemble_thumb_private(data,0,len(data),'clang','llvm-objdump',Path(d))
            self.assertEqual(decoded[0].op,'ldr')
            self.assertEqual(a.edges(decoded[0]),([2],False))
            self.assertIn(decoded[2].op,('adr','add'))
            self.assertEqual(a.edges(decoded[2]),([4],False))
            self.assertEqual(decoded[4].op,'bl')
            self.assertEqual(a.edges(decoded[4]),([8],False))

    def test_52_public_address_metadata_digest_is_reproducible(self):
        import json,hashlib
        packet=json.loads((HERE/'R4_R7_VISITED_ADDRESSES_ONLY.json').read_text())
        addrs={int(x,16)-0x08000000 for x in packet['visited_original_guest_addresses']}
        self.assertEqual(len(addrs),66)
        digest=a.visited_address_sha256(addrs)
        self.assertEqual(digest,a.visited_address_sha256(set(reversed(sorted(addrs)))))
        self.assertEqual(len(digest),64)

    def test_53_raw_candidate_gate_is_not_warning_only(self):
        import inspect
        body=inspect.getsource(a.private_rom_analysis)
        self.assertIn('hook_entry_gate(caller,rom,0)',body)
        self.assertNotIn('WARNING: unclassified whole-ROM',body)


class LayoutProvenance(unittest.TestCase):
    def test_34_layout_projection_contains_required_source_patterns(self):
        # The full public header audit runs separately via --source-zip.
        dump=(HERE/'armv4t_header_projection_dump.txt').read_text()
        for pattern in ('88:7-7 |     u32 torment','98:0-0 |     u32 imprison',
                        '109:3-12 |     u32 disabledMove','110:5-14 |     u32 encoredMove',
                        '364 |   u16[4] choicedMove','[sizeof=152, align=4]'):
            self.assertIn(pattern,dump)

    def test_35_critical_approved_source_is_preserved(self):
        self.assertEqual(b.SOURCE.read_bytes(),a.Path(__file__).with_name('player_taunt_recovery_choice_gorilla_r4.s').read_bytes())


if __name__=='__main__': unittest.main(verbosity=2)
