# 16266 pending move-choice exclusions

Experimental assisted preview only. Human confirmation remains required. Automatic Smart AI acceptance stays 0/20; no Current promotion or phone trial requested.

## Problem and behavior

The preview previously accepted a player-like controller signature and move data even when that actor's pending-request bit was clear or its request opcode was unrelated to choosing a move. These inconsistent states were constructed at the existing game hook; they are not claimed as naturally occurring bugs.

The original player dispatcher at 0x080619D4 tests the actor bit in 0x02001D2C before reading buffer A's opcode. Its table at 0x084443EC maps opcode19 to the chooser at 0x08065A58 (Thumb pointer). The completion callback at 0x080625F8 clears that actor bit on the ordinary non-link path. This provides a negative request-phase exclusion; repeated uses of the same bit/opcode do not identify a unique choice epoch or prove player ownership.

## Shipped source change

- `snapshot.c`: after existing pointer bounds checks, reject capture with code7 if the actor bit is clear or buffer A opcode is not19. This runs during both existing captures, before allocation on the first capture.
- `diagnostic.c`: if the second capture specifically returns7, return status0 to the unchanged native chain. Do not install the preview chooser or write the cursor for a completed/replaced request. Other consistency failures retain the reviewed status5 behavior.
- `snapshot.h`: document code7; struct remains76 bytes.

Wrapper, scorer, safety preflight, target guard, resume and held-B sources are unchanged. The builder now pins private16265 as its input and exact16266 as its output. Only the scorer cave changes in the ROM; the hooks and held-B cave are preserved. The code still writes only the existing cursor byte on status4, plus its stack/result/scratch.

## Local validation — not independently reproduced

| Check | Result |
|---|---|
| Shipped C instruction cases | 614 passed; includes all256 opcodes for actor0 and actor2 pending-bit indexing controls |
| Between-capture consistency cases | 20 passed; pending clear/request replacement return0 without cursor write |
| Trainer safety/controller regression processes | 32 passed |
| Native preview/confirmation/change/cancel/idle cases | 8 passed |
| Native recovery processes | 4 passed |
| Override controls plus held-B+A confirmation | 4 passed |
| New native paired request cases | 12 processes: six per ROM,16265 vs16266 |
| Trainer paired trace | 1208 frames, identical RNG/pixels and hook frames; no hook spans a frame |
| Public-source private-input reproduction | Exact ROM, cave and IPS hashes reproduced |

Paired request observations:

| Constructed input at existing hook | 16265 status | 16266 status |
|---|---|---|
| Normal pending request, opcode19 | 4 | 4 |
| Actor0 bit absent (pending0 or pending2) | 4 | 2, no allocation |
| Opcode18 or20 | 4 | 2, no allocation |
| Actor0 bit present with additional actor bits | 4 | 4 |

The native paired probe stops at scorer return, checks both input/output buffers unchanged by the scorer and heap headers restored. Only its explicitly labeled request-field mutations are host RAM writes. Preview/recovery tests press ordinary buttons and execute the original native validator. The compiled tests use Unicorn TI925T with allocation/free stubs; mutation tests alter disposable inputs. None proves universal phase freshness, IRQ safety or target legality.

Trainer hook costs: baseline13052/14241/12876/13981 cycles; candidate13109/14298/12933/14038, an added57 at each hook. Wild first-call cost13889 cycles, same frame. Observed native first-call stack516 bytes; compiled maximum432 plus unchanged88-byte wrapper=520. These instruments are different and there is no known universal stack headroom.

The run recorded62 native processes (32 regressions +8 preview +4 recovery +4 overrides +12 request controls +2 traces), two initial compiled suites and a further compiled-suite run adding actor2 controls. Per-stage timestamps, elapsed times and return codes remain in private evidence. Public CI performs source checks only.

## Reproduction

The exact-input build is documented in BUILD.md. The new native paired probe can run in the existing private runtime with explicit paths:

```
LD_LIBRARY_PATH=/private/runtime:/private/compat python3 tools/probe_pending_choice.py --rom /private/SoulGold_16266.gba --save /private/Soulgold.sav --state /private/genuine_wild_hook.ss --bridge /private/mgba_bridge_16187.so --case pending0 --output build/pending0.json
```

The probe pins both accepted ROMs, save, state and bridge; it refuses an existing output. Its output is private evidence, not a public fixture. Complete prior replay infrastructure and original-ROM excerpts are excluded from this repository.

## Review request and remaining work

Review the pending-bit/opcode provenance, capture failure code, first-capture no-allocation path, second-capture status0 fallback, write surface and builder identities. No automatic adapter is requested. In particular, returning to the original chain does not certify what the original native auto path may subsequently do with a synthetic inconsistent request.

Positive ownership, a current choice epoch, complete move/target permissions, metadata, natural restrictions, varied encounters, IRQ and stack headroom remain open. This patch narrows phase eligibility; it does not close those contracts.
