"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    if type(s.get('epoch')) is not int or s['epoch']<=0 or s.get('status_epoch')!=s['epoch']:return False
    if s.get('player0') is not True or s.get('wild_single') is not True:return False
    if type(s.get('selected_move')) is not int or type(s.get('taunt_move')) is not int:return False
    if s['taunt_move']<=0 or s['selected_move']!=s['taunt_move']:return False
    if s.get('status_proven') is not True or s.get('target_alive') is not True:return False
    if s.get('target_id')!=s.get('status_target_id'):return False
    if s.get('taunt_active') is not True:return False
    if s.get('legality_verified') is not True:return False
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
