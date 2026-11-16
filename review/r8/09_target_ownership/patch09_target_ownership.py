"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    if s.get('battler')!=0 or type(s.get('battler')) is not int:return False
    if s.get('owned') is not True or s.get('wild_single') is not True or s.get('doubles') is not False:return False
    target=s.get('target');foe=s.get('active_foe')
    if type(target) is not int or type(foe) is not int or target!=foe or not 0<=foe<=3:return False
    if target==s.get('battler') or s.get('foe_alive') is not True:return False
    if s.get('native_target_proven') is not True or s.get('partner') is not False:return False
    if s.get('target_epoch')!=s.get('request_epoch') or type(s.get('request_epoch')) is not int or s['request_epoch']<=0:return False
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
