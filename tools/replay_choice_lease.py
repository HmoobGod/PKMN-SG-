"""Replay old actor-0 request observations without mistaking entry for a copy.

The archived observer breaks at 0x0806B370, before the non-link/direction
branches and byte-copy loop. Hence it cannot certify post-copy delivery,
even when a later native response/consumer was observed. Zero leases open.
"""
import argparse
import ctypes as C
import json
import subprocess
import tempfile
from pathlib import Path
from validate_choice_lifecycle import validate

ROOT = Path(__file__).resolve().parents[1]
ENTRY_PC = '0x806b370'


class Lease(C.Structure):
    _fields_ = [('epoch', C.c_uint64), ('state', C.c_int), ('actor', C.c_uint8)]


def replay(lib, report):
    ledger = validate(report)
    lease = Lease()
    lib.sg_lease_init(C.byref(lease))
    attempts = 0
    for event in report['events']:
        if (event['event'] == 'copy' and event.get('direction') == 0
                and event.get('header', [None])[0] == 19):
            if event.get('pc') != ENTRY_PC:
                raise ValueError('unrecognized/missing historical copy-entry PC')
            attempts += 1
            # At entry the actual original copy has NOT been witnessed.
            opened = lib.sg_lease_on_buffer_a_copy(
                C.byref(lease), 0, 19, 44, False)
            if opened or lease.state != 0:
                raise AssertionError('entry-only observation opened a lease')
    if attempts != len(report['epochs']) - 1 or attempts != ledger['observed_copies']:
        raise AssertionError('request-entry provenance/count mismatch')
    return {
        'seeded_before_observer': 1,
        'copier_entry_attempts': attempts,
        'native_reply_lifetimes_in_prior_log': sum(
            bool(e['completion']) for e in report['epochs']),
        'post_copy_executions_observed': 0,
        'certified_copy_witnesses': 0,
        'opened_leases': 0,
        'automatic_dispatch': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports', type=Path, help='local read-only historic JSON')
    args = parser.parse_args()
    obj = json.loads(args.reports.read_text(encoding='utf-8'))
    reports = [entry['report'] for entry in obj['reports']] if 'reports' in obj else [obj]
    with tempfile.TemporaryDirectory() as tmp:
        shared = Path(tmp) / 'libchoice_lease.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-std=c11', '-O2',
                        '-Wall', '-Wextra', '-Werror',
                        '-I' + str(ROOT / 'research'),
                        str(ROOT / 'research' / 'sg_choice_lease.c'),
                        '-o', str(shared)], check=True)
        lib = C.CDLL(str(shared))
        lib.sg_lease_init.argtypes = [C.POINTER(Lease)]
        lib.sg_lease_on_buffer_a_copy.argtypes = [
            C.POINTER(Lease), C.c_uint32, C.c_uint32, C.c_uint32, C.c_bool]
        lib.sg_lease_on_buffer_a_copy.restype = C.c_bool
        total_attempts = total_replies = 0
        for report in reports:
            result = replay(lib, report)
            total_attempts += result['copier_entry_attempts']
            total_replies += result['native_reply_lifetimes_in_prior_log']
            print('PASS', report.get('case', 'historic report'), result)
        print('TOTAL', len(reports), 'reports:', total_attempts,
              'copier entries,', total_replies,
              'native reply lifetimes; ZERO copy witnesses and leases')


if __name__ == '__main__':
    main()
