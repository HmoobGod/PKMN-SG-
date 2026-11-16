# R6-08 R3 — Exact single-PP marker regression for PR116

Source-only test addition, no native acceptance. Adds a generated double-PP same-epoch negative to pin `len(pp)==1` and verifies `candidate_UNVERIFIED` stays True for a single syntactically eligible candidate. Also verifies enemy PP does not alter player uniqueness, two separate epochs are not confused, and gameplay certifications remain false.

No private trace data, no source/game patch, no merge or release. Fresh independent Claude review required. Formal native acceptance 0/20.
