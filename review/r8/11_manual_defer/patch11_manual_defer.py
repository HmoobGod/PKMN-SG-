"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    if s.get('auto_response_count')!=0 or type(s.get('auto_response_count')) is not int:return False
    if s.get('defer_requested') is not True or s.get('original_controller_retained') is not True:return False
    if s.get('manual_menu_visible') is not True or s.get('human_input_after_menu') is not True:return False
    if s.get('original_manual_action_seen') is not True or s.get('auto_switch_seen') is not False:return False
    sequence=s.get('events')
    if type(sequence) is not list or sequence!=['defer','menu','human_input','original_manual_action']:return False
    if s.get('original_request_epoch')!=s.get('menu_epoch') or type(s.get('menu_epoch')) is not int or s['menu_epoch']<=0:return False
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
