"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    checks=s.get('checks');witness=s.get('witnesses')
    if type(checks) is not list or len(checks)!=20 or any(type(x) is not bool for x in checks):return False
    if type(witness) is not list or len(witness)!=20 or any(type(x) is not str for x in witness):return False
    if any(not x for x in checks):return False
    if any(not x or not x.startswith('independent-original-engine:') for x in witness):return False
    if len(set(witness))!=20:return False
    if s.get('exact_rom_identity_verified') is not True or s.get('manual_fallback_native_verified') is not True:return False
    if s.get('forced_switch_blocked_native') is not True or s.get('private_replay_complete') is not True:return False
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
