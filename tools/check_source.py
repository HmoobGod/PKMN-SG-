"""Check tracked public files and host C syntax; never loads private game data."""
from pathlib import Path
import os,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
BLOCKED={'.gba','.sav','.ss','.state','.elf','.o','.so','.bin','.zip','.7z','.b64'}
def content_issue(text):
 if re.search(r'(?i)(?<![0-9a-f])[0-9a-f]{128,}(?![0-9a-f])',text):return 'long hex run'
 if re.search(r'(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{256,}={0,2}(?![A-Za-z0-9+/])',text):return 'long base64-like run'
 if re.search(r'POKEMON(?: FIRE| LEAF| EMER| RUBY| SAPP)',text):return 'possible game ROM title'
 if re.search(r'=\s*\{[^{}]{16384,}\}',text,re.S):return 'large flat initializer'
 return None
def public_files():
 if (ROOT/'.git').exists():
  names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0');return [ROOT/n for n in names if n]
 return [p for p in ROOT.rglob('*')if p.is_file()and not set(p.relative_to(ROOT).parts)&{'.git','build','__pycache__'}]
def main():
 files=public_files()
 for p in files:
  assert p.suffix.lower()not in BLOCKED,f'Private/generated artifact: {p.relative_to(ROOT)}'
  assert p.stat().st_size<1_000_000,f'Unexpected large file: {p.relative_to(ROOT)}'
  text=p.read_text();issue=content_issue(text);assert not issue,f'{issue}: {p.relative_to(ROOT)}'
 for name in ['README.md','.gitignore','docs/STATUS.md','docs/checkpoint.json']:assert (ROOT/name).is_file(),name
 sources=sorted(str(p)for p in (ROOT/'src').glob('*.c'))
 subprocess.run([os.environ.get('CC','cc'),'-std=c11','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+str(ROOT/'src'),'-I'+str(ROOT/'include'),*sources],check=True)
 print(f'PASS: {len(files)} public files; {len(sources)} C translation units; content checks are heuristics, not a proof')
if __name__=='__main__':main()
