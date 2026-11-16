"""One-use request lease *model*. Never writes to original controller.

A lease requires a genuine external engine-issued request epoch. Do not create
one merely by observing PP or an unchanging menu cursor.
"""
from dataclasses import dataclass
@dataclass
class Lease:
 epoch:int
 turn:int
 owner:int
 requested_command:int
 resource_identity:int
 consumed:bool=False

def consume(lease,epoch,turn,owner,command,resource_identity):
 if not isinstance(lease,Lease) or type(lease.consumed) is not bool:return False
 vals=(epoch,turn,owner,command,resource_identity,lease.epoch,lease.turn,lease.owner,lease.requested_command,lease.resource_identity)
 if any(type(x) is not int or x<0 or x>0xffffffff for x in vals):return False
 if lease.consumed or not epoch or not resource_identity or owner!=0 or command not in (17,19):return False
 if (lease.epoch,lease.turn,lease.owner,lease.requested_command,lease.resource_identity)!=(epoch,turn,owner,command,resource_identity):return False
 lease.consumed=True
 return True
PRODUCTION_AUTHORIZED=False
