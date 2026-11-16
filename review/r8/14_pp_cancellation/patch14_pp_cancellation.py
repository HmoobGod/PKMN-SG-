"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    cause=s.get('cause');reason=s.get('reason');ep=s.get('epoch')
    if type(ep) is not int or ep<=0 or s.get('request_epoch')!=ep:return False
    if s.get('original_opcode_verified') is not True or s.get('owner')!=0:return False
    if type(s.get('pp_before')) is not int or type(s.get('pp_after')) is not int:return False
    if not 1<=s['pp_before']<=99 or s['pp_after']!=s['pp_before']-1:return False
    if cause!='confirmed_move_execution' or reason!='original_script_consumed_pp':return False
    if s.get('cancellation_barrier') is not False or s.get('manual_barrier') is not False:return False
    if s.get('outcome_confirmed') is not True:return False
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
