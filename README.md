# PKMN-SG

Experimental player battle-selection patch source and development tracking for Pokémon SoulGold.

Latest local checkpoint: **16265**. The scorer provides an assisted-selection preview that requires confirmation. A scoped held-B override is implemented for actor 0 in ordinary wild singles. Automatic Smart AI dispatch remains unfinished (acceptance 0/20); this repository import does not promote an experimental ROM to Current.

## Contents

- `src/`: authored C/Thumb patch source from 16265, plus the unchanged 16264 held-B wrapper.
- `include/`: standalone scorer dependency headers.
- `tools/check_source.py`: public-file boundary and host C syntax checks.
- `docs/STATUS.md`: checkpoint, review scope, known gaps and next work.
- `docs/checkpoint.json`: identities of private local build artifacts for comparison.

Run `python3 tools/check_source.py` with Python 3 and a C compiler. CI performs source checks only. It does not run a game, reproduce emulator parity, or build a playable ROM.

## Private build environment

ROMs, saves, savestates, emulator/runtime binaries, extracted original-code windows and full review archives are excluded. Local ROM compilation still uses the existing private 16261/16263 checkpoint infrastructure. This initial public import is a source checkpoint, not a replacement for those recovery archives or a standalone reproducible ROM build. Migration of the private-input build interface is pending.

No repository-wide license is selected yet. Source provenance/licensing must be reviewed before choosing one. Adding this code to GitHub does not license third-party game material.
