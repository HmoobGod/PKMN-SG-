"""Public import boundary and host syntax check; never loads private game data."""
from pathlib import Path
import os,subprocess
root=Path(__file__).resolve().parents[1]
blocked={'.gba','.sav','.ss','.state','.elf','.o','.so','.bin','.zip','.7z','.b64'}
files=[p for p in root.rglob('*')if p.is_file()and '.git'not in p.relative_to(root).parts]
for p in files:
 assert p.suffix.lower()not in blocked,f'Private/generated artifact: {p.relative_to(root)}'
 assert p.stat().st_size<1_000_000,f'Unexpected large file: {p.relative_to(root)}'
for name in ['README.md','.gitignore','docs/STATUS.md','docs/checkpoint.json']:
 assert (root/name).is_file(),name
sources=sorted(str(p)for p in (root/'src').glob('*.c'))
subprocess.run([os.environ.get('CC','cc'),'-std=c11','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+str(root/'src'),'-I'+str(root/'include'),*sources],check=True)
print(f'PASS: {len(files)} public source/document files; {len(sources)} C translation units')
