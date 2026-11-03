/* Host-only lab caller of the ORIGINAL isolated SoulGold source ranker.
 * Never linked to or invoked by the actual game. Input mask supplied from
 * historical manually-accepted test cases, NOT engine action authority. */
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include "ranker_workspace.h"
static int parse(const char *p, unsigned max, unsigned *out) {
 char *end=0;unsigned long v;
 if(!p||!*p||*p=='-'||*p=='+')return 0;
 v=strtoul(p,&end,10);if(!end||*end||v>max)return 0;
 *out=(unsigned)v;return 1;
}
/* Usage: shadow_ranker <previously accepted slots mask 1..3> <id pp power accuracy targetmode> repeated four times */
int main(int argc,char**argv){
 if(argc!=22){fprintf(stderr,"FAIL: argc (expect mask + four 5-field slots)\n");return 2;}
 unsigned accepted; if(!parse(argv[1],3,&accepted)||!accepted)return 2;
 SG_View v={0};SG_PublicBattleObservation o={0};SG_Proposal p={0};
 v.battle_token=o.battle_token=1;v.turn_token=o.turn_token=1;v.choice_token=o.choice_token=1;
 v.battle_mode_flags=4;v.controller=1;v.phase=2;v.actor=o.actor=0;
 v.battler_count=2;v.supported_mode=true;
 o.active[0].role=SG_PUBLIC_SELF;o.active[1].role=SG_PUBLIC_FOE;
 for(int m=0;m<4;m++){
  unsigned id,pp,power,accuracy,mode;
  /* The inputs are a read-only host reconstruction of OWN visible moves.
   * The two sampled original manually accepted slots are not future permission. */
  char *const *f=argv+2+5*m;
  if(!parse(f[0],935,&id)||!parse(f[1],99,&pp)||!parse(f[2],999,&power)||
     !parse(f[3],100,&accuracy)||!parse(f[4],255,&mode))return 2;
  /* ROM target mode is >= 1; status moves have zero power. Attested mask
     limited to exactly the two manual R9 accepted slots. No hidden foe data. */
  if(!(accepted&(1u<<m)))continue;
  if(!id||!pp||!power||(mode!=1&&mode!=6))return 3;
  o.moves[m]=(SG_PublicMove){.known_damaging_move=true,
     .displayed_base_power=(uint16_t)power,.displayed_accuracy=(uint8_t)accuracy,
     .known_always_hits=(accuracy==0)};
  v.permitted_move_mask|=(uint8_t)(1u<<m);
  v.permitted_targets[m]=(uint8_t)(1u<<1);
 }
 size_t count=sg_rank_damage_best(&v,&o,&p);
 if(count==0||p.action!=SG_USE_MOVE||p.actor!=0||p.target!=1||p.move_slot>3||
    !(accepted&(1u<<p.move_slot))){fprintf(stderr,"NO SHADOW PROPOSAL\n");return 4;}
 printf("SHADOW_ONLY slot=%u target=%u candidates=%zu; NO ENGINE PERMISSION\n",
   (unsigned)p.move_slot,(unsigned)p.target,count);
 return 0;
}