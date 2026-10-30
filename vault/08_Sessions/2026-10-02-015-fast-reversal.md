---
id: SESSION-20261002-015
type: session
status: complete
task: TASK-0010
---
# Continue TASK-0010 through fast reversal and owned effects

## Start and preservation

The user authorized continuing TASK-0010 autonomously. Actual repository root:
`~/WizNLizPC`; branch `work/airborne-update`; clean worktree and empty
index at `f8ce9e423c2131216e2f2abc83c1075c33797a59`. No pending Git operation or
pre-existing project changes were found. Read actual AGENTS/CLAUDE/START_HERE,
vault workflow/status/next actions, durable brief, Git rules, task, latest
presentation finding/handoff and Genesis capability/protocol/ABI documentation.

Original ROM remains 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
The finished movie remains SHA-256
`c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd`.
Its existing adapted recording is used without changing original import/header
or relaxing input/build checks. All 104 external runtime manifest binaries and
the separate worker executable match the frozen manifest at final audit.
`local/generated/reversal-research/preservation.json` records the check.

Owned independent headless workers closed normally. The user's GUI, external
BizHawk source/runtime, Sonic installation/port 19420 and WL3PC were not modified;
WL3PC was not consulted. No runtime rebuild, package installation, push or upload.
The project-owned restricted Musashi harness was rebuilt under ignored Wiz/local.
Native targets contain no emulator. No subagents were used.

Intended checkpoint: `Implement fast reversal and owned effect lifetimes`.

## Implemented and reviewed scope

`src/sim/actor.*` implements both allocating fast reversals, their immediate
motion phase, ungated reversal jump and two presentation completion callbacks.
`src/sim/reversal.*` implements effect initialization, retained Y / followed X,
release-before-final-follow ordering, typed owners and a bounded LIFO store with
generation guards. Actor/scratch/store changes publish together; failure after
internal allocation rolls everything back. Empty allocation is an explicit
bounded error, replacing the original non-returning hardware failure loop.

The shared `advance_presentation` primitive preserves the previous scheduler
semantics. Old actor transport modes retain their output contract. New reversal
modes return normalized spawn fields; effect modes support independent and
continuous lifetime comparisons. Unknown up/down behavior remains rejected.
The pool contains only reversal effects, not every original object type.

`re/reversal_step.json` adds fourteen disjoint ranges: 576 bytes, 119 instructions,
23 direct transfers and explicit known indirect targets/stops. Twelve routine
mappings plus two bounded effect-dispatch fragments join the index: 67 functions,
58 simulation mappings, two idle initializers, one actor phase and two effect
phases. See [[03_Reverse_Engineering/findings/FIND-0015-fast-reversal]].

## Movie research and comparison

Initial discovery recipe and output are retained under ignored
`local/generated/reversal-research/capture.py`, `capture.log` and `capture/`.
It found both object-loop variants and the final follow after release. The final
tracked recipe is `tools/genesis_reversal_capture.py`, exposed as
`project.py reversal-capture`. It pins complete inputs/settings, loaded binary
identity, exact instruction/return boundaries, owned objects and unhooked replay.

Final ordinary report:
`local/generated/reversal-movie/run-llim31lv/report.json`.
Windows [1048,1090) and [2170,2220) supply **92 continuous native actor calls**
and **24 continuous effect updates**, two allocations/releases and two sound
requests. Native actor/effect state is retained; owner positions are taken from
compared native actor output. Inputs/parameters/shared terrain scratch remain
external environment feeds. Terrain matches at endpoints; no claim of every
transient terrain mutation or complete world simulation is made.

Observed effects: FF2C12 born at 1067, released at 1078; FF2A3E born at 2189,
released at 2200. A9DA completes at 1085. The second actor enters airborne through
terrain before A814 completion; A814 remains authored/Musashi evidence, not an
ordinary movie observation. Both endpoint hashes match fresh unhooked workers:

- 1090: `1839b7f2e597b9b923408a465d637b291e23cf8da3698934896dd45bc750cbe9`
- 2220: `8fb37f99c7e2874cd0d17e656be8fa49cb1644833d99dddd5aa9d7cd7ee0c4b9`

The earlier movie comparator was rerun successfully at
`local/generated/movie-actor/run-0yo4xcu0/report.json`: 507 actor / 507 presentation
comparisons. The first reversal window overlaps 19 earlier source frames; these
are separate comparison contracts, not totals of unique whole native frames.

## Fresh validation and limits

- **203,586/203,586 original/native cases per debug/release/sanitize preset**, with
  identical output hashes: 1,670 flat actor, 192 scheduled sequences, 197,372
  effect cases, 768 authored terrain and 3,584 cataloged terrain. Ten independent
  goldens and four exact exhaustion rejections pass per preset.
- All **119 newly scoped instructions** execute, including original active gate,
  scheduler and indirect follow in both effect-dispatch fragments. Restricted
  execution stops before the later +46 service or inactive tail with the caller
  return pending; it does not synthesize RTS or patch original instructions.
- Fresh sanitized regressions: **347,320 presentation, 152,093 actor, 415,940
  airborne, 282,233 movement and 614,436 terrain**, all passing. The six corpora
  jointly visit **856 scoped instructions**, including six research-only sound
  guard instructions.
- **129 Python tests, zero skips; 16/16 CTest targets** pass in debug, release and
  Clang ASan+UBSan. Authored checks include ownership/stale handles/reuse, double
  release, wrapping coordinates, failure after allocation, same-call completion,
  reversal jump and malformed/incomplete evidence/sequence rejection.
- Primary decoding and CPU sentinels pass, with five old scheduler and five new
  reversal GNU corroborations. Exploratory GNU decoding misdecoded F9A0's 23c8
  absolute store; the probe explicitly records that limitation. It is not
  counted as independently GNU decoded. Original execution still covers it.

No native/original comparison mismatch or final suite failure occurred. An
initial compile reported a misleading-indentation warning in the new transport;
it was corrected before final builds. The first vault check ran before the new
session note existed and reported its missing links; those links are now
resolved. No expected outputs were adjusted to conceal a native mismatch.
No final suite skips. Source/probe/report/log hashes and exact paths are pinned
in `re/reversal_validation.json`; commands are in [[05_Validation/RESULTS]].
All bulk traces, states, disassembly, resource fixtures and binaries stay ignored.

Final staged review covered all 36 owned paths: native state/transactions,
reference boundaries, transports, authored/evidence tests, range/index metadata,
report hashes and vault changes. Staged whitespace checks pass; vault checks
pass for 62 notes and hygiene for 200 indexed files. No ROM, movie, binary,
state, bulk disassembly or unrelated user work is staged.

## Next handoff

[[07_Tasks/TASK-0010-grounded-controller]] stays **in progress**.
**Native playability remains none.** Up/down paths and complete shared services remain unimplemented. Exact next task:
research **9D4E down / 9C56 up** around ordinary movie frames **1616/1629**, using
selected window [1608,1648). Resolve raw +14/global dependencies and additional
handlers/callbacks/services before adding typed native behavior. This proposed
window is not a passed native comparison. General object competition/owner
destruction, +46, sound consumption, broader scheduling and SDL3 follow later.
See [[01_Project/NEXT_ACTIONS]].
