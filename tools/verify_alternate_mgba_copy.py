"""Read-only consistency validator for a single manually driven R7 mGBA trace.

Not a native ownership/legality certificate, emulator authenticity attestation,
or permission for automatic move submission. Returns PASS only for a bounded,
fully coherent *reported observation*, not proof no debugger tampering occurred.
"""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED = {
    'rom_sha256': '6be1201f7c492d2621a3b8f88aac3acbcd07231457da3f78fd2f1224e879a6de',
    'save_sha256': '8c6cb520de6dc475e5fde31cb78ddd49ceb6add89f5c208598977886fa5579a4',
    'savestate_sha256': '0dbcb91a26a3825357f14c18800708a28ef371db57e8fe907ecfbb9dc2c1c7ef',
    'original_host_sha256': '4304688a0b44007cca23c9e887af17c44530fd602ee3d1e57a232da397bec769',
    'patched_host_sha256': 'fef5effac26b13f53afe88511990fdf3049184402ca50faf9325d4daed7869c7',
}
FIELDS = ('source_before_hex', 'source_after_hex', 'destination_after_hex',
          'store_values_hex')


def verify(report):
    def must(condition, reason):
        if not condition:
            raise ValueError(reason)
    must(type(report) is dict, 'expected an object')
    for key, val in EXPECTED.items():
        must(report.get(key) == val, f'unpinned input: {key}')
    for key, val in [
            ('schema', 'sg16266-alt-mgba-observer-v1'),
            ('case', 'manual_confirm_then_next_actor0_move_request'),
            ('cpu_thumb_prefetch_refreshed', True),
            ('prefetch_before', ['0x20', '0xf000']),
            ('prefetch_after', ['0x4b00', '0x4718']),
            ('human_confirm_frame', 14246),
            ('human_confirm_original_payload', 257),
            ('entry_frame', 14369), ('post_frame', 14369),
            ('actor', 0), ('direction', 0), ('length', 44),
            ('entry_pc', '0x0806b370'), ('store_pc', '0x0806b3be'),
            ('post_pc', '0x0806b3c6'),
            ('source_address', 0x0201CF14),
            ('destination_address', 0x0201BF14),
            ('entry_sp', 0x03007D3C), ('post_sp', 0x03007D34),
            ('entry_lr', 0x0806BB13), ('post_lr', 0x0806BB13),
            ('pending_at_copy_entry', 0), ('pending_at_post_copy', 0),
            ('opcode_at_post_copy', 19),
            ('pending_set_after_post_guest_steps', 23),
            ('pending_transition_pc', '0x80d4ca4'),
            ('pending_transition_frame', 14369),
            ('pending_word_after_transition', 1),
            ('pending_request_opcode_after_transition', 19),
            ('native_auto_moves', 0),
            ('native_automatic_battle_acceptance', 0),
            ('user_ownership_certified', False),
            ('move_and_target_legality_certified', False),
            ('real_mobile_gameplay_certified', False)]:
        must(type(report.get(key)) is type(val) and report[key] == val,
             f'required fixture invariant: {key}')
    must(report.get('savestate_version_warning') ==
         'emulator reported warning; acknowledged, not cleared',
         'lost savestate caveat')
    must(type(report.get('store_indices')) is list and
         report['store_indices'] == list(range(44)), 'wrong store order/count')
    raws = []
    for key in FIELDS:
        s = report.get(key)
        must(type(s) is str and len(s) == 88, f'invalid 44-byte hex in {key}')
        try:
            raw = bytes.fromhex(s)
        except ValueError as exc:
            raise ValueError(f'invalid hex: {key}') from exc
        must(len(raw) == 44, f'invalid byte count: {key}')
        raws.append(raw)
    must(all(raw == raws[0] for raw in raws), 'source/store/destination differ')
    must(raws[0][0] == 19, 'not a move-choice request')
    return {'status': 'PASS: observation consistency only',
            'copy_bytes': 44, 'original_stores': 44,
            'request_bytes_sha256': hashlib.sha256(raws[0]).hexdigest(),
            'runtime_copy_witnesses_on_one_fixture': 1,
            'automatic_moves_authorized': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', type=Path)
    args = p.parse_args()
    result = verify(json.loads(args.report.read_text()))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()