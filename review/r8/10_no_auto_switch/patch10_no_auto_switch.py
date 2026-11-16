"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    cmd=s.get('command');action=s.get('action')
    if type(cmd) is not int or type(action) is not int:return False
    if not ((cmd==17 and action==0) or (cmd==19 and action==10)):return False
    if s.get('player0') is not True or s.get('wild_single') is not True:return False
    if s.get('engine_owned') is not True or s.get('lease_unconsumed') is not True:return False
    if s.get('manual_pending') is not False or s.get('actor_is_partner') is not False:return False
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
