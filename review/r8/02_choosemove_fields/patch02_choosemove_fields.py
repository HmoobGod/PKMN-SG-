"""Source-only, fake-input audit contract. NOT an original-engine witness."""
import re

def _predicate(s):
    if type(s) is not dict: return False
    b=s.get('payload'); moves=s.get('moves'); pp=s.get('pp'); mx=s.get('max_pp')
    if type(b) is not list or len(b)!=40 or any(type(x) is not int or not 0<=x<=255 for x in b):return False
    if type(moves) is not list or type(pp) is not list or type(mx) is not list or any(len(x)!=4 for x in (moves,pp,mx)):return False
    if b[:4]!=[19,0,0,0]:return False
    for i in range(4):
        if type(moves[i]) is not int or not 0<=moves[i]<=65535:return False
        if type(pp[i]) is not int or type(mx[i]) is not int or not 0<=pp[i]<=99 or not 0<=mx[i]<=99:return False
        if b[4+2*i] + (b[5+2*i]<<8)!=moves[i] or b[12+i]!=pp[i] or b[16+i]!=mx[i]:return False
        if (moves[i]==0 and (pp[i]!=0 or mx[i]!=0)) or (moves[i]!=0 and (mx[i]==0 or pp[i]>mx[i])):return False
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
