# Development status — 16266

**Latest native encounter milestone 16266R11 (November 3, 2026):** Two independent NORMAL-SAVE fresh wild-single encounters (battle flags0x4; count2) were observed without midbattle savestate, and two reloadable private pre-controller raw mGBA states were captured before original controller initialization. Each replays independently through original actor0 player installer and actor1 opponent installer, original 44-byte actor0 opcode19 buffer-A copy with 44 actual byte-store instructions, exact own live move/request correspondence [325,157,92,269] and positive PP, and original pending-bit activation 23 guest steps later. A separate roaming Entei mode (flags0x404) was explicitly excluded. Two private pre-controller .ss plus reports stay outside public repo. No automatic move, enemy/NPC partner AI edits or Current ROM/save writes; native in-ROM auto acceptance remains0/20. See [R11_FRESH_WILD_ENGINE_BOUNDARY.md](R11_FRESH_WILD_ENGINE_BOUNDARY.md).


**Latest host-selected Smart AI trial, 16266R10 (November 3, 2026):** The repository's **exact unchanged isolated Smart AI C ranker** was compiled as a separate host executable (its nine source/header Git blobs verified against main). In two independent disposable Linux mGBA wild-single replays pinned to the R9 ROM/save/savestate, the host read only actor0 own four moves/PP and exact ROM metadata, passed the TWO original manually accepted slots as a **historical test-only mask**, and invoked the real scorer. With both historical slots present the scorer proposed slot1/move157; with slot1 excluded by the artificial historical test mask it proposed slot0/move325. The host scripted ordinary original move-menu buttons, and the native emitter/reply/original restriction result0 and slot/move/target commit instruction chain passed for **both host-selected trials**. This is NOT automatic AI code running inside the ROM; no game hook or native command injection exists; no player owner/epoch or complete legality certification. Host-selected test moves=2/2; **in-ROM native auto acceptance=0/20**; experimental game ROM remains 16266. Tests: 10 public unit methods PASS plus private two replay verifications; exact Current ROM/save remain unchanged. See [R10_HOST_SHADOW_MENU.md](R10_HOST_SHADOW_MENU.md).


**Latest native manual acceptance milestone, 16266R9 (November 3, 2026):** Two separate **original-human-input** disposable alternative mGBA wild-single replays continue from R8's verified actor0 completed buffer-A copy and pending gate. Original actor0 manual A selection: slot1/move157 (frame14375), original native restriction returns0, then slot/move/target commits (frame14376). Human LEFT then A: slot0/move325 (frame14377), original native restriction returns0, then three commits (frame14378). For each: original emitter subcommand10 payload257/256 respectively, exact six-byte matching reply, pending clears at completion, same original validator/consumer path. This confirms two **MANUAL** accepted move choices only, not complete target legality, original player authorization, auto move, trainer doubles or Android. New research tooling/negative tests in [R9_NATIVE_MANUAL_LEGALITY.md](R9_NATIVE_MANUAL_LEGALITY.md). Original ROM/save untouched, source-only tooling change. Automatic-battle acceptance **0/20**; experimental gameplay ROM still **16266**.


**Latest native context milestone, 16266R8 (November 3, 2026):** Replayed the R7 confirmed original actor0 44-byte request and separately sampled original engine player/opponent controller classes (1/3), completion/run callbacks, battle mode4/count2, positions0/1, public present mask, own four move IDs and PP and own-only Disable/Encore/repeat/cache fields at *both* postcopy and the original pending transition 23 guest steps later. All fields stayed constant except pending word0->1; no hidden foe field reads. One fixture and alternative host with savestate version warning; no contemporaneous installer execution, exclusive ownership certificate or automatic legality. **R4 lease reference model corrected:** copy only STAGES; paired original pending opens model; synthetic C optimized/UBSan each104 assertions. Source-only; native automatic acceptance 0/20. See [R8_PENDING_OWNER_CONTEXT.md](R8_PENDING_OWNER_CONTEXT.md).


**Latest source/runtime milestone, 16266R7 (November 3, 2026):** A third-party *alternative Linux* mGBA test executable bundled in the existing user source archive was loaded as a temporary host-only library, enabling **actual game emulation** of pinned experimental16266 ROM, save, and battle state without altering the ROM. With Thumb savestate prefetch repaired (host workaround; savestate version warning persists), native human-confirmed emitter payload257 at frame14246 matched historic confirm, and a new actor0 opcode19 **44-byte original buffer-A copy** at frame14369 was observed through 44 real byte-store instructions, byte-identical before/after buffers. Its request SHA matches the old independent confirm record. The pending flag was set **23 guest instructions after postloop**, not during copy. This is ONE read-only runtime witness, not an approved automatic battle or complete player ownership/legal move proof. No gameplay source changes; automatic acceptance remains **0/20**, no ROM promotion. See [R7_ALTERNATE_MGBA_LIVE_COPY.md](R7_ALTERNATE_MGBA_LIVE_COPY.md).


**Latest R6 research-only source update (November 3, 2026):** Added an optional, SHA-pinned native debugger observer at original copier entry 0x0806B370, byte-store PC 0x0806B3BE, and static post-loop candidate 0x0806B3C6. Its offline verifier demands 44 ordered store-PC observations and identical final source/destination bytes, and cannot grant player ownership, move legality, or automatic commands. Public synthetic tests: four unittest methods and 37 negative mutations pass. No private mGBA debugger runtime is present; no new post-copy native trace, game ROM patch, acceptance pass, Android certification or Current promotion. See [R6_COMPLETED_COPY_PROBE.md](R6_COMPLETED_COPY_PROBE.md).


**Latest source-only follow-up, 16266R5 (November 3, 2026):** Native copier entry0x0806B370 and original buffer-A post-loop candidate0x0806B3C6 are distinct. The prior eleven observed entries are not proven completed writes. Static Current/experimental16266 branch/loop structure and sixteen private negative perturbations checked; historic six-report replay now opens zero leases; no new native emulator run, source gameplay patch, or auto-enable. See [R5_COPY_BOUNDARY.md](R5_COPY_BOUNDARY.md).

Local baseline imported November 2, 2026. Source-only GitHub migration; original playable ROM and save remain separate.

## Verified locally before import

16265 adds a negative raw-target-mode filter (1/6) to the assisted preview and preserves 16264 held-B bytes. Local results: 348 shipped-C cases, 18 consistency cases, 32 trainer/controller regressions, native preview/override checks, and paired 1208-frame trainer parity. These are historical local results; public CI does not reproduce them.

16263's eligibility refactor received independent static review with no defect found. The combined 16264/16265 code review remains pending. No automatic enablement, Current promotion or phone trial approval.

## Current behavior and constraints

16266 adds pending-request exclusions to both captures. A missing actor pending bit or a request opcode other than19 rejects the first capture before allocation. If this specific phase check fails after scoring, status0 chains the native path without writing the cursor or installing the preview chooser. Other failed rechecks retain the reviewed status5 manual fallback. This is a negative phase check, not ownership or an epoch token. Claude approved the exact PR5 source change at8dfe5b8db4ffca6b6b76fcf738c18bce66b1d5ad with no blocking finding. Original dispatcher provenance and runtime/build claims remain unverified by that reviewer.

- Human confirmation is required; a recommendation is not action authority.
- Supported held-B override: actor 0, player-controller signature, flags 4/count 2 wild context only.
- Unsupported raw target modes are excluded conservatively, potentially prompting manual choice for legal moves.
- A clear restriction-cache bit grants no permission. Cache freshness is unproven for natural restrictions.
- Native submission, restriction-return and later commit writes are distinct stages. A zero restriction return is not complete target/ownership authorization.
- Preserve manual/default-disabled behavior, the existing player save, enemy/NPC-partner AI, and no automatic items/capture/Master Ball.

## Next work

1. Finish combined 16264/16265 independent source review.
2. Effect-specific target resolver overrides now have isolated original-instruction coverage (see NATIVE_TARGET_CONTRACT.md). Native target selection, controller/session ownership and automatic submission remain unproven.
3. Private-input build migration implemented: tools/build_private.py reproduces the exact16266 hashes from a SHA-pinned private16265 ROM. Native replay migration and reconstruction of that base remain pending.
4. Expand natural encounters, settings-screen default tests and metadata/UI checks; stack headroom, IRQ, Android/speed-up and cave reference closure remain open.

The historical source checklist being complete does not mean in-game Smart AI integration is complete. Overall percentage estimates are retired; track these milestones and automatic acceptance 0/20.

## Import review and build migration

PR1 at0a5648b378e25b412c817192ea597b34563cecce received source-import approval with no blocker (reviewer inspected the archive, did not independently verify GitHub identity/CI). GitHub CI was independently checked before merging. That approval does not certify installed hooks, native replay or automatic enablement.

checkpoint.json base_sha256 is now the private16265 ROM (deef0016...). The earlier PR2 builder consumed16264 (db9142...). Both bases inherit the held-B hooks and safety patch. The current builder replaces only the scorer cave; exact local16266 reproduction passed for ROM, cave and IPS.

## Review scope clarification

PR5 source-level phase-guard review is approved; exact-head CI was rechecked before source merge. Capture and diagnostic return meanings are in STATUS_CODES.md. PR1 approved the source import, PR2 the builder/boundary tooling, and PR5 the phase-guard diff. Those scopes do not constitute the earlier combined16264/16265 installed-hook and target-filter implementation review. That earlier scope remains open deliberately; it is not resolved by relabeling it. No automatic enablement, ownership or choice-epoch claim is approved.

## Provenance and assignment follow-up

Claude independently decoded the supplied dispatcher/table/non-link completion excerpts and confirmed the pending-bit/opcode semantics. The binding of those excerpts to the ROM hash and runtime replays was not independently verified. PR6 documentation/tooling/tests approval received at34ac04bf. New local controller-assignment evidence is in CONTROLLER_ASSIGNMENT.md: two fresh native processes plus12 isolated installer cases. This narrows the assignment question for those fixtures; general ownership and a current choice epoch remain open. No new shipped code or automatic enablement.


## Request lifetime follow-up

CHOICE_LIFECYCLE.md records six fresh human-input/constructed-restriction processes:11 submissions each paired with one reply copy and completion; native results6accepted/4rejected/1cancelled. Recovery can issue an identical44-byte request, so payload equality is not an epoch ID. Cached restrictions remain zero at first recovery in the four constructed rejection cases. Effective choice-item/trait lock classification remains the next permission gap; no unconditional stored-lock filter or extra validator call is introduced. No shipped source/ROM change or automatic enablement.
