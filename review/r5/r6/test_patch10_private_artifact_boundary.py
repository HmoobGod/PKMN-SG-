import unittest,io,zipfile
from patch10_private_artifact_boundary import check_names,inspect_zip

def pack(entries):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w') as z:
  for k,v in entries.items():z.writestr(k,v)
 return b.getvalue()
class Tests(unittest.TestCase):
 def test_safe(self):self.assertTrue(inspect_zip(pack({'tools/test.py':'print(1)'})))
 def test_rom(self):
  with self.assertRaises(ValueError):inspect_zip(pack({'assets/game.gba':'secret'}))
 def test_save(self):
  with self.assertRaises(ValueError):inspect_zip(pack({'current.sav':'save'}))
 def test_cpu_trace(self):
  with self.assertRaises(ValueError):inspect_zip(pack({'cpu.jsonl':'private'}))
 def test_traversal(self):
  with self.assertRaises(ValueError):inspect_zip(pack({'../x.py':'x'}))
 def test_hidden(self):
  with self.assertRaises(ValueError):inspect_zip(pack({'.ssh/key.py':'x'}))
 def test_dup(self):
  b=io.BytesIO()
  with zipfile.ZipFile(b,'w') as z:z.writestr('t.py','a');z.writestr('t.py','b')
  with self.assertRaises(ValueError):inspect_zip(b.getvalue())
 def test_extension(self):
  with self.assertRaises(ValueError):check_names([('test.exe',10,0)])
if __name__=='__main__':unittest.main()
