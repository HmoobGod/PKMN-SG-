"""Strict source-only archive preflight; not a privacy proof.

This intentionally fails closed. It does not absolve a human/independent reviewer
from checking all source text before uploading to a public repository.
No private ROMs, saves, CPU logs or exact-ROM data are required by this module.
"""
from pathlib import PurePosixPath
import io
import re
import stat
import zipfile

FORBIDDEN_SUFFIX={'.gba','.sav','.sgm','.state','.bin','.jsonl','.rgba','.png','.jpg','.jpeg','.so','.elf','.map','.dmp','.trace','.log','.nds','.zip','.7z','.tar','.gz','.cso','.rom','.dat'}
FORBIDDEN_BASENAMES={'pokemon soulgold.gba','pokemon soulgold.sav','mgba-rom-test'}
ALLOWED_SUFFIX={'.py','.c','.h','.md','.txt','.patch','.yml','.yaml'}
MAX_SOURCE_BYTES=1024*1024
MAX_TOTAL_BYTES=10*1024*1024
MAX_ENTRIES=500
# Deny pasted text encodings of large game data. Intentionally conservative:
# false positives are safer than leaking private bytes.
_HEX_DUMP=re.compile(rb'(?:0x[0-9a-fA-F]{2}\s*,\s*){128,}')
_ESCAPED_BYTES=re.compile(rb'(?:\\x[0-9a-fA-F]{2}){128,}')
_BASE64_BLOB=re.compile(rb'[A-Za-z0-9+/]{4096,}={0,2}')
_HEX_BLOB=re.compile(rb'(?<![0-9A-Fa-f])[0-9A-Fa-f]{8192,}(?![0-9A-Fa-f])')


def _valid_name(name):
    if type(name) is not str or not name or '\x00' in name or '\\' in name or '\r' in name or '\n' in name:
        raise ValueError('unsafe name')
    if name.startswith(('/', '//')) or ':' in name or name.endswith('/'):
        raise ValueError('absolute or non-file path')
    p=PurePosixPath(name)
    if str(p)!=name or '..' in p.parts or p.is_absolute():
        raise ValueError('unsafe noncanonical path')
    for idx,part in enumerate(p.parts):
        if part in ('','.','..') or part.startswith('.') and not(idx==0 and part=='.github'):
            raise ValueError('hidden or ambiguous path')
    lower=p.name.lower()
    if lower in FORBIDDEN_BASENAMES:
        raise ValueError('private file name')
    if any(s in FORBIDDEN_SUFFIX for s in p.suffixes):
        raise ValueError('private artifact extension, including double extensions')
    # The baseline is conservative: JSON is often raw captured state. Never
    # infer from a JSON extension that its content is synthetic.
    if p.suffix.lower() not in ALLOWED_SUFFIX:
        raise ValueError('not source-only extension')
    if p.suffix.lower() in ('.yml','.yaml') and p.parts[:2]!=('.github','workflows'):
        raise ValueError('workflow YAML only')
    if re.search(r'(?:^|[._-])(?:cpu[_-]?trace|memory[_-]?dump|save[_-]?dump|rom[_-]?dump|sav|gba|jsonl)(?:[._-]|$)',lower):
        raise ValueError('disguised game content filename')
    return p


def check_names(entries):
    total=0
    seen=set()
    if not isinstance(entries,(list,tuple)) or not entries or len(entries)>MAX_ENTRIES:
        raise ValueError('empty or excessive entry count')
    for name,size,mode in entries:
        _valid_name(name)
        canonical=name.casefold()
        if canonical in seen:
            raise ValueError('duplicate or case-colliding path')
        seen.add(canonical)
        if type(size) is not int or not 0<=size<=MAX_SOURCE_BYTES:
            raise ValueError('oversized file or invalid size')
        if type(mode) is not int or stat.S_IFMT(mode)==stat.S_IFLNK:
            raise ValueError('symlink/invalid mode')
        if stat.S_IFMT(mode) not in (0,stat.S_IFREG):
            raise ValueError('nonregular entry')
        total+=size
        if total>MAX_TOTAL_BYTES:raise ValueError('oversized archive')
    return True


def _check_source_content(name, data):
    if not data or b'\x00' in data:
        raise ValueError('binary or empty source')
    try:
        data.decode('utf-8',errors='strict')
    except UnicodeDecodeError:
        raise ValueError('non-UTF8 source') from None
    if any(c<32 and c not in (9,10,13) for c in data):
        raise ValueError('embedded binary control bytes')
    if any(regex.search(data) for regex in (_HEX_DUMP,_ESCAPED_BYTES,_BASE64_BLOB,_HEX_BLOB)):
        raise ValueError('potential embedded game data; manual review required')
    # Real per-frame object arrays often appear inside .json/.yml uploads.
    # Only pinned workflow YAML is allowed (checked above).
    return True


def inspect_zip(data):
    if not isinstance(data,bytes):raise ValueError('archive must be bytes')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos=z.infolist()
            files=[i for i in infos if not i.is_dir()]
            # Ensure directory entries also have safe canonical names.
            for i in infos:
                if i.is_dir():
                    dirname=i.filename.rstrip('/')
                    if not dirname or dirname.startswith('/') or '\\' in dirname or '..' in PurePosixPath(dirname).parts:
                        raise ValueError('unsafe archive directory')
            check_names([(i.filename,i.file_size,i.external_attr>>16) for i in files])
            for i in files:
                if i.flag_bits & 1:raise ValueError('encrypted entry')
                # Excessive compression is suspicious for binary or pasted ROMs.
                if i.file_size>65536 and i.compress_size*100<i.file_size:
                    raise ValueError('excessive compression ratio')
                content=z.read(i)
                if len(content)!=i.file_size:raise ValueError('size mismatch')
                _check_source_content(i.filename,content)
    except (zipfile.BadZipFile,RuntimeError) as e:
        raise ValueError('unsafe or invalid ZIP') from e
    return True
