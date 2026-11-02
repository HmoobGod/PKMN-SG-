# PKMN-SG

Experimental player battle-selection patch source and development tracking for Pokémon SoulGold.

Latest local checkpoint: **16266**. The scorer provides an assisted-selection preview that requires confirmation. Checkpoint 16266 excludes completed or non-move requests before scoring and suppresses the preview if that request is replaced during scoring. A scoped held-B override is implemented for actor 0 in ordinary wild singles. Automatic Smart AI dispatch remains unfinished (acceptance 0/20); this repository import does not promote an experimental ROM to Current.

## Contents

- `src/`: authored C/Thumb patch source from 16266, plus the unchanged 16264 held-B wrapper.
- `include/`: standalone scorer dependency headers.
- `tools/check_source.py`: public-file boundary and host C syntax checks.
- `docs/STATUS.md`: checkpoint, review scope, known gaps and next work.
- `docs/checkpoint.json`: identities of private local build artifacts for comparison.

Run `python3 tools/check_source.py` with Python 3 and a C compiler. CI performs source checks only. It does not run a game, reproduce emulator parity, or build a playable ROM.

## Private build environment

ROMs, saves, savestates, emulator/runtime binaries, extracted original-code windows and full review archives are excluded. `tools/build_private.py` reproduces the exact 16266 ROM, cave and IPS from the public source plus an explicitly supplied private 16265 base ROM. See `docs/BUILD.md`. Recovering that base ROM still requires the private archives; the repository does not build the base from an original commercial ROM. Local emulator replay infrastructure remains private.

No repository-wide license is selected yet. Source provenance/licensing must be reviewed before choosing one. Adding this code to GitHub does not license third-party game material.
