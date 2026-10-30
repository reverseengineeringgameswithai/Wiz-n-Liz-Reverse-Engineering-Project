---
id: SESSION-2026-10-05-033
type: session
status: completed
---
# Retain return-only objects and dormant occupancy

Started clean at `3fa722ba8b34e8eb912e0a3994decf7d80a599fc` on
`work/airborne-update`, with an empty index and no merge/rebase/cherry-pick/revert
operation. The user asked to continue onto the next task after session 032.
Read AGENTS/CLAUDE, entry points, current handoff/task, brief/Git workflow,
pool/presentation/reference code and external worker instructions. No existing
user changes. Authorized local implementation, validation, vault synchronization
and reviewed commit; no pushes/uploads. No subagents or external tool changes.

Intended checkpoint: `Retain return-only objects and dormant pool occupancy`.

## Delivered scope

`ReturnOnlyObject` retains all represented fields for fixed 12646 handler and
service selectors. The original active gate, presentation and two RTS calls are
composed from existing mapped routines. An invoked callback, including a null
selector, rejects transactionally. No initializer, activation or release is
invented. Inactive typed objects remain occupied with unchanged generations;
they emit explicit inactive observations without consuming active-update budget.

The retained mixed pool now represents all seven former reservations: five
active slots 58–62 and dormant occupied slots 52/66. The current capture adapter
rejects unknown objects instead of falling back to reservations. The older
explicit `ExternalReservation` API remains available outside this measured
contract. Native pool kind 8 and event kind 3 carry typed state and inactive
observations; existing physical-input-only continuation rows are unchanged.

Evidence guards verify raw fields, fixed selectors, control identities, full
phase order, stacks, preserved A5/A6, unrelated state and exact write sites.
Extra invocations anywhere in the same frame reject. All 271 writes to these
seven objects are audited: 101 animation writes and 170 zero render clears.
Dormant slots have no writes and never appear on the free stack. Existing P1,
FF31xx, collision inputs, allocation order and whole-session rollback hold.

See [[03_Reverse_Engineering/findings/FIND-0033-return-only-objects]],
`re/return_only_step.json` and `re/return_only_validation.json` for scope,
identities, artifact hashes, comparisons and preservation metadata.

## Validation

- **286,848 original/native cases per debug/release/sanitize** pass, covering
  all mode/counter bytes, every first-frame word in both directions, boundary
  products, repetitions, inactive callback traps and seeded preserved fields.
  Each corpus executes 3,295,984 presentation calls and 6,591,968 RTS calls.
  All 42 successful supported instructions execute. Three callback cases reject
  in each implementation; original execution stops before null code executes.
- Restricted original execution permits only the declared routines, object
  reads, presentation writes and bounded stack. Static closure covers 67
  instructions; four selected GNU checks corroborate BPL, JSR, SUBQ.B and RTS.
  The project-owned Musashi harness rebuilt offline; native targets contain no
  emulator code or original CPU execution.
- Final fresh ordinary capture and independent unhooked replay:
  `local/generated/mixed-session/run-lw7uuh43/report.json`. Release/sanitize
  comparisons reuse and revalidate that fixture in `run-2oxlv1e6` and
  `run-yy6ctdui`. **633 ordered records** match per preset: 565 spawn/update/
  release events and 68 inactive observations. Added active work is 170
  return-only updates. There are zero external reservations in `[1066,1100)`.
- The 68-slot seed has fifty free and eighteen typed occupied entries. All
  prior updates, nine allocations/releases, full free order/RNG, 34 banners
  and two sounds still match. Output SHA-256:
  `ee43b59863c5171cbd96d553e3889309a9fd5834f27d0a00fe6f7a8458d025dd`.
  Zero edits, drops or overflow; 9,973 routine / 52,895 native events,
  2,111 managed writes and 27 free-stack writes. Hidden-device state remains
  outside the endpoint; this is not whole-frame/render/audio parity.
- **198 Python tests, zero skips; 46/46 CTests per preset** pass. Builds are
  warning-free. Tests cover dormant occupancy, exhausted capacity, release/reuse
  generations, exact transport events, callback/raw-field/writer rejection,
  extra invocations and rollback after earlier presentation, release,
  allocation/RNG, P1 movement, banner scratch and reversal allocation.
- Collision 478,345; table 406,634; private 277,232; trail 209,082; reversal
  203,586 comparisons pass per preset, as do older 390-call P1 fixtures.
  Table writer research reruns 131,422 cases. Eight additional sanitized
  corpora pass: input 1,024; banner 66,880; presentation 347,320; actor 152,093;
  dispatch 138,149; airborne 415,940; movement 282,233; terrain 614,436.
- No new original function/instruction/byte classification from composition.
  Fresh fourteen-corpus union is 1,185, or 1,194 including nine research writer
  instructions. Cumulative union remains 1,543; mappings remain 106 bounded
  plus two partial / 117 indexed; classified bytes remain 26,257.

## Attempts and skips

The first fresh capture `run-42_vkdyu` passed, then the evidence guard was
tightened to reject extra per-frame invocations outside the ordered slot phase.
A final fresh hooked capture and independent unhooked replay used the final
source hashes. Diagnostic reuse of the preceding session's fixture preceded
these new captures and is not claimed as new original execution.

A local summary attempted to read two comparison logs while their processes
were still running; the subsequent preservation attachment lacked its index.
Both metadata steps succeeded after waiting for completion. No native/reference
semantic mismatch, test failure or capture failure occurred in this pass.

Not rerun: actions/transition/coasting/tally/palette/bonus/exit-tally/score
comparison corpora, other historical/controlled captures, whole-movie survey
and SDL3 availability. No controlled full-machine edit was needed.

## Reproduction and handoff

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py configure --preset debug
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py return-only-compare --preset debug
python3 -B tools/project.py mixed-session local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py mixed-session local/generated/capture-qb2htq3j/recording.json --preset release --fixture local/generated/mixed-session/run-lw7uuh43/report.json
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py mixed-session-probe
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Build, tests, component and movie comparisons cover all three presets. Exact
reports/logs/provenance are indexed in `re/return_only_validation.json`.
Bulk research stays ignored under `local/generated/passive-object-research/`.

Next: **F9E2 allocation and the 7B9C return-only pair initializer**. Static
`[7B9C,7C26)` fields match retained slots 59/58, but dynamic creation provenance
is not established. Neither routine was executed in this pass. Verify allocator
range, A6 ownership versus F994's A5, defaults, ordered free-stack/exhaustion and
FF31C0 identity before implementing. See [[01_Project/NEXT_ACTIONS]].
callback79B6 and collision-hit7910 stay unsupported. TASK-0010 is **in progress**;
native playability is **none**. Boot, world scheduling, rendering/audio and P2
remain unfinished. Original execution remains reference tooling only.

Final preservation verifies ROM/BK2/recording, worker/build manifest,
104 runtime binaries and 59 manifest-recorded source files; owned workers are
closed. No GUI, Sonic19420, WL3PC or external source/runtime changes. The pass
closes with 98 vault notes checked, clean whitespace/hygiene checks, 44 artifact
hashes and 39 native executable identities verified, plus the restricted
reference and final source/test-log identities. Explicit staged review precedes
the local checkpoint commit. No pushes/uploads.
