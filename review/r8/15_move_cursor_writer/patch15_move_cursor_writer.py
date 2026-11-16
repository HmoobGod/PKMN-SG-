"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    if s.get('event')!='cursor_store' or s.get('kind')!='slot':return False
    if s.get('pc')!='0x0801862e' or s.get('thumb_source_verified') is not True:return False
    ptr=s.get('pointer');address=s.get('address')
    if type(ptr) is not int or type(address) is not int or not 0x02000000<=ptr<=0x0203fef9:return False
    if address!=ptr+0x106:return False
    if s.get('owner')!=0 or type(s.get('owner')) is not int:return False
    slot=s.get('slot_after')
    if type(slot) is not int or not 0<=slot<=3:return False
    if s.get('epoch')!=s.get('request_epoch') or type(s.get('epoch')) is not int or s['epoch']<=0:return False
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
