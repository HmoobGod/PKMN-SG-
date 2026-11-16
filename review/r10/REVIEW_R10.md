# R10 independent review packet — source/test/security only

- Parent: previously approved PR124 exact head, not review-pending PR125/PR146/R8 siblings.
- New files: one pure-Python original CPU-store lineage verifier, one generated-only test suite, this note and README, one dedicated CI workflow.
- Generated fixtures **only** in CI; no private original-ROM game files or observations are uploaded.
- Independent failure cases include missing source, missing player copy, opponent copy confusion, wrong actor0 reply, duplicate PP writer, wrong PP byte PC/width, broken order, wrong header, bad 40-byte payload, wrong move/max PP, next-request drift and false native promotion.
- Local check: 53 fake-only tests passed; 10 targeted scratch mutants caught. Private evaluation (outside GitHub/Drive) found 3 original-ROM request→copy→reply→PP **UNVERIFIED** candidates; no guest modifications and no integrated patch acceptance.
- Need independent exact-head Claude verdict. Review any integer/buffer bounds, false-positive episode grouping, source→copy event ordering, nonplayer exclusion and provenance trust boundaries. Real renderer and mGBA host pointers remain private/unaudited by this PR.
- No merge/release/installation, acceptance stays 0/20.
