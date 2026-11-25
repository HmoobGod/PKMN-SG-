# Native source type-multiplier compatibility

2026-11-24 Central. Direct child of PR154 2a04ee87e1744ace722fbaac53e06bd1cadbf910. Source-only gameplay scoring change.

Reopened supplied soulgold-master.zip, exact source file SHA-256:
- include/fpmath.h 1f1d7522f2667cef0fe00105b34f6121aab317d91add656ac80eebfe822da51c, lines 5 and 15: engine uq4_12_t is u32, one is 4096.
- src/battle_util.c 928d19aa0d54098cd950a793b3ce4c0dd34546ea25c54b4fc1fd3253928fac5d, lines 10638–10664: GetRawTypeModifierAgainstBattler combines three distinct types. Three half/double factors can yield 1/8x or 8x. Legacy quarter matrix cannot represent 1/8 and rejects 8x.
- Same file lines 10667–10700 and 11047–11088: CalcTypeEffectivenessMultiplier calls TryTransmuteMoveType, which can mark party state, use RNG and record an ability. Do not use this full calculator as an unconditionally read-only observation provider. CalcVisualTypeEffectivenessMultiplier also temporarily writes defender types (lines 11093–11122).
- GetTypeModifier at lines 11212–11217 performs type-chart lookup with inverse-battle handling. This is a candidate read-only building block with authenticated public typing, not a guarantee of complete live move legality or actual damage.

Reused PR154's existing ranker and controller. Opt-in bounded raw UQ4.12 matrix accepts verified type-only values up to 8x without rounding away 1/8x. Checked raw-u32 ingestion rejects out-of-range values before narrowing; legacy quarter inputs retain identical scoring and default behavior. No full engine damage/ability calls or hidden foe observations. The source struct layout changes; old private build identities and installed ABI are not reproduced by this branch. Do not use it to regenerate pinned 16266 binaries. Rebuild and certify separately if later authorized. Existing R7 controller, guard, approval flags and native holds untouched.

Tests exercise both real scorer entry points and existing R7 Fight-to-Move planner with raw fixed-point values, immunity, max product arithmetic, invalid narrowing, conflicting formats, absent cells, legal masks, and legacy parity. Native observation provenance remains missing, especially safe public type and move classification plus authenticated original request lifecycle. No ROM/save access, execution, release, cloud compatibility work or native certification. Formal acceptance 0/20.

Next: do not keep expanding scorer heuristics. Find the exact already-developed Current-compatible observation provider and manual deferral handoff; if no authenticated mapping exists, request a narrowly authorized native evidence step rather than inventing an adapter.
