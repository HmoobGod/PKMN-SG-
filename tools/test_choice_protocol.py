"""Synthetic adversarial protocol tests; no commercial bytes or saved states."""
import copy
import hashlib
import unittest

from validate_choice_lifecycle import ProtocolViolation, validate


def make_report(outcomes=('accepted', 'accepted'), duplicate_hash=False):
    """Construct distinct request copies with deliberately reusable content."""
    epochs = []
    events = []
    for i in range(len(outcomes) + 1):
        h = hashlib.sha256((str(0 if duplicate_hash else i) + ':synthetic').encode()).hexdigest()
        epoch = dict(id=i, origin='seeded request in saved hook state' if i == 0
                     else 'observed native buffer-A copy', request_bytes=44,
                     request_sha256=h, emit=[], reply=[], completion=[], validation=[], commits=[])
        epochs.append(epoch)
        if i:
            events.append(dict(event='copy', epoch=i, direction=0, size=44, header=[19, 0, 0, 0, 0, 0]))
        if i == len(outcomes):
            break
        result = outcomes[i]
        payload = 0xffff if result == 'cancelled' else (i + 1) | (1 << 8)
        emit = dict(event='emit', epoch=i, payload=payload, context=dict(pending=3, opcode=19))
        reply = dict(event='copy', epoch=i, direction=1, size=6,
                     header=[32, 10, *payload.to_bytes(4, 'little')])
        done = dict(event='completion', epoch=i, context=dict(pending=2, run='0x80619d5'))
        for key, event in (('emit', emit), ('reply', reply), ('completion', done)):
            epoch[key].append(event)
            events.append(event)
        if result != 'cancelled':
            check = dict(event='validation', epoch=i, result=0 if result == 'accepted' else 1)
            epoch['validation'].append(check)
            events.append(check)
            if result == 'accepted':
                for kind in ['slot_commit', 'move_commit', 'target_commit']:
                    event = dict(event=kind, epoch=i)
                    epoch['commits'].append(event)
                    events.append(event)
    return dict(host_epoch_ids_only=True, automatic_dispatch=False,
                active_epoch_at_end=len(epochs)-1, epochs=epochs, events=events)


class TestProtocol(unittest.TestCase):
    def test_accepted_rejected_cancelled(self):
        for results in [('accepted',), ('rejected', 'accepted'),
                        ('cancelled', 'accepted'), ('accepted', 'rejected', 'cancelled')]:
            with self.subTest(results=results):
                result = validate(make_report(results))
                self.assertEqual(result['accepted'], results.count('accepted'))

    def test_repeat_request_bytes_is_not_a_freshness_token(self):
        result = make_report(('rejected', 'accepted'), duplicate_hash=True)
        self.assertEqual(len({x['request_sha256'] for x in result['epochs']}), 1)
        self.assertEqual(validate(result)['observed_copies'], 2)

    def assert_denied(self, mutate, description):
        report = make_report(('accepted', 'accepted'))
        mutate(report)
        with self.subTest(description=description), self.assertRaises(ProtocolViolation):
            validate(report)

    def test_fail_closed_mutations(self):
        cases = [
            ('no provenance', lambda r: r.pop('host_epoch_ids_only')),
            ('claims auto dispatch', lambda r: r.update(automatic_dispatch=True)),
            ('wrong active ID', lambda r: r.update(active_epoch_at_end=0)),
            ('skipped ID', lambda r: r['epochs'][2].update(id=3)),
            ('malformed hash', lambda r: r['epochs'][1].update(request_sha256='not a hash')),
            ('duplicate request', lambda r: r['events'].insert(7, copy.deepcopy(r['events'][7]))),
            ('unattributed opcode19', lambda r: r['events'].insert(1, dict(event='copy', direction=0, header=[19]))),
            ('request before completion', lambda r: r['events'].insert(1, copy.deepcopy(next(e for e in r['events'] if e.get('epoch') == 1 and e['event'] == 'copy' and e.get('direction') == 0)))),
            ('replayed emitter', lambda r: r['events'].insert(1, copy.deepcopy(r['events'][0]))),
            ('mismatched payload', lambda r: r['events'][1]['header'].__setitem__(2, 3)),
            ('missing reply', lambda r: r['events'].pop(1)),
            ('premature completion', lambda r: r['events'].insert(1, copy.deepcopy(r['events'][2]))),
            ('wrong reply direction', lambda r: r['events'][1].update(direction=0)),
            ('pending missing', lambda r: r['events'][0]['context'].update(pending=2)),
            ('wrong request opcode', lambda r: r['events'][0]['context'].update(opcode=18)),
            ('completion pending remains', lambda r: r['events'][2]['context'].update(pending=3)),
            ('wrong native callback', lambda r: r['events'][2]['context'].update(run='0x00000000')),
            ('validation before completion', lambda r: r['events'].insert(1, copy.deepcopy(r['events'][3]))),
            ('out of order commits', lambda r: r['events'].__setitem__(4, dict(event='target_commit', epoch=0))),
            ('duplicated commit', lambda r: r['events'].insert(6, copy.deepcopy(r['events'][6]))),
            ('fabricated epoch ledger', lambda r: r['epochs'][0]['commits'].clear()),
            ('missing observed copy', lambda r: r['events'].remove(next(e for e in r['events'] if e.get('epoch') == 1 and e['event'] == 'copy' and e.get('direction') == 0))),
            ('phantom missing terminal', lambda r: r['epochs'].pop()),
        ]
        for description, mutate in cases:
            self.assert_denied(mutate, description)

    def test_cancel_never_commits(self):
        report = make_report(('cancelled', 'accepted'))
        report['events'].insert(3, dict(event='slot_commit', epoch=0))
        with self.assertRaises(ProtocolViolation):
            validate(report)

    def test_rejection_never_commits(self):
        report = make_report(('rejected', 'accepted'))
        report['events'].insert(4, dict(event='slot_commit', epoch=0))
        with self.assertRaises(ProtocolViolation):
            validate(report)

    def test_input_report_unchanged(self):
        report = make_report(('accepted',))
        original = copy.deepcopy(report)
        validate(report)
        self.assertEqual(report, original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
