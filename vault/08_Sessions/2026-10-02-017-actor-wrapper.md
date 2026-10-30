---
id: SESSION-2026-10-02-017
type: session
status: completed
---
# Bounded actor wrapper through service and control tracking

Started clean on `work/airborne-update` at
`59c6124b122cf59a97598e80188188a6981ae169`. Read the actual entry points, current
status/next/session/task/finding, durable brief, Git rules and Genesis capability/
hook documentation. No pre-existing index or worktree changes, and no pending
Git operation. User authorized continuing the reconstruction autonomously.

Intended checkpoint: `Complete bounded actor wrapper and airborne callback`.

## Implemented result

Closed the exact 12646/AA50 gap at movie 1608–1614, then implemented F906–F938's
selected service and control-coordinate tail. Return-only handler/service are
explicit typed identities; AA50 initializes only, then the wrapper selects and
executes airborne in the same call. Inactive calls still update coordinates.
Unknown invoked services reject; the transaction spans actor, tracking, terrain,
shared action globals, reversal storage and returned requests.

`step_actor_dispatch` retains the prior narrower APIs. New research transport
modes retain actor/service/tracking coordinates across sequences. Musashi uses
original bytes through actual RTS; all emulation stays outside native targets.
Details and limitations: [[03_Reverse_Engineering/findings/FIND-0017-actor-wrapper]].
One added bounded routine mapping plus the extended actor phase brings totals
to 80 indexed functions / 71 simulation mappings and 23,169 classified ROM bytes.

## Verification performed here

- Static closed graph and original-68000 CPU sentinels pass; six new GNU checks.
  Two new disjoint ranges contain 52 bytes / 15 instructions, all executed.
- **138,149 original/native cases per debug/release/sanitize preset**, identical
  output hashes, thirteen independent goldens, four expected rejection runs per
  preset. All coordinate/selector words, mode/countdown bytes, both facings,
  callback/landing order and authored/cataloged terrain are exercised.
- **139 Python tests, zero skips; 18/18 CTest targets in every preset.** Native
  tests include late service failures after sample request and reversal allocation,
  unchanged owners on failure, unknown selectors, budgets, inactive tracking,
  word wrap and coordinate continuity assertions.
- **191 continuous ordinary movie wrapper calls and 72 input-branch calls**,
  with separate presentation and selected-handler checks for every call. Four
  fresh unhooked endpoint matches. No memory/register/ROM edits.
- Fresh sanitized regressions: **146,638 actions; 347,320 presentation; 152,093
  actor; 203,586 reversal; 415,940 airborne; 282,233 movement; 614,436 terrain**.
  Eight corpora visit 952 scoped instructions, including six reference-only
  sound guards. No original/native semantic mismatch occurred.
- Fresh older movie regressions: **507 actor/presentation checks** and **92 actor
  / 24 effect updates**, each with independent unhooked replay. These windows
  overlap other contracts and must not be summed as unique gameplay frames.
- Fresh 5298-row selected-PC survey: all **4139 selected +46 services are 12646**;
  recorded final unhooked baseline matched. This is discovery, not another 4139
  native comparisons. Six unsupported handler identities remain.

Exact final reports, hashes and log identities: `re/dispatch_validation.json`.
Bulk artifacts: ignored `local/generated/scheduler-research/`,
`dispatch-probe/`, `dispatch-comparison/`, `dispatch-movie/`, `movie-survey/`.
Final wrapper report: `local/generated/dispatch-movie/run-zefqb8xw/report.json`.
Fresh survey: `local/generated/movie-survey/run-gxfthj5e/report.json`.

## Corrected exploratory attempts

- `dispatch-comparison/run-ndfibh_w` found a manual golden error after the native
  and original outputs already agreed. On the flat record at Y109, the horizontal
  foot probe already equals contact; falling lands immediately, then consumes
  idle. The initial authored expectation of Y111/falling was corrected to
  Y109/idle, two settle calls and one landing. Native code was not changed to
  hide a mismatch; the corrected test explains the contact ordering.
- `dispatch-movie/run-be_c4j49` passed [1608,1690), then rejected the second
  window's return boundary. The first caller returns to 5F3A; the level loop
  actually returns to 07EC. Static calls at 5F34/07E6 both target F8F2. The
  final recipe hooks both and verifies each pending return and SP+4.
- A later comparator edit initially imported `terrain_cases` before the existing
  test-path bootstrap and failed at import, before execution. Moving the import
  after the established comparison imports fixed it; all three final corpora,
  including explicit original/native unknown-selector failures, pass.

No final failures or skips. These corrections remain distinct from passing
original/native comparisons. Historical counts from session 016 were not used
as current results.

## Reproduction

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py dispatch-probe --disassemble
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py dispatch-compare --rom --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py dispatch-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/genesis_movie_survey.py local/generated/capture-qb2htq3j/recording.json
python3 -B tools/project.py movie-actor-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py reversal-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Build/dispatch-compare/test were repeated with `release` and `sanitize`.
All seven prior `*-compare --rom --preset sanitize` commands were run. Tool
help and earlier session recipes were read before selecting corpora. The local
Musashi harness was explicitly rebuilt; the external Genesis runtime was not.

## Checkpoint review

Explicitly staged and reviewed all 36 owned paths: native dispatch/transaction,
reference allowlists, adapters, authored cases and evidence validators, static
mapping metadata, comparison report references and vault. No unrelated index
content or ROM/movie/binary/bulk capture is staged. All fifteen referenced
report hashes, final test/build logs, dispatch report source/output hashes and
wrapper artifact hashes were verified. Staged files match working files;
whitespace, vault (66 notes) and hygiene (220 indexed files) pass. The final
all-preset test rerun still passes 139 Python tests and 18 CTest targets each.

## Preservation and next handoff

ROM remains 1,048,576 bytes with SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Original BK2 remains
`c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd`.
All 104 external runtime binaries and the separate worker match their frozen
hashes; audit: `local/generated/scheduler-research/preservation.json`.
Owned headless worker contexts close automatically. User GUI, Sonic bridge,
BizHawk sources/runtime and read-only WL3PC were untouched. No package install,
subagent, external rebuild, push or upload occurred.

TASK-0010 stays **in progress**. **Native playability: none.** Next reconstruct
710E/7126 at movie frames 1516–1532, including A148 / 13208 called effects and
shared transition words. Read the fresh survey and finding before widening
scope. Other recorded selectors, world scheduling, shared pools/owner destruction,
audio consumption, rendering and the action/reversal combined capture contract
remain open. No additional user input is needed.
