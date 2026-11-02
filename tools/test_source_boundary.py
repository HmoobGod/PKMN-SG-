"""Adversarial smoke checks for renamed binary-like content in text files."""
from check_source import content_issue
assert content_issue('deadbeef'*32)=='long hex run'
assert content_issue('QWxhZGRp'*40)=='long base64-like run'
assert content_issue('POKEMON'+' EMER Version')=='possible game ROM title'
assert content_issue('data = {'+'1,'*9000+'};')=='large flat initializer'
assert content_issue('sha256: '+'a'*64)is None
assert content_issue('const int chart[] = {1,2,3};')is None
print('PASS: six renamed-content/boundary cases')
