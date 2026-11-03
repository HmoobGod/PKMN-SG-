"""ROM-free host C test for research-only single-use request leases."""
from pathlib import Path
import os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
sources=[ROOT/'research'/'sg_choice_lease.c',ROOT/'research'/'test_choice_lease.c']
with tempfile.TemporaryDirectory() as tmp:
 for label,flags in [('optimized',['-O2']),('UBSan',['-O1','-fno-sanitize-recover=all','-fsanitize=undefined'])]:
  exe=Path(tmp)/label
  subprocess.run([os.environ.get('CC','cc'),'-std=c11','-pedantic','-Wall','-Wextra','-Werror',*flags,'-I'+str(ROOT/'research'),*(str(s) for s in sources),'-o',str(exe)],check=True)
  r=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
  print(label,r.stdout.strip())
