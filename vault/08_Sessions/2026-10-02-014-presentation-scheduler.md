---
id: SESSION-20261002-014
type: session
status: complete
task: TASK-0010
---
# Use the user movie to reconstruct presentation scheduling

## Start and preservation

User authorized continued native reconstruction using the finished recording.
Read the actual entry instructions, project status/next actions, durable brief,
Git rules, task, grounded-actor finding/handoff and user-movie handoff; inspected
the native actor APIs/transports, reference harness, metadata and Genesis worker
protocol/ABI/Python guide before instrumenting. Actual root was
`~/WizNLizPC`, branch `work/airborne-update`, clean working tree and
empty index at `766e604423fdbc7cce983a929421763e5a110af6`. No pre-existing Wiz
changes or pending Git operation were present.

Original ROM remains 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
The finished user movie remains unchanged, SHA-256
`c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd`.
Used its existing verified adapted recording and complete input/settings/binary
identity; did not alter the original header or relax importer checks.

All workers were independent owned processes and closed normally. The user's GUI
was not controlled. BizHawk source/runtime binaries and Sonic/port 19420 remained
read-only; no external runtime rebuild, install, upload or push. WL3PC was not
used. The project-owned restricted Musashi harness was explicitly rebuilt under
WizNLizPC/local, separate from native targets. Bulk artifacts remain ignored.
All 104 runtime manifest binaries and the separate worker executable still match
the frozen build hashes at final review.

Intended checkpoint: `Reconstruct presentation scheduling using recorded gameplay`.

## Implemented scope

`src/sim/presentation.*` adds `step_presentation` and transactional
`step_scheduled_actor`. The scheduler preserves countdown/frame/cycle wrap,
old-frame target and endpoint comparisons, loop/bounce order, six typed callback
identities and callback-before-handler selection. Active bit 7 gates the wrapper;
F76C itself tests animation bit 0. Unknown callbacks reject when invoked, and a
later actor failure rolls back the whole scheduled phase. Older handler-only
and airborne component contracts remain unchanged.

The six callbacks complete idle turns, normal reversals and fast-jump animation.
Four callbacks tail to existing grounded initializers; their selected handler
runs in the same invocation. Two decrement the fast-jump cycle word and retain
motion handler/facing. Exact findings and exclusions:
[[03_Reverse_Engineering/findings/FIND-0014-presentation-scheduler]].

`re/presentation_step.json` pins eight disjoint ranges: 364 new classified bytes,
90 instructions, 25 direct transfers, two explicit indirect selectors. Seven
routine mappings join the function index; the bounded F8F6 dispatch phase is a
separate fragment. Total: 55 indexed functions, 46 simulation routine mappings,
two idle initializer fragments and one scheduled-dispatch phase. The next +46
service and broader frame/world loop are not implemented.

The native transport adds presentation-only, scheduled and continuous-sequence
modes without changing the old input/output shape. A sequence imports actor
state once; subsequent actor columns are continuity assertions. Inputs,
parameters and shared terrain scratch remain explicit environment feeds.

## Movie evidence and reproducibility

The first discovery survey used ignored
`local/generated/presentation-research/scan_movie.py`; its complete selected-PC
traces are in `local/generated/presentation-research/movie-scan/`. The final
tracked recipe is `tools/genesis_movie_survey.py`, independently rerun at
`local/generated/movie-survey/run-e7xmaphg/report.json`. It observes 4,139 active
P1 actor calls / 16,840 selected events across 5,298 movie input rows, rejects
trace overflow and matches the earlier unhooked movie's covered-state hash at
frame 5298. These observations are discovery, not native parity.

`tools/genesis_movie_actor_capture.py` uses ordinary unedited windows
[700,1067), [3100,3200), [4360,4400). It verifies exact pre-instruction phases,
A5/A6/SP and pending F900/F906 return words, selected callbacks/handlers,
continuous actor-field identity, no uncontracted writes and stable control
inputs within each call. Terrain resources are equal at window endpoints.
Every supported actor state field remains native across each window.

Final report: `local/generated/movie-actor/run-4xe1ygk8/report.json`.
**507 scheduled actor outputs and 507 presentation-phase outputs match**.
A774/A93A each execute four times; A50E/A654 each execute once. All 16 sound
requests match in order. Both normal reversals complete and select their new
ground handler immediately. Three window ends match a second fresh unhooked
worker. A2E8/A380 completion is verified by authored/Musashi cases, not by these
ordinary movie windows. Shared scratch feeds and unimplemented world services
prevent any claim of native whole-frame gameplay parity.

Commands and exact report hashes are in [[05_Validation/RESULTS]] and
`re/presentation_validation.json`. New static probe evidence:
`local/generated/presentation-probe/run-pyx50wn8/report.json` and sibling decoder
commands/graph. Local build/test logs: `local/generated/presentation-research/`.
The frozen Genesis build is
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`.

## Verification and observed failure

- 347,320 original/native presentation/scheduled cases pass in each of debug,
  release and ASan+UBSan. All three output-hash sets agree. All 90 new instruction
  addresses execute; 24 authored goldens and four exact callback rejection checks
  pass per preset. The corpus includes byte combinations, word sweeps, both
  directions, loops/bounces, terrain, repeated calls and inactive gating.
- Fresh sanitized regressions pass: 152,093 actor, 415,940 airborne, 282,233
  movement and 614,436 terrain. The five corpora visit all 737 scoped addresses.
- 123 Python tests pass with zero skips. All 15 CTest targets pass in debug,
  release and sanitize. Native units exercise continuous idle turn-to-ground,
  callback-to-jump, zero-reload timing, unsupported callbacks and whole-call
  rollback after presentation succeeded. Evidence tests reject missing phases,
  malformed stacks/selectors/order, drops and silent actor reseeding.
- Initial static probe `run-2nb1ctj5` failed because installed `m68k.gnu` rejects
  immediate BCHG 086e. Final probe explicitly reports that decoder limitation
  and corroborates five other instructions. The primary decoder and Musashi
  establish the mode-toggle effect; the selected GPGX actor windows do not
  establish bounce-mode coverage. No native mismatch
  was observed; no golden was adjusted to conceal a failure.

Final review tightened input loading to use the external bounded recording
validator (which recomputes the actual input digest) and require an unhooked
source baseline. Both movie tools were rerun successfully afterward. All 32
owned paths were explicitly staged and their code, evidence, tests and vault
diffs reviewed. Vault checks pass for 60 notes, hygiene for 188 indexed files,
and staged whitespace checks pass. No binaries, movie/state data or raw
disassembly are staged. Git and the vault describe the same implemented scope.

## Exact next pass

[[07_Tasks/TASK-0010-grounded-controller]] remains **in progress**, and
**native playability remains none**.
Use ordinary movie windows [1048,1090) and [2170,2210) to resolve fast reversal:
A96E/frame 1067 and A7A8/frame 2189, helpers A9DE/A818, allocator F994, returned
object/backlink and callback ownership. Subsequent selectors A9B2/A7EC remain
unsupported. Then up/down actions 9C56/frame 1629 and 9D4E/frame 1616, their
globals/services, the +46 post-handler service and broader scheduling/audio.
Those proposed windows are research targets, not passed native comparisons.
See [[01_Project/NEXT_ACTIONS]].
