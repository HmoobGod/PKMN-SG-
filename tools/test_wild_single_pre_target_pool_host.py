#!/usr/bin/env python3
"""Host-C execution of the ACTUAL added player0 source-LAB proposal function.

Disposable public source only. No private ROM, emulator, game state, or
build integration. The test extracts the live C function from the patch,
compiles that function unchanged against minimal host mocks, and attempts
helper-side mutations of earlier/later player-owned move and PP slots.
"""
from pathlib import Path
import subprocess
import tempfile

PATCH = Path(__file__).resolve().parents[1] / "source-first" / "wild-single-lab.patch"

PRELUDE = r"""
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#ifdef NDEBUG
#error "Host player0 proposal tests require enabled assertions"
#endif
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int bool32;
enum BattlerId { B_PLAYER=0, B_FOE=1 };
enum Move { MOVE_NONE=0, MOVE_A=10, MOVE_B=11, MOVE_C=12,
            MOVE_D=13, MOVE_STRUGGLE=165 };
#define MAX_MON_MOVES 4
#define TARGET_SELECTED 1
#define CONTROLLER_CHOOSEACTION 0x20
#define CONTROLLER_CHOOSEMOVE 0x21
#define B_POSITION_OPPONENT_LEFT 1
#define MOVE_LIMITATIONS_ALL 255
#define FALSE 0
#define TRUE 1

struct ChooseMoveStruct {
    enum Move moves[4];
    u8 currentPp[4];
};
struct BattleResources { u8 bufferA[2][128]; };
struct BattleMon { enum Move moves[4]; u8 pp[4]; };
static struct BattleResources res;
static struct BattleResources *gBattleResources=&res;
static struct BattleMon gBattleMons[2];
static u16 gBattleTurnCounter=9;
static u8 gBattlerPartyIndexes[2]={0,0};
static struct {
    u16 turnCounter;
    u32 proposedSlot;
} sSourceFirstWildLease;

static unsigned mutate_kind; /* 0 none; 1 move; 2 PP */
static unsigned mutate_slot, skip_first, helper_calls;
static bool32 SourceFirstWildSingleOwner(enum BattlerId battler)
{
    return battler==B_PLAYER &&
           gBattleResources!=NULL &&
           gBattleTurnCounter==9 &&
           gBattlerPartyIndexes[B_PLAYER]==0;
}
static bool32 SourceFirstWildLeaseSnapshotMatches(enum BattlerId battler)
{
    return SourceFirstWildSingleOwner(battler);
}
static enum BattlerId GetBattlerAtPosition(int position)
{
    assert(position==B_POSITION_OPPONENT_LEFT);
    return B_FOE;
}
static u32 CheckMoveLimitations(enum BattlerId battler,u32 restricts,u32 flags)
{
    (void)battler; (void)restricts; (void)flags;
    return 0;
}
static int GetBattlerMoveTargetType(enum BattlerId battler,enum Move move)
{
    assert(battler==B_PLAYER);
    assert(move>=MOVE_A && move<=MOVE_D);
    return TARGET_SELECTED;
}
static bool32 CanTargetBattler(enum BattlerId battler,
                               enum BattlerId target,enum Move move)
{
    assert(battler==B_PLAYER && target==B_FOE);
    helper_calls++;
    if(move==MOVE_A) {
        if(mutate_kind==1)
            gBattleMons[B_PLAYER].moves[mutate_slot]=MOVE_STRUGGLE;
        if(mutate_kind==2)
            gBattleMons[B_PLAYER].pp[mutate_slot]=0;
        if(skip_first)return FALSE;
    }
    return TRUE;
}
"""

TESTS = r"""
static void reset_case(unsigned kind,unsigned target_slot,unsigned skip)
{
    enum Move before[4]={MOVE_A,MOVE_B,MOVE_C,MOVE_D};
    u8 pp[4]={8,9,10,11};
    memset(&res,0,sizeof res);
    memset(gBattleMons,0,sizeof gBattleMons);
    memcpy(gBattleMons[B_PLAYER].moves,before,sizeof before);
    memcpy(gBattleMons[B_PLAYER].pp,pp,sizeof pp);
    res.bufferA[B_PLAYER][0]=CONTROLLER_CHOOSEACTION;
    gBattleTurnCounter=9;
    gBattlerPartyIndexes[B_PLAYER]=0;
    gBattlerPartyIndexes[B_FOE]=0;
    sSourceFirstWildLease.turnCounter=9;
    sSourceFirstWildLease.proposedSlot=0;
    mutate_kind=kind;
    mutate_slot=target_slot;
    skip_first=skip;
    helper_calls=0;
}
int main(void)
{
    u32 reply=99;
    unsigned count=0;
    /* No-drift baselines: normal slot0 and ineligible slot0 -> slot1. */
    for(unsigned skip=0;skip<=1;skip++){
        reset_case(0,0,skip);
        reply=99;
        assert(SourceFirstWildSingleMove(B_PLAYER,FALSE,&reply)==TRUE);
        assert(reply==(skip?1u:0u));
        assert(helper_calls>=1u);
        count++;
    }
    /* Mutation of ANY player-owned move/PP, including an earlier or later
     * candidate, must return FALSE even if slot0 was ineligible. */
    for(unsigned kind=1;kind<=2;kind++){
        for(unsigned slot=0;slot<MAX_MON_MOVES;slot++){
            for(unsigned skip=0;skip<=1;skip++){
                reset_case(kind,slot,skip);
                reply=99;
                assert(SourceFirstWildSingleMove(B_PLAYER,FALSE,&reply)==FALSE);
                assert(reply==99u);
                assert(helper_calls==1u); /* Do not choose another slot. */
                count++;
            }
        }
    }
    /* Existing manual fallback when the original player command is gone. */
    reset_case(0,0,0);
    res.bufferA[B_PLAYER][0]=0;
    reply=99;
    assert(SourceFirstWildSingleMove(B_PLAYER,FALSE,&reply)==FALSE);
    assert(reply==99u && helper_calls==0u);
    count++;
    printf("PUBLIC_PLAYER0_HOST_C: PASS %u behavior cases; no private game\n",count);
    return 0;
}
"""


def extract_exact_function():
    patch = PATCH.read_text(encoding="utf-8")
    if not patch.startswith("--- a/src/battle_controller_player.c\n"
                            "+++ b/src/battle_controller_player.c\n"):
        raise RuntimeError("unexpected public C patch identity")
    added = "\n".join(line[1:] for line in patch.splitlines()
                      if line.startswith("+") and not line.startswith("+++"))
    start = added.index("static bool32 SourceFirstWildSingleMove(")
    end = added.index("static void PlayerHandleChooseAction(", start)
    func = added[start:end]
    if func.count("static bool32 SourceFirstWildSingleMove(") != 1:
        raise RuntimeError("ambiguous real C function")
    if "preTargetMoves" not in func or "preTargetPP" not in func:
        raise RuntimeError("live proposal-wide pool guard missing")
    return func


def main():
    program = PRELUDE + "\n" + extract_exact_function() + "\n" + TESTS
    with tempfile.TemporaryDirectory(prefix="sg-public-host-c-") as td:
        src = Path(td) / "player0_proposal.c"
        exe = Path(td) / "player0_proposal"
        src.write_text(program, encoding="utf-8")
        subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-pedantic", "-O2", str(src), "-o", str(exe)],
                       check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == "__main__":
    main()
