---
id: SESSION-2026-10-12-039
type: session
status: completed
---
# The 783A collision quad initializer

Started clean at `5b80c0ce389c9eb059a58d71b10569724ee16c3a` on
`work/airborne-update`, with an empty index and no merge/rebase/cherry-pick/revert
operation. No pre-existing user changes in this repository; no emulator or
worker processes. The user asked to continue the recent work and leave Obsidian
and Git clean; this pass took the recorded next task. Authorized local
implementation, validation, vault sync and a reviewed local commit; no pushes/
uploads. No subagents; no external tool changes.

Intended checkpoint: `Reconstruct the 783A collision quad initializer`.

## Delivered scope

`[783A,78EE)` pops four F9E2 objects: a 78EE collision probe (mode 80, caller
A5 at +4A, (150,262), frame 912, extents 0038/0008), then three return-only
objects at (X+32,Y), (X,Y+32), (X+32,Y+32) copied through A4 with frames
913..915. None writes +08..+0D, target or countdown; the last three keep the link.

Native: `MixedPool::initialize_group<N>` generalizes the shared all-or-nothing
F9E2 template (pairs keep their two-pop wrapper). `InheritedObjectFields` gains
optional `InheritedPresentation`; `initialize_collision_quad(control)` requires
it on every popped slot and builds `make_quad_probe` plus three
`make_quad_return_only` members. Seed tag 9 accepts an optional four-field tail.
`wiznliz-collision` gains `--quad` and `--quad-pool` (control header field and
explicit per-phase 78EE inputs); `pair_pool` now takes typed phase inputs.

Tools: the reference harness gains `--collision-quad`; the comparator gains
`--variant collision-quad` with a 47-field per-member corpus; the evidence tool
is generalized from two to N ordered pops with per-member kinds, fields and
inputs, captures 78EE inputs per walk and traces 78EE/7910 during walks.

See [[03_Reverse_Engineering/findings/FIND-0037-collision-quad]],
`re/collision_quad_step.json` and `re/collision_quad_validation.json`.

## Validation

- **8,746 restricted original/native 783A cases per preset**; 45 successful
  instructions, 31 new. The three pair corpora rerun identically per preset.
- Final fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  `3f66b79f…`: `local/generated/pair-initializer-capture/run-yeihu450/report.json`.
  783A runs once (frame 629, slots 63..60) with an exact 65-write block; the
  frame-629 audit is complete (65/43/40/38 blocks, 54 other F9E2 writes).
- **The ordinary movie reaches unsupported hit7910 at frames 823..831** from the
  slot-63 probe (P1 X wraps through the 03FF mask). Native matches the quad's
  creation and first 189 walks, then rejects at frame 823; 243 later walks are
  original-only. All ten retained slots continue in the original through 432
  walks (the quad's bytes never change) and equal the 1066 mixed seed. Debug/release/sanitize reuse the capture.
- Mixed `[1066,1100)`: session-035 capture `run-q_wuylbz` reused; same output
  hash `c6167d3a…` in every preset.
- **209 Python tests, zero skips; 46/46 CTests per preset**; warning-free builds;
  29 regressions and the mixed-pool context probe pass. Totals: 111 bounded plus
  two partial / 122 indexed; 26,929 classified / 1,021,647 unclassified bytes;
  1,659 cumulative; union 1,301 (1,310 with writers).

## Attempts, failures and skips

The first fresh capture (`run-uho0q5pz`, log `capture-first-debug.log` in
`local/generated/collision-quad-research/`) stopped because continuity rejected
every 7910 event, and the ordinary movie hits. The tool now records hits only
inside a retained probe's own service and bounds native comparison at the first
hit; offline revalidation passed, then a final fresh capture used final sources.
An ad hoc regression runner omitted `--rom` flags; it was stopped and the
session-036 script reused. A comment-only header edit made build provenance
stale, so all presets were rebuilt and every native comparison rerun. Test
goldens (free-row order, bad-row placement, streamed init line before a hit) and
a sign-conversion warning were corrected without native changes. Two of my
wait loops matched their own command lines in `pgrep -f` and were stopped.

Not rerun: action through score corpora, debug/release runs of the eight
sanitized corpora, a fresh mixed capture (tool unchanged), other captures,
whole-movie survey and SDL3 availability.

## Reproduction and handoff

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py pair-initializer-compare --preset debug --variant collision-quad
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset release --fixture local/generated/pair-initializer-capture/run-yeihu450/report.json
python3 -B tools/project.py mixed-session local/generated/capture-qb2htq3j/recording.json --preset debug --fixture local/generated/mixed-session/run-q_wuylbz/report.json
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Next: **the 6EC8/6EDC dormant initializers and the native `[6886,68A4)` setup
prefix**. See [[01_Project/NEXT_ACTIONS]]. Hit7910, callback79B6, 7AD6,
overlap-hit FF31C0 readers and gate producers stay unsupported. TASK-0010 is
**in progress**; native playability is **none**.

Preservation: ROM, BK2/recording, worker/build manifest, 104 runtime binaries
and 59 GenesisDebug sources verify; owned workers are closed (their checkpoints
removed). BizHawkOpenSource differs from session 036 only by owner work dated
2026-10-10/11 and did not change during this pass. WL3PC was only read; its
owner made concurrent uncommitted doc edits there during the pass. Explicit
staged review precedes the local checkpoint commit. No pushes/uploads.
