"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    moves=s.get('moves');pp=s.get('pp');legal=s.get('legal');targets=s.get('targets');priority=s.get('priority')
    if any(type(x) is not list or len(x)!=4 for x in (moves,pp,legal,targets,priority)):return False
    for i in range(4):
        if type(moves[i]) is not int or not 0<=moves[i]<=65535:return False
        if type(pp[i]) is not int or not 0<=pp[i]<=99:return False
        if type(legal[i]) is not bool or type(targets[i]) is not bool:return False
        if type(priority[i]) is not int or not -9<=priority[i]<=9:return False
    slot=s.get('slot')
    if type(slot) is not int or not 0<=slot<=3:return False
    if not (moves[slot]>0 and pp[slot]>0 and legal[slot] and targets[slot]):return False
    if s.get('engine_limits_checked') is not True or s.get('engine_target_checked') is not True:return False
    if s.get('epoch')!=s.get('legality_epoch') or type(s.get('epoch')) is not int or s['epoch']<=0:return False
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
