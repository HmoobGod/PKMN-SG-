import unittest,io,zipfile,stat,base64
from patch10_private_artifact_boundary import check_names,inspect_zip,MAX_SOURCE_BYTES,MAX_TOTAL_BYTES

def pack(entries):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w') as z:
  for k,v in entries.items():z.writestr(k,v)
 return b.getvalue()
class Tests(unittest.TestCase):
 def deny(self,entries):
  with self.assertRaises(ValueError):inspect_zip(pack(entries))
 def test_safe(self):
  self.assertTrue(inspect_zip(pack({'tools/test.py':'print(1)'})))
 def test_rom_save_trace_extensions_and_double_suffixes(self):
  for name in ('assets/game.gba','current.sav','cpu.jsonl','rom.gba.txt','x.sav.py','rom.nds.md','save.sgm.c','assets/picture.PNG','my.log.py','nested.zip.txt'):
   with self.subTest(name=name):self.deny({name:'synthetic'})
 def test_disguised_trace(self):
  for name in ('cpu_trace.json','cpu_trace.yml','save_dump.c','rom_dump.txt','r6/raw-memory-dump.py'):
   with self.subTest(name=name):self.deny({name:'{}'})
 def test_hidden_and_paths(self):
  for name in ('../x.py','.ssh/key.py','tools/../x.py','/tmp/x.py','x\\y.py','C:/x.py','./x.py','a//x.py','a/.secret.py','a/./b.py'):
   with self.subTest(name=name):self.deny({name:'safe'})
 def test_hidden_exceptions_workflow(self):
  self.assertTrue(inspect_zip(pack({'.github/workflows/check.yml':'name: Test\n'})))
  self.deny({'misc/check.yml':'name: Check\n'})
 def test_single_size_total_size_and_types(self):
  for vals in ([('x.py',MAX_SOURCE_BYTES+1,0)],[('x.py',True,0)],[('x.py',-1,0)],[('x.py',0,'bad')]):
   with self.subTest(vals=vals):
    with self.assertRaises(ValueError):check_names(vals)
  with self.assertRaises(ValueError):check_names([(f'p/{i:03d}.py',MAX_SOURCE_BYTES,0) for i in range(11)])
 def test_symlink_and_nonregular(self):
  with self.assertRaises(ValueError):check_names([('link.py',5,stat.S_IFLNK|0o777)])
  with self.assertRaises(ValueError):check_names([('dev.py',5,stat.S_IFCHR|0o600)])
 def test_duplicate_and_case_collision(self):
  with self.assertRaises(ValueError):check_names([('A.py',1,0),('a.py',1,0)])
  b=io.BytesIO()
  with zipfile.ZipFile(b,'w') as z:z.writestr('t.py','a');z.writestr('t.py','b')
  with self.assertRaises(ValueError):inspect_zip(b.getvalue())
 def test_many_entries(self):
  with self.assertRaises(ValueError):check_names([(f'{i}.py',1,0) for i in range(501)])
 def test_hidden_binary_save_dumps_in_code(self):
  # Synthetic dump shape only; never read real game assets.
  self.deny({'safe.c':'const unsigned char x[]={'+'0x12, '*512+'};'})
  self.deny({'safe.c':'const char *x="'+'\\x20'*256+'";'})
  self.deny({'safe.txt':base64.b64encode(b'fake' * 32768).decode()})
  self.deny({'safe.h':'A1'*10000})
 def test_binary_or_undecodable(self):
  self.deny({'safe.py':b'\x00\x01'});self.deny({'safe.py':b'\xff'})
 def test_nested_archive_or_empty(self):
  self.deny({'nested.zip':pack({'x.py':'safe'})})
  self.deny({'blank.py':''})
 def test_forbidden_extension(self):
  with self.assertRaises(ValueError):check_names([('test.exe',10,0)])
 def test_no_privacy_guarantee(self):
  # Name/content heuristics are only a secondary control; human review still required.
  self.assertTrue(inspect_zip(pack({'src/small.py':'value = 1\n'})))
if __name__=='__main__':unittest.main()
