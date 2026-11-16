"""Conservative SOURCE-ONLY ZIP preflight. Never a proof of privacy.

A human must independently inspect every source file before a public upload.
This module uses only adversarial synthetic data. It never reads game files.
"""
from pathlib import PurePosixPath
import io
import re
import stat
import zipfile

FORBIDDEN_SUFFIX = {'.gba', '.sav', '.sgm', '.state', '.bin', '.jsonl',
                    '.rgba', '.png', '.jpg', '.jpeg', '.so', '.elf', '.map',
                    '.dmp', '.trace', '.log', '.nds', '.zip', '.7z', '.tar',
                    '.gz', '.cso', '.rom', '.dat'}
FORBIDDEN_BASENAMES = {'pokemon soulgold.gba', 'pokemon soulgold.sav', 'mgba-rom-test'}
ALLOWED_SUFFIX = {'.py', '.c', '.h', '.md', '.txt', '.patch', '.yml', '.yaml'}
MAX_SOURCE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 10 * 1024 * 1024
MAX_ENTRIES = 500

# Long unbroken encodings. Wrapped encodings are checked separately below.
_ESCAPED_BYTES = re.compile(rb'(?:\\[xX][0-9a-fA-F]{2}){128,}')
_BASE64_BLOB = re.compile(rb'(?<![A-Za-z0-9+/_-])[A-Za-z0-9+/_-]{4096,}={0,2}(?![A-Za-z0-9+/_-])')
_HEX_BLOB = re.compile(rb'(?<![0-9A-Fa-f])[0-9A-Fa-f]{8192,}(?![0-9A-Fa-f])')
_HEX_TOKENS = re.compile(rb'(?<![A-Za-z0-9_])0[xX][0-9a-fA-F]{2}(?![A-Za-z0-9_])')
_DECIMAL_ARRAY = re.compile(rb'(?:\b(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\b\s*,\s*){256,}')
_HEX_LINE = re.compile(rb'^\s*(?:[0-9a-fA-F]{2}\s*){8,}$')
_HEXDUMP_C = re.compile(rb'^\s*[0-9a-fA-F]{7,9}\s+(?:[0-9a-fA-F]{2}\s+){8,}', re.ASCII)
_XXD_LINE = re.compile(rb'^\s*[0-9a-fA-F]{7,9}:\s+(?:[0-9a-fA-F]{2}\s*){8,}', re.ASCII)
_B64_LINE = re.compile(rb'^[A-Za-z0-9+/_-]{64,}(?:={0,2})?$')
_FROMHEX = re.compile(rb'\b(?:bytes|bytearray)\s*\.\s*fromhex\s*\(([^)]{0,100000})\)', re.DOTALL)


def _valid_name(name):
    if type(name) is not str or not name or '\x00' in name or '\\' in name or '\r' in name or '\n' in name:
        raise ValueError('unsafe name')
    if name.startswith(('/', '//')) or ':' in name or name.endswith('/'):
        raise ValueError('absolute or non-file path')
    p = PurePosixPath(name)
    if str(p) != name or '..' in p.parts or p.is_absolute():
        raise ValueError('unsafe noncanonical path')
    for idx, part in enumerate(p.parts):
        if part in ('', '.', '..') or (part.startswith('.') and not (idx == 0 and part == '.github')):
            raise ValueError('hidden or ambiguous path')
    lower = p.name.lower()
    if lower in FORBIDDEN_BASENAMES:
        raise ValueError('private file name')
    if any(s in FORBIDDEN_SUFFIX for s in p.suffixes):
        raise ValueError('private artifact extension, including double extensions')
    if p.suffix.lower() not in ALLOWED_SUFFIX:
        raise ValueError('not source-only extension')
    if p.suffix.lower() in ('.yml', '.yaml') and p.parts[:2] != ('.github', 'workflows'):
        raise ValueError('workflow YAML only')
    if re.search(r'(?:^|[._-])(?:cpu[_-]?trace|memory[_-]?dump|save[_-]?dump|rom[_-]?dump|sav|gba|jsonl)(?:[._-]|$)', lower):
        raise ValueError('disguised game content filename')
    return p


def check_names(entries):
    total = 0
    seen = set()
    if not isinstance(entries, (list, tuple)) or not entries or len(entries) > MAX_ENTRIES:
        raise ValueError('empty or excessive entry count')
    for name, size, mode in entries:
        _valid_name(name)
        canonical = name.casefold()
        if canonical in seen:
            raise ValueError('duplicate or case-colliding path')
        seen.add(canonical)
        if type(size) is not int or not 0 <= size <= MAX_SOURCE_BYTES:
            raise ValueError('oversized file or invalid size')
        if type(mode) is not int or stat.S_IFMT(mode) == stat.S_IFLNK:
            raise ValueError('symlink/invalid mode')
        if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
            raise ValueError('nonregular entry')
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError('oversized archive')
    return True


def _has_large_wrapped_base64(data):
    # Require contiguous long base64-only lines; this catches MIME-wrapped
    # standard and URL-safe representations while avoiding prose joins.
    run = 0
    for line in data.splitlines():
        line = line.strip()
        if _B64_LINE.fullmatch(line):
            run += len(line.rstrip(b'='))
            if run >= 4096:
                return True
        else:
            run = 0
    return False


def _has_large_wrapped_hex(data):
    # Covers xxd -p, spaced hex, hexdump -C, and xxd address-prefixed lines.
    # Recognize actual dump-like runs, not arbitrary source containing digits.
    run_hex_digits = 0
    for line in data.splitlines():
        stripped = line.strip()
        if _HEXDUMP_C.match(stripped) or _XXD_LINE.match(stripped):
            # A standard dump line contains at least eight hex bytes.
            run_hex_digits += 16
        elif _HEX_LINE.fullmatch(stripped):
            run_hex_digits += len(re.findall(rb'[0-9a-fA-F]{2}', stripped)) * 2
        elif len(stripped) >= 32 and re.fullmatch(rb'[0-9a-fA-F]+', stripped):
            run_hex_digits += len(stripped)
        else:
            run_hex_digits = 0
        if run_hex_digits >= 2048:
            return True
    return False


def _has_large_fromhex(data):
    # Join literal string fragments and whitespace in fromhex("...") calls.
    for match in _FROMHEX.finditer(data):
        s = re.sub(rb'[\s\x22\x27]', b'', match.group(1))
        if len(s) >= 2048 and re.fullmatch(rb'[0-9a-fA-F]+', s):
            return True
    return False


def _check_source_content(name, data):
    if not data or b'\x00' in data:
        raise ValueError('binary or empty source')
    try:
        data.decode('utf-8', errors='strict')
    except UnicodeDecodeError:
        raise ValueError('non-UTF8 source') from None
    if any(c < 32 and c not in (9, 10, 13) for c in data):
        raise ValueError('embedded binary control bytes')
    if (_ESCAPED_BYTES.search(data) or _BASE64_BLOB.search(data) or
        _HEX_BLOB.search(data) or len(_HEX_TOKENS.findall(data)) >= 128 or
        _DECIMAL_ARRAY.search(data) or _has_large_wrapped_base64(data) or
        _has_large_wrapped_hex(data) or _has_large_fromhex(data)):
        raise ValueError('potential embedded game data; manual review required')
    return True


def inspect_zip(data):
    if not isinstance(data, bytes):
        raise ValueError('archive must be bytes')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos = z.infolist()
            files = [i for i in infos if not i.is_dir()]
            for i in infos:
                if i.is_dir():
                    dirname = i.filename.rstrip('/')
                    if (not dirname or dirname.startswith('/') or '\\' in dirname or
                            '..' in PurePosixPath(dirname).parts):
                        raise ValueError('unsafe archive directory')
            check_names([(i.filename, i.file_size, i.external_attr >> 16) for i in files])
            for i in files:
                if i.flag_bits & 1:
                    raise ValueError('encrypted entry')
                if i.file_size > 65536 and i.compress_size * 100 < i.file_size:
                    raise ValueError('excessive compression ratio')
                content = z.read(i)
                if len(content) != i.file_size:
                    raise ValueError('size mismatch')
                _check_source_content(i.filename, content)
    except (zipfile.BadZipFile, RuntimeError) as e:
        raise ValueError('unsafe or invalid ZIP') from e
    return True
