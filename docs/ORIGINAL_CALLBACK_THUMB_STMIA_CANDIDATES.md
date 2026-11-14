# Original callback word changes: multiple writes by one Thumb-1 STMIA

PR79 observes original callback1 and callback2 32-bit pointer transitions,
and a decoded 16-bit STR immediate/register word store can be an UNVERIFIED
candidate CPU writer. A distinct valid Thumb-1 store also exists: STMIA
Rb!,{Rlist} (opcode 0xC000-0xC7FF). One CPU instruction can write multiple
consecutive aligned words. Treating that as a non-store loses some possible
original callback-writer evidence, while treating any callback transition
as native return would be unsafe.

The isolated verifier helper `observed_thumb_stmia_word_at` uses only
pre-step original r0..r7, 16-bit opcode and observed watcher address.
It decodes the ordered register list to the precise word address and Rt
value. It refuses non-STMIA/LDMIA, zero register-list, included base
register (writeback ambiguity), unaligned base/target, overflowed last
word, malformed pre-step registers, and wrong source. A newly separate
STMIA candidate counter and sorted writer-PC list prevents changing
PR79's existing scalar STR counts. A transition unaccounted for by
either instruction remains unattributed. Same-step watcher CPU identity
and live RAM chronology remain required.

Public fake tests cover one synthetic STMIA r4!,{r0,r1} writing both
callback pointers from one pre-step PC and adversarial invalid forms.
**This is not proof that original code uses STMIA**, not ROM opcode
attestation, not original battle result semantics, and not real
overworld callback execution. Candidate never becomes terminal or
production evidence from this decoder alone. Any real CPU trace needs
separately authorized exact modified-ROM provenance and original
same-run terminal replay.

No original Current ROM/save/savestate/modified ROM/private emulator
read, staged, hashed or executed; no manual fallback, foe/NPC AI,
auto-items/capture, protected branches or approved heads changed.
DRAFT/unmerged, new Claude exact-head review and Source CI required.
Formal native acceptance 0/20; production 0%; historical PP causes 0/2.
