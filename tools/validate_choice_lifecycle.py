"""Fail-closed offline checks for the 16266 actor-0 request-observer JSON.

This is a trace-consistency checker, NOT a ROM adapter or a permission oracle.
It never opens game files, replays instructions, or submits a battle command.
"""
import argparse
import json
from pathlib import Path


class ProtocolViolation(ValueError):
    """The claimed lifecycle cannot be justified by the supplied observation."""


def require(condition, message):
    if not condition:
        raise ProtocolViolation(message)


def validate(report):
    """Check an actor-0 *observer report* against its event-indexed epoch ledger.

    In particular, *identical* request hashes are intentionally allowed across
    different observed copies. A host epoch ID is not a native ownership token.
    """
    require(isinstance(report, dict), 'report must be an object')
    require(report.get('host_epoch_ids_only') is True, 'host ID provenance required')
    require(report.get('automatic_dispatch') is False, 'must not claim automatic dispatch')
    epochs, events = report.get('epochs'), report.get('events')
    require(isinstance(epochs, list) and epochs, 'missing epochs')
    require(isinstance(events, list), 'missing event list')
    require(len(epochs) <= 100000 and len(events) <= 1000000, 'implausible report size')
    for i, epoch in enumerate(epochs):
        require(isinstance(epoch, dict) and type(epoch.get('id')) is int and epoch['id'] == i,
                'epoch IDs must be consecutive host observation counters')
        require(epoch.get('request_bytes') == 44, f'epoch {i}: unexpected request size')
        digest = epoch.get('request_sha256')
        require(isinstance(digest, str) and len(digest) == 64 and
                all(c in '0123456789abcdef' for c in digest), f'epoch {i}: invalid hash')
        require(epoch.get('origin') == ('seeded request in saved hook state' if i == 0 else 'observed native buffer-A copy'),
                f'epoch {i}: origin mismatch')
        for key in ('emit', 'reply', 'completion', 'validation', 'commits'):
            require(isinstance(epoch.get(key), list), f'epoch {i}: missing {key} ledger')

    # Check a strict event order; source hashes, pointer equality and pending bits
    # are observations, not proof that a choice belongs to the player.
    ledger = {i: {k: [] for k in ('emit', 'reply', 'completion', 'validation', 'commits')}
              for i in range(len(epochs))}
    states = ['unseen'] * len(epochs)
    states[0] = 'open'  # Initial buffer-A enqueue occurred before attached state.
    active = 0
    observed_copy = 0
    payload = {}
    for ordinal, event in enumerate(events):
        require(isinstance(event, dict), f'event {ordinal}: not an object')
        kind = event.get('event')
        require(kind in ('copy', 'emit', 'completion', 'validation',
                         'slot_commit', 'move_commit', 'target_commit'),
                f'event {ordinal}: unexpected event kind')
        indexed = event.get('epoch')
        if kind == 'copy' and indexed is None:
            # The existing observer also logs actor-0 copies not used as move requests.
            require(event.get('direction') == 0, f'event {ordinal}: unattributed reply')
            header = event.get('header')
            require(isinstance(header, list) and len(header) >= 1 and header[0] != 19,
                    f'event {ordinal}: unattributed move request')
            continue
        require(type(indexed) is int and 0 <= indexed < len(epochs),
                f'event {ordinal}: unknown epoch')
        if kind == 'copy' and event.get('direction') == 0:
            require(indexed == observed_copy + 1, f'event {ordinal}: skipped/duplicate request')
            require(active is None, f'event {ordinal}: overlap with uncompleted reply')
            require(states[indexed - 1] in ('accepted', 'rejected', 'cancelled'),
                    f'event {ordinal}: previous request not closed by consumer')
            header = event.get('header')
            require(event.get('size') == 44 and isinstance(header, list) and len(header) >= 1 and header[0] == 19,
                    f'event {ordinal}: malformed move request')
            require(states[indexed] == 'unseen', f'event {ordinal}: replayed request')
            states[indexed] = 'open'
            active = indexed
            observed_copy += 1
            continue
        require(indexed <= observed_copy, f'event {ordinal}: event before request copy')
        state = states[indexed]
        if kind == 'emit':
            require(active == indexed and state == 'open', f'event {ordinal}: stale/duplicate emitter')
            context = event.get('context')
            require(isinstance(context, dict), f'event {ordinal}: missing context')
            require(type(context.get('pending')) is int and (context['pending'] & 1) != 0 and
                    context.get('opcode') == 19,
                    f'event {ordinal}: no actor-0 move request at emission')
            value = event.get('payload')
            require(type(value) is int and 0 <= value <= 0xffffffff,
                    f'event {ordinal}: invalid payload')
            payload[indexed] = value
            states[indexed] = 'emitted'
            ledger[indexed]['emit'].append(event)
        elif kind == 'copy':
            require(event.get('direction') == 1 and event.get('size') == 6,
                    f'event {ordinal}: response direction/size mismatch')
            header = event.get('header')
            require(isinstance(header, list) and len(header) == 6 and
                    all(type(b) is int and 0 <= b <= 255 for b in header),
                    f'event {ordinal}: malformed response bytes')
            require(header[:2] == [32, 10] and int.from_bytes(bytes(header[2:]), 'little') == payload.get(indexed),
                    f'event {ordinal}: reply opcode/payload mismatch')
            require(active == indexed and state == 'emitted',
                    f'event {ordinal}: stale/duplicate reply')
            states[indexed] = 'replied'
            ledger[indexed]['reply'].append(event)
        elif kind == 'completion':
            context = event.get('context')
            require(isinstance(context, dict), f'event {ordinal}: missing context')
            require(active == indexed and state == 'replied',
                    f'event {ordinal}: premature/duplicate completion')
            require(type(context.get('pending')) is int and not (context['pending'] & 1) and
                    context.get('run') == '0x80619d5',
                    f'event {ordinal}: callback/pending completion mismatch')
            states[indexed] = 'cancelled' if payload[indexed] == 0xffff else 'completed'
            active = None
            ledger[indexed]['completion'].append(event)
        elif kind == 'validation':
            require(state == 'completed', f'event {ordinal}: validation without completed non-cancel reply')
            require(event.get('result') in (0, 1) and type(event['result']) is int,
                    f'event {ordinal}: unobserved validation outcome')
            states[indexed] = 'committing' if event['result'] == 0 else 'rejected'
            ledger[indexed]['validation'].append(event)
        else:
            expected = {'slot_commit': ('committing', 'slot'),
                        'move_commit': ('slot', 'move'),
                        'target_commit': ('move', 'accepted')}
            before, after = expected[kind]
            require(state == before, f'event {ordinal}: missing/out-of-order native commit')
            states[indexed] = after
            ledger[indexed]['commits'].append(event)

    require(observed_copy == len(epochs) - 1, 'unobserved or duplicated epoch copies')
    require(active == len(epochs) - 1 and states[-1] == 'open',
            'expected final new request waiting for manual input')
    require(report.get('active_epoch_at_end') == active, 'terminal active ID mismatch')
    for i, epoch in enumerate(epochs):
        require(states[i] in ('accepted', 'rejected', 'cancelled') if i != len(epochs) - 1
                else states[i] == 'open', f'epoch {i}: incomplete/overlapping lifecycle')
        for key in ledger[i]:
            require(epoch[key] == ledger[i][key], f'epoch {i}: {key} ledger and event stream disagree')
    return {'epochs': len(epochs), 'observed_copies': observed_copy,
            'accepted': states.count('accepted'), 'rejected': states.count('rejected'),
            'cancelled': states.count('cancelled'), 'open': states.count('open')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports', nargs='+', type=Path,
                        help='private observer JSON; read locally, never uploaded')
    args = parser.parse_args()
    for path in args.reports:
        summary = validate(json.loads(path.read_text(encoding='utf-8')))
        print(f'PASS {path.name}: {summary}')


if __name__ == '__main__':
    main()
