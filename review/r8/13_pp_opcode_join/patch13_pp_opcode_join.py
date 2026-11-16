"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    events=s.get('events')
    if type(events) is not list or len(events)!=3 or any(type(e) is not dict for e in events):return False
    if [e.get('kind') for e in events]!=['fight','move','pp']:return False
    if any(type(e.get('f')) is not int or type(e.get('epoch')) is not int or type(e.get('owner')) is not int or type(e.get('slot')) is not int for e in events):return False
    if not events[0]['f']<events[1]['f']<events[2]['f']:return False
    if len({e['epoch'] for e in events})!=1 or events[0]['epoch']<=0 or any(e['owner']!=0 for e in events):return False
    if events[1]['slot']!=events[2]['slot'] or not 0<=events[2]['slot']<=3:return False
    p=events[2]
    if p.get('pc')!='0x0809e6ba' or p.get('opcode_verified') is not True:return False
    if type(p.get('before')) is not int or type(p.get('after')) is not int:return False
    if not 1<=p['before']<=99 or p['after']!=p['before']-1:return False
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
