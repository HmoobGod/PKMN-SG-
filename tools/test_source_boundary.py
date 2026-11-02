"""Adversarial smoke checks for renamed binary-like content in text files."""
from check_source import content_issue
import base64,json,random,textwrap
assert content_issue('deadbeef'*32)=='long hex run'
assert content_issue('QWxhZGRp'*40)=='long base64-like run'
assert content_issue('POKEMON'+' EMER Version')=='possible game ROM title'
assert content_issue('data = {'+'1,'*9000+'};')=='large decimal byte array'
assert content_issue('sha256: '+'a'*64)is None
assert content_issue('const int chart[] = {1,2,3};')is None
# Deterministic disposable bytes, unrelated to any game or private file.
payload=random.Random(16265).randbytes(4096)
formats={
 'wrapped base64':'\n'.join(textwrap.wrap(base64.b64encode(payload).decode(),76)),
 'wrapped xxd hex':'\n'.join(textwrap.wrap(payload.hex(),60)),
 'spaced hex':' '.join(f'{b:02x}'for b in payload),
 'JSON bytes':json.dumps(list(payload)),
 'C decimal bytes':'unsigned char data[] = {'+','.join(map(str,payload))+'};',
 'prefixed hex':'unsigned char data[] = {'+','.join(f'0x{b:02x}'for b in payload)+'};',
}
for name,value in formats.items():assert content_issue(value),name
for value in ['Normal documentation with words and spaces.\n'*100,
              'sha256: '+'b'*64+'\n'+'sha256: '+'c'*64,
              'int counts[] = {'+','.join(['1024']*300)+'};']:
 assert content_issue(value)is None
print('PASS: 15 renamed-content/boundary cases (six encoded dump formats)')
