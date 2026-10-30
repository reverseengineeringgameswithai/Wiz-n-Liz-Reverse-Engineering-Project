---
id: SESSION-2026-10-02-018
type: session
status: completed
---
# Transition actor coasting, shared initialization and timer

Started clean on `work/airborne-update` at
`28045904d4078d2541acfdb4dd084739d68a4ec4`. Read actual entry points, current
status/next/task/finding/session, durable brief, Git rules and Genesis capability/
hook documentation. No existing index/worktree changes or pending Git operation.
The user authorized continuing reconstruction autonomously; no input was needed.

Intended checkpoint: `Reconstruct actor transition coasting and shared timer`.

## Implemented result

710E/7126 now run their distinct A148 coasting, initialize shared transition
state through the immediate 13208 tail and defer the wait handler to a later
invocation. Completion saves requested coordinates to the associated control and
sets the existing shared mode word to 7. A separate native 1345A timer implements
word countdown, signed direction, wrapped level changes and exact endpoint
completion. No palette consumer or implicit world scheduling was added.

`TransitionState` contains typed curve identities and explicit shared/control
state. All actor/presentation/wrapper layers propagate it transactionally; late
service failure rolls back coasting, transition writes and destination/mode
completion. Zero-speed coasting does no terrain work. Pixel count is fixed
before double damping, including the unusual 8000 speed's 64,513 iterations.
Native execution budgets and terrain failures remain explicit.

Seven new mappings bring totals to **78 simulation / 87 indexed functions**,
with **23,511 classified ROM bytes**. Exact scope and limits:
[[03_Reverse_Engineering/findings/FIND-0018-actor-transition]]. Emulation remains
only in research tooling; no CPU emulator enters native runtime targets.

## Verification performed here

- Four new disjoint ranges: **342 bytes / 68 instructions**, all executed in
  restricted original comparisons. Static hashes and closed graph pass, with
  original-68000 sentinels and six new supported GNU checks.
- **306,528 comparisons per debug/release/sanitize preset**, identical output
  hashes: 27,816 actor-flat, 263,352 timer, 4,608 authored terrain and 10,752
  cataloged terrain. Sixteen authored goldens pass. Timer word sweeps are
  independent dimensions; no exhaustive Cartesian claim.
- **144 Python tests, zero skips; 20/20 CTest targets in all three presets.**
  Meaningful failure checks include a second-pixel invalid record, budget
  exhaustion, missing contexts, unknown curves, actor/tracking sequence drift,
  trace overflow/missing returns, and late service failure after both new effects.
- **17 continuous ordinary movie wrapper calls plus 17 separate timer calls**
  at [1516,1533), with exact stack/return boundaries and independent unhooked
  endpoint equality. Handler hits: 710E once / 7126 sixteen times. Completion
  at 1532; saved position 0/48 and mode=7. No memory/register/ROM/input edits.
- Fresh sanitized regressions: **138,149 wrapper, 146,638 actions, 347,320
  presentation, 152,093 actor, 203,586 reversal, 415,940 airborne, 282,233 movement,
  614,436 terrain**. Nine fresh corpora visit **1,020 scoped instructions**,
  including six reference-only sound guards.
- Fresh wrapper movie regression: **191 ordinary / 72 input-branch calls**,
  each with intermediate presentation/handler checks and four independent
  unhooked matches. Earlier 507 actor/presentation and 92 actor / 24 effect
  movie contracts, and the full recording survey, were not rerun in this pass.

Exact final reports/hashes/build/test logs: `re/transition_validation.json`.
New movie: `local/generated/transition-movie/run-i6q8a7yy/report.json`.
Wrapper regression: `local/generated/dispatch-movie/run-f8s_q4o3/report.json`.
Discovery, states, bulk disassembly and build/test logs are ignored under
`local/generated/transition-research/`; corpus/probe/capture reports are in their
corresponding ignored transition directories.

## Exploratory corrections and limits

- The initial mid-coast failure test altered the parsed display `pattern_index`.
  Terrain reads the retained `source_word`, so that fixture did not fail. The
  authored test now corrupts the actual second pixel's map word and verifies
  unchanged actor/scratch. This was a test-fixture correction, not an original/
  native behavior mismatch.
- The installed secondary GNU decoder rejects absolute-long JMP and SUBQ.
  The final probe explicitly records this limitation and corroborates six other
  new instructions. Primary decoding, pinned transfer targets and independent
  original execution cover the rejected decoder forms.
- Discovery confirmed the new wrapper caller is 6986 and timer caller EBF2.
  Both are explicitly captured; no fabricated return or generalized inferred
  call-stack claim was introduced. Actor/control identities and return words are
  checked at every scoped invocation.
- Saved coordinates change externally between frames, and palette dirty is
  consumed before the actor. Native actor/service/tracking persist; shared
  environment inputs are supplied explicitly. The timer and actor checks do
  not claim native rendering, transition entry or whole-frame parity.

No final comparison failures or skipped tests. These corrections are distinct
from passing differential execution. Historical results are not relabeled fresh.

## Reproduction

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py transition-probe --disassemble
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py transition-compare --rom --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py transition-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py dispatch-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Build/transition-compare/test were repeated with release and sanitize. All eight
previous `*-compare --rom --preset sanitize` commands ran after their tool help
and previous recipes were read. The local Musashi harness was explicitly rebuilt;
the external Genesis source/runtime was read-only and never rebuilt.

## Review and preservation

Explicitly staged and reviewed all **34 owned paths**, including native
transactions, original allowlists, typed adapters, authored tests, exact metadata
and synchronized vault. Review tightened coasting call order and timer pre-RTS
checks; the final fresh movie capture and all three test presets still pass.
All fifteen report hashes, current source/build identities and final log hashes
were verified. Staged files match working files; whitespace, vault (**68 notes**)
and hygiene (**233 indexed files**) pass. No unrelated changes or ROM/movie/
binary/state/bulk capture is staged. The commit follows this reviewed index.

ROM remains 1,048,576 bytes with SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Original BK2 remains 2,597 bytes with SHA-256
`c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd`.
All 104 frozen runtime binaries and separate worker match their original hashes;
audit: `local/generated/transition-research/preservation.json`. Owned headless
worker contexts closed normally. User GUI, Sonic bridge, BizHawk source/runtime
and read-only WL3PC were untouched. No package installation, subagent, external
rebuild, push or upload occurred.

## Exact handoff

TASK-0010 remains **in progress**. **Native playability: none.** Next reconstruct
**632A at movie frames 1743–1758** using the prior full-recording survey and new
narrow captures. Derive exact calls/effects/state/return boundaries before adding
its native handler. Other observed unknown selectors: 51C8, 5132, 5188. Preceding
70D2 actor entry, palette conversion, later mode scheduling, general allocation/
owner destruction, sound consumption and full rendering remain open. No new
recording or user input is needed.
