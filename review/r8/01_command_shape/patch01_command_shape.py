"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    if type(s.get('command')) is not int or s['command'] not in (17,19):return False
    b=s.get('payload')
    if type(b) is not list or any(type(x) is not int or not 0<=x<=255 for x in b):return False
    if len(b)!=(4 if s['command']==17 else 40):return False
    if b[0]!=s['command'] or b[1]!=0 or b[2]!=0 or b[3]!=0:return False
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
