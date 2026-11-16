"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    if s.get('event')!='cursor_store' or s.get('kind')!='target':return False
    if s.get('pc')!='0x08016fb6' or s.get('thumb_source_verified') is not True:return False
    ptr=s.get('pointer');address=s.get('address')
    if type(ptr) is not int or type(address) is not int or not 0x02000000<=ptr<=0x0203fef5:return False
    if address!=ptr+0x10a:return False
    if s.get('owner')!=0 or type(s.get('owner')) is not int:return False
    target=s.get('target_after');foe=s.get('active_foe')
    if type(target) is not int or type(foe) is not int or not 0<=target<=3 or target!=foe:return False
    if s.get('target_alive') is not True or s.get('epoch')!=s.get('request_epoch') or type(s.get('epoch')) is not int or s['epoch']<=0:return False
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
