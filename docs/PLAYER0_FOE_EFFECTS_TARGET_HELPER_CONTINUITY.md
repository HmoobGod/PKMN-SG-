# Player0 wild-single SOURCE LAB: foe effect continuity

## Gap after independently approved PR73 R2
The engine's first-stage target helper can modify foe-held items, secondary
passive abilities (innates), configured items, and volatile rule timers
(taunt, disable, encore, torment) before the source-LAB staging lease is
armed. Existing PR71/73 first-stage guards froze foe species, HP, status,
ability and types, and PR73 froze player volatile fields, but not these
remaining FOE fields. A helper-induced foe effect could otherwise become
the baseline for a newly staged player0 move; cross-stage changes could
also go unnoticed when the original ChooseMove request is received.

## Source-LAB-only fix
In an isolated new child of approved-but-unmerged PR73 R2, freeze foe
item/innate/items and four volatile timers ONCE before any first-stage
target helper; compare all after each helper and before skipping an
ineligible candidate or emitting Fight. Add the same foe properties to
the read-only lease snapshot captured at stage one and rechecked during
the original stage-two Move request. A mismatch denies automatic
selection and follows the original manual path, never selecting another
slot or touching foe controllers. The existing player, move pool, foe
identity and original ownership guards stay in place.

Public synthetic mutation tests enforce captures, all array elements,
rechecks, no rebasing, no disabled guards, stage-two lease equality and
no foe moves/PP/controller/AI or item/capture code. Source CI and the
pinned disposable GNU ARM compiler LAB run against PUBLIC source only.

No owner Current ROM/save/savestate/private original CPU or modified
game staged/read/hashed/executed. No original native action validated;
preserve protected branches and independently approved exact PR73.
Draft unmerged pending new independent Claude review. Native 0/20,
production 0%, historical unmatched PP classifications 0/2.
