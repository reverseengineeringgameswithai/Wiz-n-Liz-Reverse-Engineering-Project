---
id: SESSION-2026-10-05-029
type: session
status: completed
---
# Integrate P1 and the ordered mixed object pool

Started clean at `b24cabf3fd3801bf2c0593eeee79149e9bd2e5f4` on `work/airborne-update`, with an empty index and no
pending Git operation. Read actual entry points, brief/workflow, current status,
next/task and session/finding 028, native session/trail/reversal code and the
external debugger capability/hook semantics. The user authorized the next
ordered shared-pool integration. No new movie or GUI action needed.

Intended checkpoint: `Integrate P1 and effects with an ordered mixed object pool`.

## Implemented result

`src/sim/mixed_pool.*` adds typed mixed storage and a retained P1 session.
Initial live trail particles, emitter/RNG, reversal objects, ordered logical slots
and the full free stack persist. Only physical held-button masks follow the
initial seed. Owner position and capacity come from native state, replacing the
previous trail comparator's per-call reference feeds. Exact scope and private
reservation audit: [[03_Reverse_Engineering/findings/FIND-0029-mixed-object-pool]].

Births in earlier slots wait; later slots execute immediately. Earlier releases
can be reallocated within the same pass without rewinding the iterator. Shared
identities include generations; stale handles reject. Native capacity is supplied
by the initial vector/free stack, bounded to 4,096 for safety. The fixture's 68
slots are not a permanent hardware limit. All actor, pool, RNG, ordinal and
request changes roll back on failure, including failures after P1 allocation.

Thirteen explicit external reservations retain occupancy only. Full original
execution continues normally; write/selector/caller/stack guards establish their
noninterference in this exact interval. Their private Y, table motion and
presentation are not reconstructed or compared. Collision service 78EE always
misses; 7910, 79B6 callback, new allocator clients or occupancy changes reject.
This is a bounded shared-allocation projection, not whole-world/frame parity.

## Fresh evidence and tests

- Final ordinary movie `[1066,1100)` capture and independent unhooked replay:
  `local/generated/mixed-session/run-vt8017re/`. Exposed-state endpoints agree;
  no edits, dropped events or overflow. Owned workers closed afterward.
- Every native preset freshly compares **34 P1/emitter invocations, 136 trail
  particle updates, twelve reversal updates, nine allocations/nine releases,
  191 ordered pool events, 34 banners and two sound requests**. Four initial live
  particles contribute 39 updates; new particles contribute 97.
- Captured cadence: 102 conversions, 136 polls, 34 inactive timers, 214 scratch
  writes, 9,767 routine events and 52,895 native events. Audited writes: 1,205
  managed, 906 reserved, 27 free-stack. All nine original allocations have known
  callers, and full free-stack order matches throughout.
- Three final native fixture comparisons reuse one final capture; they are not
  three fresh original replays. Earlier discovery capture
  `local/generated/mixed-pool-research/capture-fn228h1v/` also matches an independent
  unhooked endpoint and supported the implementation audit.
- **190 Python tests, zero skips; 38/38 CTests per debug/release/sanitize.**
  Authored mixed-pool/session tests include both facings, live initial particles,
  nontrivial free order, generation reuse, earlier/later births, full rollback,
  capacity/work/owner/callback failures and malformed evidence/transport.
- Trail **209,082** and reversal **203,586** original/native cases pass per preset.
  Eight further sanitized corpora pass: input 1,024; banner 66,880; presentation
  347,320; actor 152,093; dispatch 138,149; airborne 415,940; movement 282,233;
  terrain 614,436. Fresh restricted union 1,118; cumulative 1,467 partly historical.
- Previous P1/reversal saved original fixture freshly matches **390 calls per
  preset**, with unchanged output. No extra original replay is claimed for it.
- Static audit: five ranges / 260 bytes / 67 instructions and 48 data bytes;
  primary decode, hashes, closed graph with explicit unsupported exit, and five
  GNU checks pass. This is context evidence, not new native function coverage.

No native/reference semantic mismatch. The first native build warned about
misleading indentation in the transport; it was corrected before the final
builds/tests, which have no warnings. No reference runtime or project Musashi
harness rebuild was needed. Not rerun: eight other component corpora (actions,
transition, coasting, tally, palette, bonus, exit tally, score), other old or
controlled captures, whole-movie survey, SDL3 availability.

## Reproduction and handoff

```sh
python3 -B tools/project.py mixed-session-probe
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py mixed-session local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py mixed-session local/generated/capture-qb2htq3j/recording.json --preset release --fixture local/generated/mixed-session/run-vt8017re/report.json
python3 -B tools/project.py trail-compare --preset debug
python3 -B tools/project.py reversal-compare --rom --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Repeat build/test/component comparisons for each preset. Fixture reuse verifies
source/input/artifact hashes and identities before revalidating raw chunks and
running the current native binary. It does not invoke the original emulator.
Reports and source hashes: `re/mixed_session_validation.json`. Research logs,
static disassembly, states and captures remain ignored under `local/generated/`.

Next bounded task: reconstruct **7808 and 7CA4** as typed private-object updates,
including their preceding presentation phase and required FF31xx inputs; validate
both branch directions with original execution, then integrate these two kinds
into the mixed session. Keep 7A88 table motion and 78EE collision hit explicit
until separately implemented. Preserve the established free-stack/RNG/P1 audit.

TASK-0010 remains in progress. No added native function mappings: **102 bounded
plus one partial / 112 indexed**. New static context raises classified bytes to
26,205 and lowers unclassified to 1,022,371. Native playability is **none**;
world services, boot, rendering/audio and broader scheduling remain unfinished.


Final preservation check matches the original ROM, BK2, worker, build manifest
and all 104 frozen runtime binaries. No owned reference workers remain. No GUI,
Sonic19420, WL3PC or external source/runtime changes; no upload/push. Vault check
passes (90 notes); hygiene and whitespace checks pass. The initially empty index
is retained until explicit staging of the owned source, tests, metadata and notes.
