"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    times=s.get('times')
    if type(times) is not dict or set(times)!=set(('defer','menu','human','manual_action')):return False
    if any(type(v) is not int or v<0 for v in times.values()):return False
    if not times['defer']<times['menu']<times['human']<times['manual_action']:return False
    if s.get('input_source')!='physical_human' or s.get('key') not in ('A','B','UP','DOWN','LEFT','RIGHT'):return False
    if s.get('emulated_input_injected') is not False or s.get('automatic_action_after_defer') is not False:return False
    if s.get('battler')!=0 or type(s.get('battler')) is not int:return False
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
