"""Old copier-entry reports must never authorize the R4 reference lease."""
import copy
import ctypes as C
import subprocess
import tempfile
import unittest
from pathlib import Path
from replay_choice_lease import Lease, replay
from test_choice_protocol import make_report

ROOT = Path(__file__).resolve().parents[1]


class EntryOnlyReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        so = Path(cls.temp.name) / 'lease.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-std=c11', '-O2',
                        '-Wall', '-Wextra', '-Werror',
                        '-I' + str(ROOT / 'research'),
                        str(ROOT / 'research' / 'sg_choice_lease.c'),
                        '-o', str(so)], check=True, capture_output=True)
        cls.lib = C.CDLL(str(so))
        cls.lib.sg_lease_init.argtypes = [C.POINTER(Lease)]
        cls.lib.sg_lease_on_buffer_a_copy.argtypes = [
            C.POINTER(Lease), C.c_uint32, C.c_uint32, C.c_uint32, C.c_bool]
        cls.lib.sg_lease_on_buffer_a_copy.restype = C.c_bool

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def sample(self):
        report = make_report(('rejected', 'accepted'), duplicate_hash=True)
        for e in report['events']:
            if e['event'] == 'copy' and e.get('direction') == 0:
                e['pc'] = '0x806b370'
        return report

    def test_identical_contents_never_open_leases(self):
        r = self.sample()
        self.assertEqual(len({e['request_sha256'] for e in r['epochs']}), 1)
        result = replay(self.lib, r)
        self.assertEqual(result['copier_entry_attempts'], 2)
        self.assertEqual(result['native_reply_lifetimes_in_prior_log'], 2)
        self.assertEqual(result['certified_copy_witnesses'], 0)
        self.assertEqual(result['opened_leases'], 0)

    def test_wrong_pc_denied(self):
        r = self.sample()
        next(e for e in r['events'] if e.get('pc') == '0x806b370')['pc'] = '0x806b3c6'
        with self.assertRaises(ValueError):
            replay(self.lib, r)

    def test_missing_pc_denied(self):
        r = self.sample()
        next(e for e in r['events'] if e.get('pc') == '0x806b370').pop('pc')
        with self.assertRaises(ValueError):
            replay(self.lib, r)

    def test_bad_order_denied(self):
        r = self.sample()
        r['events'] = r['events'][1:]
        with self.assertRaises(ValueError):
            replay(self.lib, r)

    def test_no_report_mutation(self):
        r = self.sample()
        baseline = copy.deepcopy(r)
        replay(self.lib, r)
        self.assertEqual(r, baseline)


if __name__ == '__main__':
    unittest.main(verbosity=2)
