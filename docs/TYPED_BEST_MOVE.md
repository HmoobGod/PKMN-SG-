# Type-aware low-memory best-move scorer

2026-11-24 Central. Base e1fe87d449fd78e3afd832d3497ae66ac7bc1859. Gameplay source improvement, not a native install.

The existing full-list ranker already handles verified type effectiveness and type immunity, but its low-memory best-only projection deliberately rejects type modes. Add a separate opt-in best-only entry point that shares the existing type calculation and stable score ordering. Legacy diagnostic callers keep their original contract. No native caller or game file is changed.

Community reference: supplied soulgold-master source src/battle_ai_main.c (AI_CheckBadMove, AI_TryToFaint, AI_CalcDamage call at line 794) uses battle effectiveness and damage in AI decisions. Supplied Pokemon HnS src/battle_controller_player.c has a Battle Palace automatic move path; this is background context, not proof of compatibility with Current. No community code copied; reuse our existing scorer. Do not directly invoke enemy AI or assume public source addresses match Current.

Tests in tools/test_typed_best.c compare the real full and compact ranker for type effectiveness, immunity, legal masks, unknown values, stable ties and bound identity. Existing ordinary source CI runs the test. Runtime and exact-head CI results remain pending until observed. Native integration, R5 and Auto-Switch2 holds and formal acceptance unchanged. No cloud compatibility work resumed.
