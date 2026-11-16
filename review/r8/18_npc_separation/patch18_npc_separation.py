"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    if s.get('player_battler')!=0 or type(s.get('player_battler')) is not int:return False
    if s.get('owner_kind')!='player' or s.get('enemy_ai_changed') is not False:return False
    if s.get('npc_partner_present') is not False or s.get('npc_ai_changed') is not False:return False
    if s.get('wild_single') is not True or s.get('double_battle') is not False:return False
    if s.get('active_actor')!=0 or type(s.get('active_actor')) is not int:return False
    if s.get('original_controller_verified') is not True:return False
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
