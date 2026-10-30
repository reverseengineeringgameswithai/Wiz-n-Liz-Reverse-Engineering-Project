---
id: SESSION-2026-10-05-032
type: session
status: completed
---
# Retain the miss-only collision service

Started clean at `94611678dfa49a1edaf7691ca3ea00a949d06abf` on
`work/airborne-update`, with an empty index and no merge/rebase/cherry-pick/revert
operation. This follows the completed 7A88 checkpoint in session 031; the user
asked to continue autonomously onto the next task. Read actual AGENTS/CLAUDE,
entry points, current handoff/task, brief/workflow, pool/dispatch/presentation,
reference harness and external worker ownership/trace instructions. No existing
user changes. Authorized local implementation, tests, vault synchronization and
reviewed commit; no push/upload. No subagents or external installation edits.

Intended checkpoint: `Reconstruct collision misses in the retained mixed pool`.

## Delivered scope

`src/sim/collision_probe.*` implements AC5E's control overlap helper and the
partial 78EE miss path. Unsigned inclusive comparisons follow word arithmetic,
including threshold overflow and X-only masking. P1 control tracking is selected
first; only after a miss does nonzero FF33E2 select P2. Hit7910 rejects before
any hit instructions execute. Native output is typed state/boolean; no embedded
ROM, interpreter or emulated CPU enters the native targets.

Slot 63 is now retained `CollisionProbe` state (pool kind 7). Its fixed RTS handler
follows presentation and precedes the service. P1 tracking comes from the existing
native wrapper after actor work, including the FF80 sentinel. The thirteen-field
pool header adds mask/gate/optional secondary coordinates once; later rows remain
physical input only. Missing consumed input, hits and callbacks roll back the
entire session, including earlier allocations, RNG, presentation and P1 work.
Seven external reservations remain, including inactive occupied slots 52/66.

The movie audits 68 writes to FF06D2/FF06D4 from F91A/F924 (write callback next
PCs F91E/F928), with owner, width, order, value and continuity checks. FF13AE=03FF,
FF33E2=0 and P2 tracking=0 have no writers, including transients. Native P2
scheduling and configuration initialization remain unimplemented. Component
checks can supply P2 directly; this is not evidence for a native second player.
The prior FF31xx/table input contract is preserved.

See [[03_Reverse_Engineering/findings/FIND-0032-collision-miss]], `re/collision_step.json`,
`re/collision_validation.json`, `tools/genesis_collision_evidence.py` and
`tools/genesis_mixed_session.py` for exact fields, hashes and boundaries.

## Validation

- **478,345 original/native cases per debug/release/sanitize**: 341,497 overlap,
  66,376 service and 70,472 scheduled. Exhaustive word domains for distances,
  extents, mask and gate; edge products, deterministic random inputs, repetitions,
  all presentation modes and explicit unsupported boundaries. All 28 new
  instructions execute. No native/reference semantic mismatch.
- P1/P2 hit cases stop before 7910 in the original and reject in native code.
  Missing consumed P2 and invoked callback also reject. Reference reads/writes
  and executable ranges are restricted; original RAM remains unchanged except
  allowed scheduled presentation/stack writes.
- Primary hash/decode and 95-instruction closed graph pass; four selected GNU
  checks corroborate ADD.W, CMP.W, BHI and RTS. Other opcodes rely on primary
  decode and actual restricted execution; no blanket GNU validation claim.
- Final ordinary capture: `local/generated/mixed-session/run-iog_ybnw/`, plus
  independent unhooked replay. Final native comparisons: debug `run-iog_ybnw`, release `run-4mb26up0`, sanitize `run-c31rj0gu`.
  **34 collision updates / 395 ordered events** per preset match, alongside
  34 P1/emitter calls, 136 trail, twelve reversal, 136 private and 34 table
  updates; nine allocations/releases, complete free order/RNG, 34 banners,
  two sounds. Native output SHA-256:
  `d8c821e24c4c828b4e0b8ff2a90a3ad59dd4bc1f49a4e00a88d2bd55862e178c`.
- Helper boundaries show **32 X misses and two Y-only misses**. Caller stacks,
  fixed A5 identities, comparison operands and return Z match. Zero memory edits,
  drops or overflow; 9,973 routine / 52,895 native events, 1,840 managed / 271
  reserved / 27 free-stack writes. The exposed-state endpoint excludes hidden
  devices; no whole-frame/render/audio parity claim follows.
- **196 Python tests, zero skips; 44/44 CTests per preset**. Authored tests check
  inclusive/wrapped arithmetic, masked X, full-word gates, callback/primary/P2
  short-circuit boundaries, actual tracked coordinates, sentinel and combined
  rollback after release, table motion, emitter allocation/RNG, P1 movement,
  banner scratch and reversal allocation. Final builds have no warnings.
- Table **406,634**, private **277,232**, trail **209,082**, reversal **203,586**
  comparisons per preset pass. The table comparator also reruns its 131,422
  research writer-fragment cases; these remain outside native parent mappings.
  Older 390-call P1 fixtures pass per preset, retaining output hash
  `8c738e9a85ad89630327f17f9a973add730f96a7ee29555ce55267a51558577b`.
- Eight further sanitized corpora pass: input 1,024; banner 66,880; presentation
  347,320; actor 152,093; dispatch 138,149; airborne 415,940; movement 282,233;
  terrain 614,436. Project-owned restricted Musashi rebuilt offline.
- Fresh thirteen-corpus instruction union **1,185**, or **1,194** with the nine
  research writer instructions. Cumulative **1,543** includes historical corpora
  not rerun. AC5E adds one bounded mapping, 78EE one partial mapping: **106 bounded
  plus two partial / 117 indexed**. All 96 bytes were preclassified, leaving
  26,257 classified / 1,022,319 unclassified ROM bytes unchanged.

## Failed attempt and skips

The initial fresh capture `run-jild2s89` failed a validator assumption that all
ordinary misses ended after X. It actually had two Y-only misses. Native arithmetic
already handled both; corrected the validator to enforce the actual branch and
register arithmetic, checked the saved evidence diagnostically, then performed a
new hooked capture and independent unhooked replay with the final validator.
Both capture attempts used the unchanged ordinary recording, without edits.
An early debug comparison preceded additional rollback tests; final native
builds and all three component comparisons were rerun afterward.

Not rerun: actions/transition/coasting/tally/palette/bonus/exit-tally/score component
corpora, other historical/controlled captures, whole-movie survey and SDL3
availability. No new controlled full-machine edit was needed. Nonzero secondary
service evidence is synthetic restricted original execution, not ordinary gameplay
or a reconstructed P2 scheduler. callback79B6 and collision-hit7910 remain
explicitly unsupported; game boot, world services, rendering/audio are unfinished.

## Reproduction and handoff

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py configure --preset debug
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py collision-compare --preset debug
python3 -B tools/project.py mixed-session local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py mixed-session local/generated/capture-qb2htq3j/recording.json --preset release --fixture local/generated/mixed-session/run-iog_ybnw/report.json
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py mixed-session-probe
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Build/test/component/movie comparisons cover all three presets. Exact reports,
log hashes, provenance, research scans, failed attempt and preservation records
are indexed in `re/collision_validation.json`; bulk research remains ignored.

Next bounded task: **replace seven return-only reservations with typed retained
presentation/occupancy state**, including five active slots 58–62 and inactive
occupied slots 52/66. Audit their fields, activity, callbacks and writes, retaining
allocation order and explicit unknown-selector rejection. Keep hit7910 and
callback79B6 unsupported. TASK-0010 remains **in progress**; native playability
remains **none**. See [[01_Project/NEXT_ACTIONS]].

Final preservation checks ROM/BK2/recording, worker, frozen build manifest,
104 runtime binaries and 59 manifest-recorded sources. Owned workers are closed.
No GUI, Sonic19420, WL3PC or external source/runtime changes; no push/upload.
The pass closes with synchronized vault, whitespace/hygiene checks and explicitly
staged review before the local checkpoint commit.
