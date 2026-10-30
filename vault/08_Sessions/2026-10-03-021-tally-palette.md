---
id: SESSION-2026-10-03-021
type: session
status: completed
---
# Tally palette preparation and deferred waits

Started clean on `work/airborne-update` at
`a68f1fa54a2ecb9b8bb287040d458596e5df5d8d`, with empty index and no pending Git
operation. Read the actual entry points, current handoff/task/finding, durable
brief, Git rules and reference capability/hook/edit documentation. The latest
handoff selected 51D0/5204, rather than the older already-completed up/down work.
No new user input, recording or GUI action was required.

Intended checkpoint: `Reconstruct tally palette preparation and deferred waits`.

## Implemented result

51C8's nonzero gate now coasts, waits for the shared transition, converts sixteen
palette colors, initializes the tally transition and assigns 5204 for a later
invocation. 5204 coasts/waits and assigns deferred 5222. Zero-gate 51C8 still
branches immediately to 5222 in the same invocation. Neither new assignment
counts units immediately. Exact selected-handler/helper returns are verified.

Typed `PalettePreparation` preserves source words and B/G/R byte-triplet order.
The destination participates in the complete actor/presentation/wrapper
transaction with all prior contexts. Missing contexts, budgets, unsupported
services and the still-unsupported 5266 path expose no partial updates. The
native library contains no emulator. Curve identity 135EA is represented
logically; evaluation, rendering and device writes are not implemented.

Research transport adds bounded `--palette` and `--palette-sequence` modes.
The sequence retains actor/service/tracking, mutable tally counters and palette
destination. Source colors, shared timer, controls and scratch are explicit world
feeds. Unknown fields/curves, drift and malformed rows reject. The restricted
original harness guards fixed bank/source and read/write extents, executes
original code, and checks the converter's actual D2 clobber rather than incorrectly
requiring the older preservation sentinel on this path.

## Validation

- Static exact-byte/transfer/closed-graph checks: five new intervals,
  **232 bytes / 56 instructions**. Four GNU checks pass; inherited presentation
  BCHG limitation remains. No new decoder gap.
- **214,448 original/native cases in each of debug, release and sanitize**,
  identical output hashes. Sixteen independent goldens; every color word in
  every slot and every direction word in both handlers, plus arithmetic,
  activity, repeated-call and terrain cases. Separate sweeps are not a proof
  of the full Cartesian state space.
- **Two controlled RAM-edit experiments**, 17 and 20 continuous P1 wrappers.
  Ready path prepares at 3403, finishes its wait at 3417, counts from 3418.
  Initial-wait path prepares at 3406, finishes its wait at 3420, counts from
  3421. The second overwrites destination bytes with A5 before execution to
  make conversion observable. Independent unhooked workers repeat identical
  edits/inputs and match both covered-state endpoints. No trace overflow.
- **Ordinary movie regressions:** 175 tally wrappers, five sound requests and
  mode=3 completion at 3577; 17 transition actor / 17 timer calls; one coasting
  initializer / 16 wrappers. All have independent unhooked equality.
- Fresh sanitized corpora: 231,475 tally, 87,571 coasting, 306,528 transition,
  138,149 wrapper, 146,638 actions, 347,320 presentation, 152,093 actor,
  203,586 reversal, 415,940 airborne, 282,233 movement, 614,436 terrain.
  Twelve corpora visit **1,132 scoped instructions**, including six reference-only
  sound guards.
- **159 Python tests, zero skips; 26/26 CTest targets in every preset.**
  Authored tests verify deferred counting, externally scheduled timer sequence,
  B/G/R order, retained fields, missing contexts, coasting budget and late-service
  rollback. Synthetic traces reject missing boundaries, wrong stacks/bank/extent,
  uncontracted writes and overflow.

Initial test development found a one-step error in the authored timer expectation,
a negative continuity case that selected invalid handler 27, the old test's
now-valid curve ID 3, and missing A1/D1 fields in a synthetic trace fixture.
Those expectations/fixtures were corrected and the final suites passed.
A comparator attempt also correctly rejected stale native build provenance after
a unit-test source edit; rebuilding and rerunning passed. An intermediate vault
check reported the new finding's missing schema fields and not-yet-written
session link; the final vault check passes. No original/native semantic mismatch
or final failure is hidden. Older 507/92/24 and 191/72 movie contracts and the
full survey were not rerun in this pass.

Machine-readable evidence: `re/palette_validation.json`. Reproduction commands:

```sh
python3 -B tools/project.py palette-probe --disassemble
python3 -B tools/project.py palette-compare --rom --preset debug
python3 -B tools/project.py palette-compare --rom --preset release
python3 -B tools/project.py palette-compare --rom --preset sanitize
python3 -B tools/project.py palette-capture local/generated/capture-qb2htq3j/recording.json --preset sanitize
python3 -B tools/project.py tally-capture local/generated/capture-qb2htq3j/recording.json --preset sanitize
python3 -B tools/project.py transition-capture local/generated/capture-qb2htq3j/recording.json --preset sanitize
python3 -B tools/project.py coasting-capture local/generated/capture-qb2htq3j/recording.json --preset sanitize
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py test --rom --preset release
python3 -B tools/project.py test --rom --preset sanitize
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

## Preservation and handoff

Original ROM and BK2 hashes match, as do all 104 pinned runtime binaries and the
worker. The movie input digest remains
`34434f0aa0b1ebc7dbf4e464cd044ac52436b944bf6a01cdc24c811e1f6c3a88`.
Frozen build ID remains
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`.
No external source/runtime rebuild, GUI/Sonic manipulation, package installation,
upload or push. New captures/states/disassembly/binaries remain ignored. Owned
workers close normally. Explicit owned paths are reviewed/staged for one
synchronized code/test/metadata/vault checkpoint; the tree began clean.

Current totals: **87 bounded simulation mappings plus two partial tally handlers /
98 indexed functions**. Classified bytes: **23,995 / 1,048,576**. 51C8/5222
remain partial because they can reach 5266. **TASK-0010 stays in progress;
native playability remains none.**

Exact next task: reconstruct **5266's bonus-allocation path and 451A/4770**,
including its sample request, FF0104 write, failure result and partial
five-attempt loop. Use explicit ownership and transactional effects; do not
assume the reversal-only store applies. Discovery disassembly is in ignored
`local/generated/palette-research/5266-next-lead.txt`. Later recorded selectors
5132/5188 and broader world/P2/palette/audio scheduling remain open.
See [[01_Project/NEXT_ACTIONS]] and
[[03_Reverse_Engineering/findings/FIND-0021-tally-palette]].
