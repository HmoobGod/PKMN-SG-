"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    if s.get('quarantined') is not True:return False
    old=s.get('old_epoch');new=s.get('new_epoch')
    if type(old) is not int or type(new) is not int or old<=0 or new<=old:return False
    for field in ('battle_finished','controller_rearmed','queue_empty','request_owned','player0','wild_single','human_barrier_cleared'):
        if s.get(field) is not True:return False
    if s.get('unresolved_ticket') is not False or s.get('prior_request_in_flight') is not False:return False
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
