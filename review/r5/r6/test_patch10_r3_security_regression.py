"""R3 adversarial review regressions, generated junk bytes only.

These tests use repeated synthetic patterns, not real ROM, save, or CPU data.
"""
import base64
import io
import unittest
from unittest.mock import patch
import zipfile
from patch10_private_artifact_boundary import inspect_zip


def archive(payload, *, compression=zipfile.ZIP_STORED):
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, 'w', compression=compression) as z:
            z.writestr('safe.txt', payload)
        return buffer.getvalue()


class SecurityR3(unittest.TestCase):
    def deny(self, text, *, compression=zipfile.ZIP_STORED):
        with self.assertRaises(ValueError):
            inspect_zip(archive(text, compression=compression))

    def test_mime_wrapped_standard_and_urlsafe_base64(self):
        # Fresh synthetic bytes, deliberately not private game data.
        fake = (b'\xfb\xef\xfa\x81\x00\xee' * 1500)
        enc = base64.b64encode(fake)
        mime = b'\n'.join(enc[i:i+76] for i in range(0, len(enc), 76))
        self.deny(mime)
        url = base64.urlsafe_b64encode(fake)
        self.deny(url)
        url_wrapped = b'\n'.join(url[i:i+76] for i in range(0, len(url), 76))
        self.deny(url_wrapped)

    def test_hex_dump_and_wrapped_xxd_forms(self):
        data = bytes(range(16)) * 130
        h = data.hex().encode('ascii')
        self.deny(b'\n'.join(h[i:i+64] for i in range(0, len(h), 64)))
        spaced = b'\n'.join(b' '.join(f'{b:02x}'.encode() for b in data[i:i+16])
                            for i in range(0, len(data), 16))
        self.deny(spaced)
        hexdump = b'\n'.join((f'{offset:08x}  '.encode() +
                              b' '.join(f'{b:02x}'.encode() for b in data[offset:offset+16]) +
                              b'  |................|')
                             for offset in range(0, len(data), 16))
        self.deny(hexdump)
        xxd = b'\n'.join((f'{offset:08x}: '.encode() +
                          b' '.join(f'{b:02x}'.encode() for b in data[offset:offset+16]))
                         for offset in range(0, len(data), 16))
        self.deny(xxd)

    def test_uppercase_hex_prefix_with_comma_or_whitespace(self):
        self.deny('const byte a[] = { ' + '0X10, ' * 200 + ' };')
        self.deny('const byte a[] = { ' + '0x10 ' * 200 + ' };')
        self.deny('const byte a[] = { ' + '0X10\n' * 200 + ' };')

    def test_decimal_byte_array_and_split_fromhex(self):
        self.deny('unsigned char a[]={ ' + '255,' * 2000 + '};')
        pieces = ['01' * 64] * 20
        self.deny('x = bytes.fromhex(\n' + '\n'.join('"'+p+'"' for p in pieces) + '\n)')

    def test_bell_control_byte_is_independently_pinned(self):
        self.deny(b'print("safe")\n\x07end')

    def test_compression_ratio_guard_independent_from_content_classifier(self):
        bomb = archive(b'A' * 100000, compression=zipfile.ZIP_DEFLATED)
        with patch('patch10_private_artifact_boundary._check_source_content', return_value=True):
            with self.assertRaisesRegex(ValueError, 'compression ratio'):
                inspect_zip(bomb)

    def test_simple_public_source_is_allowed(self):
        self.assertTrue(inspect_zip(archive(b'print("public synthetic test")\n')))


if __name__ == '__main__':
    unittest.main()
