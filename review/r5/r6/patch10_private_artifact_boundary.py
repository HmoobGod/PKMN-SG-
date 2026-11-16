"""Offline source-only packaging boundary. This is supplementary to human review."""
from pathlib import PurePosixPath
import io,zipfile,stat
FORBIDDEN_SUFFIX={'.gba','.sav','.sgm','.state','.bin','.jsonl','.rgba','.png','.jpg','.jpeg','.so','.elf','.map','.dmp','.trace','.log'}
FORBIDDEN_BASENAMES={'pokemon soulgold.gba','pokemon soulgold.sav','mgba-rom-test'}
MAX_SOURCE_BYTES=1024*1024
MAX_TOTAL_BYTES=10*1024*1024

def check_names(entries):
 total=0
 for name,size,mode in entries:
  p=PurePosixPath(name)
  if not isinstance(name,str) or not name or name.startswith('/') or '\\' in name or '..' in p.parts or p.is_absolute():raise ValueError('unsafe path')
  if any(part.startswith('.') and part not in ('.github',) for part in p.parts):raise ValueError('hidden content')
  if p.suffix.lower() in FORBIDDEN_SUFFIX or p.name.lower() in FORBIDDEN_BASENAMES:raise ValueError('private or binary artifact')
  if p.suffix.lower() not in ('.py','.c','.h','.md','.txt','.patch','.yml','.yaml','.json'):raise ValueError('not source-only')
  if not 0<=size<=MAX_SOURCE_BYTES:raise ValueError('oversize entry')
  if stat.S_IFMT(mode)==stat.S_IFLNK:raise ValueError('symlink entry')
  total+=size
  if total>MAX_TOTAL_BYTES:raise ValueError('oversize archive')
 return True

def inspect_zip(data):
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  entries=[(i.filename,i.file_size,i.external_attr>>16) for i in z.infolist() if not i.is_dir()]
  if not entries or len(entries)>500:raise ValueError('empty or excessive entries')
  if len({x[0] for x in entries})!=len(entries):raise ValueError('duplicate paths')
  check_names(entries)
  # Source-only packages must not hide files in nested ZIPs or zip bombs.
  for i in z.infolist():
   if i.is_dir():continue
   if len(z.read(i))!=i.file_size:raise ValueError('bad file size')
 return True
