# Engine controller-assignment witness — 16266

This is a local evidence follow-up, not a ROM patch or automatic adapter. It uses the restored, hash-verified16266 checkpoint. No shipped C/Thumb changes or user ROM/save writes.

## New native observations

Two separate fresh mGBA processes start from the earlier field fixture, before controller initialization. The ordinary run applies only ordinary directional inputs. The comparison uses the existing bridge's explicit partner/double initialization fixture; it does not write controller tables directly. The partner run is constructed, not an authentic story-partner encounter.

| Stage | Ordinary fixture | Constructed partner fixture |
|---|---|---|
| Constructor entry | frame14045, flags4 | frame14045, flags0x00400005 |
| Controller assignments at constructor end | count2; actor0 installer0x08063D25, actor1 installer0x080619A1 | count4; actor0 installer0x08063D25, actor2 installer0x0806645D, actors1/3 opponent installer |
| Installers execute through original per-frame dispatcher | frame14063, LR0x0808CBFB | frame14072, LR0x0808CBFB |
| Actor0 after installer | kind1, completion0x080625F9, run0x080619D5 | same actor0 signature |
| Actor2 after installer | not present | kind2, completion0x08065E39, run0x08065B61 |
| First observed scorer hook after this initialization | frame14309, actor in r4=0, flags4 | no scorer hook in the observed window |

In the ordinary run, breakpoints at0x0806AD46 and0x0806AD5E bracket the original controller assignment: run slots change from the prior initialization callback to the two installer pointers before either installer executes. The constructor-end observation agrees. This ties the later kind1 signature to an actual engine-selected installer in this fixture; it is stronger evidence than reading a preexisting signature alone.

This is the first scorer hook after the recorded initialization in this input sequence. It is not proof of first-turn behavior in every natural encounter, and it is not an independent reproduction of the earlier frame14240 fixture. The endpoint is determined by the stated inputs; no archive timing comparison is claimed.

## Original-instruction installer checks

An optional Unicorn TI925T test executes each of the three original leaf installers for actors0,1,2,3: **12 cases passed**. Full EWRAM and IWRAM are initialized with sentinels and compared after execution. All tested SP, LR and r4-r11 values are preserved. The exact CPU stores match:

| Installer | Writes |
|---|---|
| 0x08063D24, kind1 | kind byte; completion table; run table; clears bytes0x02001E80 and0x02001E6A |
| 0x080619A0, kind3 | kind byte; completion table; run table |
| 0x0806645C, kind2 | kind byte; completion table; run table |

The two extra kind1 clears are side effects, not query results. **Do not invoke an installer as a supposedly read-only ownership check.** No extra installer or restriction call was injected into either native process. The isolated tests use constructed RAM and do not prove native initialization behavior by themselves.

## Reproduction

The public optional tools take explicit private inputs; they contain no original byte dump or fixture payload.

```
python3 tools/check_controller_install.py --rom /private/SoulGold_16266.gba --output build/controller_install/compiled.json
LD_LIBRARY_PATH=/private/runtime:/private/compat python3 tools/probe_controller_install.py --rom /private/SoulGold_16266.gba --save /private/Soulgold.sav --state /private/route37_before_talk.ss --bridge /private/mgba_bridge_16187.so --runtime /private/libmgba.so.0.10 --output build/controller_install/ordinary.json
```

Add `--partner-fixture` with a separate output for the constructed comparison. The instruction test requires Unicorn2.1.4; native probe pins ROM, save, state, bridge and runtime hashes and validates the private debugger ABI fields before installing its callbacks. Reports include source hashes and actual start/elapsed times. Public CI does not have private inputs and does not run these tests.

## What remains open

This witnesses engine assignment in two scoped fixtures. It is not general party ownership, authenticated multiplayer identity, partner certification, a current choice-epoch token or complete move/target authority. In particular, actor0 has the same kind1 signature in the partner fixture, so kind/completion alone cannot exclude that battle context. Existing exact-context exclusions remain necessary.

The next adapter work must bind a recommendation to the current native request and preserve exactly-once submission/rejection recovery. The current preview keeps results on its call stack and requires human confirmation. No automatic dispatch, NPC-partner control, enemy AI change, Current promotion or phone trial follows; automatic acceptance remains0/20.

## Local receipt identities

These hashes identify the retained local reports, not independent reproduction.

| Report | SHA256 |
|---|---|
| ordinary.json | a03f600601f95c220b14031640619130ff8f7cc4ed71bf9cfd79478b4b6c6275 |
| partner.json | 75def3a370b64c1017def138475a05c94060bc2be8a50e819fa52dc42bf824a1 |
| compiled.json | 37c93747552f305e17082621567f5bbd6e8743f54db57dbedb4b43d47d89ddef |
