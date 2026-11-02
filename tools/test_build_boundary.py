"""Check the pinned base-cave replacement boundary without loading any ROM."""
from build_private import BASE_CAVE_BYTES,validate_cave_span
for size in [0,BASE_CAVE_BYTES-1]:
 try:validate_cave_span(size)
 except ValueError:pass
 else:raise AssertionError('short replacement accepted')
for size in [BASE_CAVE_BYTES,BASE_CAVE_BYTES+1,5886]:validate_cave_span(size)
print('PASS: five cave replacement boundary cases')
