"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    if s.get('source_commit')!=s.get('build_source_commit'):return False
    if type(s.get('source_commit')) is not str or not re.fullmatch('[0-9a-f]{40}',s['source_commit']):return False
    for key in ('rom_sha256','build_rom_sha256','map_rom_sha256'):
        if type(s.get(key)) is not str or not re.fullmatch('[0-9a-f]{64}',s[key]):return False
    if not s['rom_sha256']==s['build_rom_sha256']==s['map_rom_sha256']:return False
    if s.get('map_present') is not True or s.get('symbol_addresses_verified') is not True:return False
    if s.get('toolchain_identity_verified') is not True or s.get('reviewed_source_diff_verified') is not True:return False
    return True

def evaluate(sample):
    try:
        candidate = (_predicate(sample) is True)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        candidate = False
    return {
        'candidate_UNVERIFIED':candidate,
        'native_accepted':0,
        'manual_fallback_certified':False,
        'no_forced_switch_certified':False,
        'production_authorized':False,
    }
