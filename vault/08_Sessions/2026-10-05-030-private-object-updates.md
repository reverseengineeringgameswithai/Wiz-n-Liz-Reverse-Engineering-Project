---
id: SESSION-2026-10-05-030
type: session
status: completed
---
# Reconstruct rising and gated visibility objects

Started clean at `a63730cd76e691d919d5fdcdd8c24b8b3b154222` on
`work/airborne-update`, with an empty index and no pending Git operation. Read
actual entry points, brief/workflow, status/next/task, session/finding 029, native
pool/trail/presentation, capture/harness code and external hook/capability rules.
User authorized autonomous continuation; no new movie or GUI action needed.

Intended checkpoint: `Reconstruct rising and gated visibility object updates`.

## Implemented result

`src/sim/private_object.*` supplies typed 7808 and 7CA4 updates, including the
bounded active/presentation phase and fixed return-only service. Exact behavior,
range hashes and logical field contract are in
[[03_Reverse_Engineering/findings/FIND-0030-private-object-updates]] and
`re/private_step.json`. Both handlers preserve word wrap, gate widths, presentation
order and untouched fields. The control link is retained without dereferencing it.
Unknown invoked callbacks/handlers reject with complete rollback.

The mixed pool retains four more original objects, reducing external reservations
from thirteen to nine. Shared gate context is seeded once, followed only by
physical held masks. Missing context, work/callback failures and earlier release/
private updates roll back together. The old four-field pool header remains valid
for scopes without private objects; the seven-field header adds the three gates.
P1/effect/emitter allocation and slot-sensitive birth/release order are preserved.

## Fresh validation

- **277,232 private original/native cases per debug/release/sanitize**: 134,520
  handler cases and 142,712 scheduled cases. All twenty handler instructions
  execute. Countdown/word gates exhaust their ranges; longword gate boundaries,
  equality-only stop, signed/word wrap, all presentation modes, inactive work,
  callback rejection and up to 256 retained calls are exercised.
- Primary hashes/closed graph (87 instructions) and four selected GNU checks
  pass. GNU cannot decode immediate MOVE.W at 7CAC/7CBA; no full GNU claim.
- Fresh ordinary unchanged movie `[1066,1100)` capture:
  `local/generated/mixed-session/run-rg1kl63c/`. Independent unhooked exposed-state
  endpoint matches. Debug compares that new capture; release and sanitize reuse
  it after artifact/source/input/identity revalidation. No memory edits, drops
  or overflow. Original branch coverage has all three private gates zero;
  nonzero paths are restricted-original synthetic cases, not gameplay observations.
- All presets match **34 P1/emitter calls, 136 trail updates, twelve reversal
  updates, 136 private updates, nine allocations/releases and 327 ordered pool
  events**, complete free-stack order, RNG, 34 banners and two sounds.
- Capture cadence: 102 conversions, 136 polls, 34 inactive timers, 214 scratch
  writes, 9,767 routine events and 52,895 native events. Audited writes: 1,621
  managed slots, 490 reservations, 27 free-stack, zero private shared-gate writes.
  Snapshots and write guards exclude transient gate changes. Gate producers are
  not reconstructed or assumed fixed outside this window.
- **192 Python tests, zero skips; 40/40 CTests per preset**. Authored goldens,
  retained gate changes, malformed state/transport/evidence and rollback after
  earlier pool work pass. Final native builds are warning-free.
- Trail **209,082** and reversal **203,586** cases per preset pass freshly.
  Eight sanitized regressions pass: input 1,024; banner 66,880; presentation 347,320;
  actor 152,093; dispatch 138,149; airborne 415,940; movement 282,233; terrain 614,436.
  Fresh eleven-corpus instruction union 1,138; cumulative 1,487 is partly historical.
- Older original P1/reversal fixture freshly matches **390 calls in each preset**;
  output remains `8c738e9a85ad89630327f17f9a973add730f96a7ee29555ce55267a51558577b`.
  Those are native comparisons of saved evidence, not extra original replays.
- Mixed output in all presets:
  `5b167fceb5eba9142ec3043d08ddbca604e493825b3368af4a11a1c22a5ea956`.

No native/reference semantic mismatch. Initial comparator setup rejected a
missing executable allowlist entry, then a GNU decode check rejected the
unsupported immediate MOVE.W form. Both were resolved before the passing runs:
registered/rebuilt the native executable and restricted GNU corroboration to
four compatible instructions, retaining primary decode and original execution
for the others. Project-owned Musashi harness was extended and rebuilt; the
external Genesis runtime was never rebuilt or changed.

Not rerun: eight other component corpora (actions, transition, coasting, tally,
palette, bonus, exit tally, score), other old/controlled captures, whole-movie
survey and SDL3 availability. No new controlled full-machine experiment was
needed for these self-contained handlers; their active branches execute in the
restricted original harness with guarded state and exact return boundaries.

## Reproduction and next pass

```sh
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py private-compare --preset debug
python3 -B tools/project.py mixed-session local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py mixed-session local/generated/capture-qb2htq3j/recording.json --preset release --fixture local/generated/mixed-session/run-rg1kl63c/report.json
python3 -B tools/project.py trail-compare --preset debug
python3 -B tools/project.py reversal-compare --rom --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Repeat native builds/tests/new comparison for all presets. The research harness
can be rebuilt explicitly with `python3 -B tools/build_terrain_reference.py`;
that offline build uses pinned local Musashi and never enters native targets.
Evidence/report hashes and comparison counts: `re/private_validation.json`.
Research disassembly, raw traces, states and binaries remain ignored locally.

Next bounded task: **7A88 table motion**, its FF31BC input/writers, bounded loop,
table cursor arithmetic and presentation callback boundary. Slot 67 runs this
handler once per measured invocation. Callback 79B6 and collision-hit 7910 remain
explicit rejects until separately verified. Preserve retained private state,
shared allocator/free order, native RNG and physical-only subsequent inputs.

TASK-0010 stays in progress. Totals: **104 bounded mappings plus one partial /
114 indexed**. These 86 bytes were already classified: 26,205 classified and
1,022,371 unclassified remain unchanged. Native playability **none**; initializers,
shared gate producers, broader world scheduling, boot/render/audio remain open.


Final preservation check matches ROM, BK2, worker, build manifest and all 104
frozen runtime binaries. All owned reference workers are closed. No external
source/runtime, GUI, Sonic19420 or WL3PC changes; no upload/push. Vault check
passes (92 notes), hygiene and whitespace checks pass. Explicitly staged owned
code/tests/metadata/notes are reviewed before the checkpoint commit.
