# 16266 source review follow-up

Claude approved PR5 at8dfe5b8db4ffca6b6b76fcf738c18bce66b1d5ad at source level, with no blocking finding. The original-code provenance and local runtime/build evidence were not independently verified. Exact-head source CI41524924241 was rechecked before source merge. The ROM is unchanged by this follow-up; no automatic enablement or promotion follows.

## Status documentation and build boundary

STATUS_CODES.md separates capture reasons0-7 from diagnostic/wrapper statuses. The builder now explicitly rejects a cave shorter than the pinned5850-byte base cave; a future shrinking migration must deliberately handle the old tail. Five boundary cases exercise the guard without a ROM. Exact private-input16266 reproduction still passes for ROM/cave/IPS, so this changes no output artifact.

Review metadata now records PR5's source-level approval and the unverified private evidence. Earlier PR1 import and PR2 builder approvals did not cover the combined16264/16265 installed-hook/target-filter implementation. That earlier scope remains open deliberately.

## Request-flow observations

Four fresh processes on the same saved wild fixture log the pending word and request opcode at the initial observed hook and later hook/manual-menu entries. The initial hook is frame14240 with pending3, opcode19. This is the first observed hook in this saved fixture, not proof of the first turn of every battle.

| Scenario | First later hook frame | Pending word | Opcode |
|---|---|---|---|
| B-cancel and existing Fight re-entry | 14249 | 1 | 19 |
| After constructed late Disable rejection | 14258 | 1 | 19 |
| After constructed late Encore rejection | 14258 | 1 | 19 |
| After constructed repeat restriction rejection | 14259 | 1 | 19 |

Each process observes five later hook/menu entries; all actor0 observations have bit0 set and opcode19. Later hooks after confirmation also report pending3/opcode19. The three constructed-restriction cases observe native rejection return1 at frame14247 before the recovery hooks above. All four recover, wait60 frames without resubmission, accept ordinary A through the native validator and show PP decrement over1200 subsequent frames.

Cancel/re-entry uses ordinary buttons with no RAM mutations. Restriction states are explicitly constructed in disposable own-battler RAM. The subsequent rejection and recovery are native engine control flow; this is not a natural Disable/Encore encounter or a general freshness certificate.

The optional public `tools/probe_request_flow.py` takes explicit ROM/save/state/bridge/runtime paths, pins identities and checks debugger ABI fields. It records request snapshots without writing request fields, cursor or command buffers. Only the late-restriction fixtures mutate their documented own-battler fields. Public CI has none of those private inputs and does not execute the probe.

Original dispatcher/table/callback excerpts remain private. They can be supplied inline in a review handoff; no archive is required. Source review, private provenance review and replay reproduction remain distinct claims.
