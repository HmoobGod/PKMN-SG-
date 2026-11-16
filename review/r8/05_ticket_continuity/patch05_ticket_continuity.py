"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    t=s.get('ticket');q=s.get('move')
    if type(t) is not dict or type(q) is not dict:return False
    fields=('epoch','turn','party','foe','slot','move_id')
    if set(t)!=set(fields) or set(q)!=set(fields):return False
    if any(type(t[k]) is not int or type(q[k]) is not int or t[k]!=q[k] for k in fields):return False
    if t['epoch']<=0 or t['turn']<0 or not 0<=t['party']<=5 or not 0<=t['foe']<=3:return False
    if not 0<=t['slot']<4 or not 0<t['move_id']<=65535:return False
    if s.get('stage')!='CHOOSEMOVE' or s.get('ticket_pending') is not True:return False
    if s.get('lease_consumed') is not False:return False
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
