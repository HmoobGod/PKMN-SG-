"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    before=s.get('before');after=s.get('after')
    if type(before) is not dict or type(after) is not dict:return False
    fields=('epoch','request','battler','command','turn','party','foe','owned','wild','doubles','partner','resources')
    if set(before)!=set(fields) or set(after)!=set(fields):return False
    if any(before[k]!=after[k] for k in fields):return False
    if any(type(before[k]) is not int for k in ('epoch','request','battler','command','turn','party','foe','resources')):return False
    if any(type(before[k]) is not bool for k in ('owned','wild','doubles','partner')):return False
    if before['epoch']<=0 or before['request']<=0 or before['battler']!=0 or before['command'] not in (17,19):return False
    if not before['owned'] or not before['wild'] or before['doubles'] or before['partner'] or before['resources']<=0:return False
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
