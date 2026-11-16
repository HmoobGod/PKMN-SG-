"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    steps=s.get('steps')
    if type(steps) is not dict or set(steps)!=set(('battle_start','last_auto','outcome','overworld')):return False
    if any(type(x) is not int or x<0 for x in steps.values()):return False
    if not steps['battle_start']<=steps['last_auto']<steps['outcome']<steps['overworld']:return False
    if s.get('original_battle_outcome_verified') is not True or s.get('original_overworld_return_verified') is not True:return False
    if s.get('auto_after_outcome')!=0 or type(s.get('auto_after_outcome')) is not int:return False
    if s.get('forced_switch_count')!=0 or type(s.get('forced_switch_count')) is not int:return False
    if s.get('owner')!=0 or type(s.get('owner')) is not int:return False
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
