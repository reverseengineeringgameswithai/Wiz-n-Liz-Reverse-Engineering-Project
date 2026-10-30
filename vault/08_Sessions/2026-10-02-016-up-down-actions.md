---
id: SESSION-20261002-016
type: session
status: complete
task: TASK-0010
---
# Continue TASK-0010 through up/down actions

## Start and preservation

The user explicitly requested reconstructing up/down actions. Actual root:
`~/WizNLizPC`; branch `work/airborne-update`; clean tree and empty index
at `28436169910a377dd925e5a0a53e4424d3b10b4a`. No pending Git operation. Read actual
AGENTS/CLAUDE, START_HERE, vault entry/status/next actions, durable brief, Git
rules, task, fast-reversal handoff/finding, source/transport/reference tools and
the external Genesis README/verification/Python/protocol/ABI documentation.

The immutable ROM remains SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
The original completed movie remains
`c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd`.
All 104 frozen runtime manifest binaries and the separate worker executable
retain their expected hashes; audit: `local/generated/actions-research/preservation.json`.
The original movie/header and derived recording intake are unchanged.

Only owned independent workers were used and closed. No GUI control, Sonic
bridge access, external source/runtime rebuild, WL3PC access, package install,
subagent, push or upload. The project-owned restricted Musashi harness was
rebuilt under ignored Wiz/local. No emulator enters native targets.

Intended checkpoint: `Reconstruct up and down actor actions`.

## Implemented scope

`src/sim/actor.*` implements both entries/hold/release/deferred-jump branches,
shared action gates and logical sample request. `src/sim/presentation.*` adds
F938 and contextual A196 execution. A196 initializes idle and runs its handler
inside presentation; the wrapper then runs the selected handler again. Native
budgets and transaction cover both executions, terrain scratch, shared globals,
explicit reversal storage and returned effects. The context-free presentation
API rejects A196 rather than dropping its context-dependent behavior.

New modes on `wiznliz-actor` compare handler-only, contextual presentation,
scheduled updates and continuous actor sequences. Shared globals and mailbox
remain explicit environment inputs; the transport maps the sample ID to the
verified original mailbox representation. Playback/consumption are excluded.
The C++ API supports shared action and reversal contexts together; their movie
transport/effect contracts stay separate and diagnose unsupported combinations.

`re/actions_step.json`: thirteen disjoint ranges, 412 new bytes, 81 instructions,
twelve direct transfers; twelve bounded mappings FUNC-0068–0079. Current total:
79 indexed functions / 70 bounded simulation mappings, plus the existing two
idle initializer fragments, one actor phase and two effect phases. Exact ranges,
state dependencies, wrap semantics and limits:
[[03_Reverse_Engineering/findings/FIND-0016-up-down-actions]].

## Movie research and final evidence

Initial ignored recipes/captures: `local/generated/actions-research/capture.py`,
`capture/`, `capture.log`, `branch.py`, `branch/`, `branch.log`. Static slices are
also there. They establish both the F900-pending callback continuation and the
separate F906-pending selected-handler execution. Wider windows are discovery
artifacts, not all passed native calls.

Final tracked recipe: `tools/genesis_actions_capture.py` / `project.py actions-capture`.
Final report: `local/generated/actions-movie/run-ee3uhda0/report.json`.
The recording retains input digest
`34434f0aa0b1ebc7dbf4e464cd044ac52436b944bf6a01cdc24c811e1f6c3a88`
and frozen worker build
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`.

- Ordinary unedited [1615,1690): 75 actor and 75 presentation checks, two A196
  callbacks and two F938 callbacks. Down entry 1616; callback-to-up entry 1629.
- Ordinary unedited [3230,3339): 109 actor and 109 presentation checks, two A196
  and two F938 callbacks, two sound requests. Up entry 3243; callback-to-down 3282.
- Explicit input branch at 3258: Up+A for 16 rows, neutral 14, Down 18, Down+B 4,
  neutral 8. Sixty actor/presentation checks, one sample request at 3258 and a
  deferred down jump at 3306, followed by two jump sound requests at 3307.
- Separate Up+B four-row / neutral eight-row branch at 3258: twelve actor and
  presentation checks. Deferred up jump at 3258 executes at 3259 with two sounds.

Branches preserve full parent and replacement-input provenance with **zero
RAM/register/ROM edits**. They exercise ordinary game logic but are not the
user's unchanged recording. Every endpoint matches a fresh unhooked worker:

| Boundary | Covered-state SHA-256 |
| --- | --- |
| Ordinary 1690 | `1baf0e12950348021cfa0a44d71a70728f9c9a324532058198a141fb1791db2f` |
| Ordinary 3339 | `0b457909f71de875506844ea091199f66492e77c5767b8af272683a365008fbb` |
| Sample/down-jump branch 3318 | `f2aaba7fd7ab1459b42deb9433b5cc616e38c3f2adedc26696e6747abb2114a0` |
| Up-jump branch 3270 | `4fe1d86467ef6a156f342ebf710912e94787adbef3ec609952d276dc22941737` |

These hashes cover declared exposed state, not hidden-device equivalence. Native
actor state persists, but controls/parameters/shared globals/mailbox/scratch are
fed from the surrounding original world. Terrain is equal at window endpoints;
no claim of all transient terrain writes or full native frame replay is made.
Branch frame numbers overlap original-route frames. The 256 intermediate checks
are distinct from 256 actor calls, not additional gameplay frames.

## Fresh verification

**146,638 cases per debug/release/sanitize preset** pass with identical native
output hashes. Groups: 139,936 handler, 2,072 contextual presentation, 2,070
scheduled, 768 authored terrain, 1,792 cataloged terrain. Eighteen hand-calculated
goldens and all 81 new instruction addresses pass. Sweeps include all interval
and cooldown words, all raw control bytes, signed wrap, both facings, immediate
and deferred transitions, press/hold/release and callback-to-jump/action behavior.

**135 Python tests, zero skips; 17/17 CTest targets per preset pass.** Native
sequence tests exercise both facings, animation freeze/reverse/wrap, deferred
jump, two movement executions in one scheduled call, retained fields, missing
context, callback/resource/budget errors and rollback after a sample request.
Evidence tests reject missing/unbalanced boundaries, overflow, changed ABI,
mailbox/uncontracted global writes and broken continuity.

Fresh sanitized regressions all pass: 203,586 reversal, 347,320 presentation,
152,093 actor, 415,940 airborne, 282,233 movement, 614,436 terrain. Seven corpora
visit 937 scoped original instructions, including six reference-only sound
selector guards. The static closed graph, CPU sentinels, five new GNU and five
previous scheduler checks pass; previous decoder limitations remain explicit.

Fresh old movie regressions also pass: 507 actor / 507 presentation checks
(`local/generated/movie-actor/run-2y7skxmj/report.json`), and 92 actor / 24 effect
updates (`local/generated/reversal-movie/run-lduvr0hq/report.json`), with unhooked
endpoint agreement. Do not add overlapping windows as unique original frames.

Reports, hashes, output digests and logs: `re/actions_validation.json`.
Reproduction commands: [[05_Validation/RESULTS]]. Bulk artifacts stay ignored.

## Corrected exploratory failures

- First action comparison `run-kro0trk6` found an authored golden calculation
  error, after original/native outputs had already agreed. Callback-to-jump
  executes two zero-speed airborne settle calls. On the authored flat record,
  Y goes 109 -> 105, then settling adds one before 106 - 4 = 102. The initial
  manual expectation 101 / one settle was corrected with this explicit original
  ordering; no native mismatch was hidden. Final goldens retain this explanation.
- Initial action movie `run-80hbul_b` rejected [1608,1690): 12646 is selected
  before the AA50 callback at 1614. Neither is claimed as integrated in this
  presentation contract. The continuous comparison now starts at 1615.
- `run-ve31oo2s` passed the first interval, then rejected frame 3339 because the
  action transport lacks reversal allocation storage/output. The second interval
  now ends before 3339; full reversal lifetimes pass their separate comparator.
- Initial old actor regression `run-d1ott9ta` stopped at an outdated rejection
  assertion. It expected generic “unsupported” for Up, now a precise missing-
  globals error, and still expected implemented Down to fail. Up's explicit
  failure was retained with its new message; Down moved to the action corpus.
  Fresh `run-ugkhb7nf` passes all 152,093 cases and remaining rejection checks.
- A local summary script initially used `cases` for the older terrain report,
  which names it `total_cases`. This metadata-only error was corrected; all
  report hashes and counts are checked before publishing the tracked summary.

No final failures or skips. No original/native output mismatch occurred.

## Checkpoint review

Explicitly staged and reviewed all 34 owned paths: native semantics/transactions,
reference allowlists, transports, original/native corpus and authored tests,
full-machine boundary/provenance checks, mapping/range metadata and vault.
No unrelated index content, ROM, movie, binary, state or bulk capture is staged.
Staged whitespace passes; vault checks pass for 64 notes and hygiene for 210
indexed files. Final debug rerun still passes 135 Python tests and 17 CTest
checks; its log hash is retained alongside the other preset results.

## Next handoff

[[07_Tasks/TASK-0010-grounded-controller]] remains **in progress**. **Native
playability: none.** Next reconstruct the measured **12646 handler / AA50 callback
integration at movie frames 1608–1614**, then investigate later F906/F90A +46
services. The action effects are complete only through the compared boundary;
shared timer scheduling, audio consumption, general object competition/owner
lifetime, rendering and full world replay remain separate. No further user input
is needed for the next bounded research start.
