"""Offline, read-only replay of recorded actor-0 native requests into C lease model.

The seed is modeled explicitly because its real enqueue predates the observer.
No automatic claims, emulator, native emitter or ROM access.
"""
import argparse
import ctypes as C
import json
import subprocess
import tempfile
from pathlib import Path
from validate_choice_lifecycle import validate
ROOT=Path(__file__).resolve().parents[1]
class Lease(C.Structure):
 _fields_=[('epoch',C.c_uint64),('state',C.c_int),('actor',C.c_uint8)]
def replay(lib,report):
 validate(report)
 lease=Lease();lib.sg_lease_init(C.byref(lease))
 assert lib.sg_lease_on_buffer_a_copy(C.byref(lease),0,19,44,True)
 stats={'seeded':1,'new':0,'completed':0}
 for event in report['events']:
  kind=event['event']
  if kind=='copy' and event.get('direction')==0 and event.get('header',[None])[0]==19:
   assert lib.sg_lease_on_buffer_a_copy(C.byref(lease),0,19,44,True)
   stats['new']+=1;assert lease.state==1
  elif kind=='emit':
   assert lease.state==1 # never call claim; owner/legality unavailable
  elif kind=='completion':
   assert lib.sg_lease_on_terminal(C.byref(lease),lease.epoch)
   stats['completed']+=1;assert lease.state==0
 assert lease.state==1 # final request awaiting human input
 assert stats['new']==len(report['epochs'])-1
 assert stats['completed']==sum(bool(x['emit']) for x in report['epochs'])
 return stats
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('reports',type=Path)
 a=p.parse_args();data=json.loads(a.reports.read_text())
 reports=[x['report'] for x in data['reports']] if 'reports' in data else [data]
 with tempfile.TemporaryDirectory() as td:
  so=Path(td)/'liblease.so'
  subprocess.run(['cc','-shared','-fPIC','-std=c11','-O2','-Wall','-Wextra','-Werror',
    '-I'+str(ROOT/'research'),str(ROOT/'research'/'sg_choice_lease.c'),'-o',str(so)],check=True)
  lib=C.CDLL(str(so))
  lib.sg_lease_init.argtypes=[C.POINTER(Lease)]
  lib.sg_lease_on_buffer_a_copy.argtypes=[C.POINTER(Lease),C.c_uint32,C.c_uint32,C.c_uint32,C.c_bool]
  lib.sg_lease_on_buffer_a_copy.restype=C.c_bool
  lib.sg_lease_on_terminal.argtypes=[C.POINTER(Lease),C.c_uint64]
  lib.sg_lease_on_terminal.restype=C.c_bool
  total={'seeded':0,'new':0,'completed':0}
  for report in reports:
   stats=replay(lib,report)
   print('PASS',report.get('case','observer'),stats)
   for key in total:total[key]+=stats[key]
  print('TOTAL',len(reports),'recorded cases',total,'(offline-only; no authorization)')
if __name__=='__main__':main()
