"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    ep=s.get('epoch');rid=s.get('request');seen=s.get('seen');cap=s.get('cap')
    if any(type(x) is not int for x in (ep,rid,cap)) or ep<=0 or rid<=0 or not 1<=cap<=64:return False
    if type(seen) is not list or len(seen)>=cap:return False
    if any(type(x) is not int or x<=0 for x in seen) or len(set(seen))!=len(seen):return False
    if rid in seen:return False
    if s.get('host_epoch')!=ep or s.get('host_owned') is not True:return False
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
