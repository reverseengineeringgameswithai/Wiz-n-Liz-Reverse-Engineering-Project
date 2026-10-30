---
id: REFERENCE-GENESIS-DEBUGGER
type: reference
status: active
---
# Independent Genesis reference capture

## Interactive GUI performance

For manual gameplay/movie recording on this workstation, use **OpenGL** under
Config → Display → Display Method (`DispMethod: 0`). The isolated installer had
selected GDI+ (`DispMethod: 1`). A controlled GUI comparison at 100% speed measured
2.33 FPS with GDI+ and 60.14 FPS with OpenGL, changing only the display backend
between test configurations. This was a frontend slowdown, not a native simulation
result or a hardware limitation. Changing display method requires restarting
EmuHawk. Preserve active movies/state before restarting. Do not rerun the GUI
installer merely to launch: it would restore the software-renderer setting.

The local isolated configuration now uses OpenGL. Runtime binaries and build ID
are unchanged; Sonic remains untouched. See
[[08_Sessions/2026-10-02-012-gui-performance]] for the saved recording, recovery
boundary and test artifacts. This interactive user GUI is intentionally left
open; headless comparison workers remain independent.

The completed user recording and explicit MD5/SHA1 header adaptation are recorded
in [[08_Sessions/2026-10-02-013-user-movie]]. Its 5,298 input frames replay on two
owned workers with eleven matching covered-state checkpoints. Do not silently
disable movie identity checks or edit the original BK2: use the documented derived
manifest, which retains the original header and verifies the known ROM SHA-256.

The recording now drives native presentation/actor reconstruction:
[[03_Reverse_Engineering/findings/FIND-0014-presentation-scheduler]] and
[[08_Sessions/2026-10-02-014-presentation-scheduler]]. Run
`project.py movie-actor-capture local/generated/capture-qb2htq3j/recording.json`
for 507 continuous actor calls in three pinned windows, with explicit F8FC/F900/
F904/F906 boundaries, stack/selector checks and independent unhooked replay.
Actor state persists; shared scratch/control parameters remain environment
inputs. The standalone `tools/genesis_movie_survey.py` covers selected boundaries
over the complete movie and finds ordinary fast reversal/up/down paths; it is
discovery, not a whole-movie native comparator. Both tools reject trace overflow,
use only owned workers and leave the user GUI/external source/runtime untouched.

BizHawkOpenSource now supplies the independent GPGX replay/debugging worker,
Python JSON client/CLI, MCP adapter and versioned Wiz 'N' Liz profile. Its code
lives under `~/BizHawkOpenSource/Tools/GenesisDebug/`; it is research
tooling outside the native runtime. This note adds a reference workflow to
[[02_Workflow/REPRODUCIBILITY]], without replacing the canonical project tools.
Task: [[07_Tasks/TASK-0011-genesis-reference]]. Session:
[[08_Sessions/2026-10-02-010-genesis-reference]]. Native next task remains
[[07_Tasks/TASK-0010-grounded-controller]].

## Reproduce the observed original-game scenarios

The original remains immutable SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Use the independent runtime; do not deploy into or control the existing Sonic
installation `~/BizHawk-2.11.1-linux-x64` or its bridge port 19420.
Build/setup instructions and the backend capability matrix are maintained in
BizHawkOpenSource's `Tools/GenesisDebug/README.md`.

```sh
cd ~/BizHawkOpenSource
python3 -B Tools/GenesisDebug/wiz/verify_profile.py
python3 -B Tools/GenesisDebug/wiz/capture_scenarios.py
```

The script creates an ignored `Tools/GenesisDebug/local/wiz/scenarios-*/`
directory and prints its report path. It records a fresh-power-on route,
initial held buttons, every input row, exact build/settings, gameplay/end
checkpoints, instruction-boundary trace, audio/video captures, fixture and
native comparison. All workers are owned child processes and closed afterward.
It checks ROM identity before and after. No ROM patch or memory/register edit
is part of this route. Frame N means N completed video frames; input row N
drives transition N to N+1. Input polls and actual actor invocations are counted
separately.

From the WizNLizPC root, compare the generated fixture with the existing native
movement executable through the canonical project entry point:

```sh
python3 -B tools/project.py genesis-compare \
  ~/BizHawkOpenSource/Tools/GenesisDebug/local/wiz/scenarios-5cgmh3hd/routine-fixture.json \
  --preset debug
```

Use the directory printed by a fresh capture when reproducing. The narrow
`tools/genesis_reference.py` wrapper checks ROM identity, then invokes the
external fixture consumer. It adds no emulator dependency to native libraries.
The native source/binary provenance gate must pass; rebuild with the existing
`project.py build --preset debug` only when its provenance requires it.

## Actual evidence

Executed report: `Tools/GenesisDebug/local/wiz/scenarios-5cgmh3hd/report.json`
in BizHawkOpenSource. The tracked non-bulk summary and artifact hashes are in
`Tools/GenesisDebug/wiz/evidence.json`. This capture used build ID
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`, source
baseline `2ce75ef9a5913bc4b6d784d963a7ce40cc0f3140` plus the recorded source hashes,
native GPGX revision `051d430d3d1b54625f9900c8f152d7f232e06daf`. Native image
SHA-256 is `501946f3512831a0d0cb3f154fcf5a5a4a5bde432acce740c4ec810eb54bf66e`;
managed core is `c66e34d56d11b00eb6d09016ef08eef34597c5c49abc32dc00cf5f8c078a050d`.
Exact worker/runtime/host hashes and settings accompany every artifact. Later
builds must make new states; no cross-build state/movie compatibility is promised.

- Reset-to-gameplay reaches frame 1983; 136 further frames cover stable idle,
  right motion, B press/hold/release, midair left reversal, landing, left motion
  and release. All eight semantic scenario checks pass.
- 135 actual `0x9A5E` damping entry/return pairs match the already implemented
  native horizontal-speed effect, including nonzero positive and negative
  speeds. Return PC comes from the captured entry stack and SP must increase
  by four. Only the contracted speed field is compared; CCR/full actor ABI,
  hardware timing and whole-game native replay are excluded.
- Save/load replay and a second independent unhooked power-on replay agree at
  frame 2119: covered-state hash
  `321bf89b4b0bf311c719f63c9cc57c90258b2d984a23b300f67cfd9848980551`.
  This hash covers exposed registers, listed RAM/video domains, frame/lag
  counters and held buttons; it excludes hidden device/CPU and host data.
- The active actor has 136 `0xF904` dispatcher calls in rows 1983–2118,
  408 input-conversion entries at `0x14F22`, and 544 input-poll callbacks.
  One actor call per frame is observed only in this interval. Same-call
  checkpoints are real: frame 2013 enters `A408`, then `AAEA`, then `AB04`
  within one dispatcher invocation. Do not count those as three updates.
- Eleven restored physical-input branches produce 33 checked observations.
  P1 writes the `0xFF0690` control record; P2 writes `0xFF0838`. At producer
  return `0x14F22`, Up/Down/Left/Right map to bytes +1A/+1B/+1C/+1D,
  A/B/C/Start to +1E/+1F/+20/+21. Pressed is FF, released is 00;
  opposing left/right normalize to zero. At this boundary +16 is B OR C,
  +17 is A and +15 is A OR B OR C. Other producer paths must be traced before
  generalizing those combined fields.

## Boundaries and remaining work

The profile pins 33 existing metadata regions and three additional static
dispatcher/input ranges. Physical pad production is now observed in this
configuration; complete input/frame scheduling, named-character mapping and
multiplayer cadence remain open. The original 136-frame route does not hit jump lead `A27E` or fast grounded
`A6C8/A88E`. The later actor capture below adds ordinary branches that hit all
three and compares their newly implemented native paths. Allocating reversal,
actions and full presentation scheduling remain outside native scope.

**Native playability remains none.** No emulator code enters the native game's
runtime, and the new full-machine original capture does not complete the native
controller or scheduler. Continue [[07_Tasks/TASK-0010-grounded-controller]],
using captured registers/state and same-call ordering alongside the existing
restricted Musashi comparison workflow. Consult the BizHawk capability matrix
for unsupported advanced debugger operations and device-model precision.


## Native actor capture extension — session 2026-10-02-011

WizNLizPC now owns `tools/genesis_actor_capture.py`, invoked with:

```sh
python3 -B tools/project.py actor-capture --preset debug
```

It imports the existing read-only worker client and reset recipe, checks actual
capabilities, loaded binary hashes and frozen build ID, and creates owned
headless workers with storage in `WizNLizPC/local/generated/genesis-actor/`.
No external source/runtime rebuild, GUI connection or Sonic bridge access occurs.
The launcher uses its normal ignored publication-lock files; no program bytes
or configuration are changed. All workers close on success or failure.

The final report is `local/generated/genesis-actor/run-cnph4jtf/report.json`
relative to WizNLizPC. `re/actor_validation.json` pins report, trace, comparison
and checkpoint-sidecar hashes. The build remains
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`.

| Branch | Provenance | Matched actor invocations |
| --- | --- | --- |
| Existing 136-frame route | Ordinary gameplay, no edits | 136 |
| Idle B press/hold/release | Ordinary gameplay, no edits; hits A27E | 13 |
| Right hold then B | Ordinary gameplay, no edits; hits A6C8 | 61 |
| Left hold then B | Ordinary gameplay, no edits; hits A88E | 71 |
| Zero-speed right landing | Explicit actor RAM edits at frame 1983 | 1 |
| Zero-speed left landing | Explicit actor RAM edits at frame 1983 | 1 |

**283/283 comparisons pass** across eighteen actor/scratch fields and ordered
sound request arguments. This expands the previous speed-only contract; it
still does not compare complete frames or audio playback. Each F904/F906 pair
has the same A5/A6/SP, an observed selected-handler entry with SP minus four and
a captured F906 return address. It uses explicit boundaries rather than general
call-stack inference. Duplicate/out-of-order events, mismatched stacks, missing
boundaries, drops/overflow and hook errors reject evidence.

All six runs match replay from the same checkpoint with hooks disabled and the
same recorded edits. Frame-end save/load rules are preserved. Ordinary and
experimental provenance are kept separate. The new capture does not independently
repeat the physical-input probe suite; the previous 33 observations remain
historical evidence. The supplied damping fixture was separately rechecked:
135/135 passes, still only scalar speed comparisons.

The captured terrain map/records are checked unchanged across each window and
translated into native logical resources; unused pixel/header content is authored
zero data. Every native invocation starts from its captured entry fields. This
is per-invocation parity, **not** a continuous native replay that also computes
the intervening presentation scheduler. Next work is the F76C scheduler and its
callbacks: [[07_Tasks/TASK-0010-grounded-controller]].


## User-movie reversal extension — session 2026-10-02-015

`tools/genesis_reversal_capture.py` / `project.py reversal-capture` now compare
ordinary user-movie windows [1048,1090) and [2170,2220), with the unchanged frozen
worker and no edits. Ninety-two continuous actor calls and 24 dependent-effect
updates pass, including both allocations/releases, owner backlinks and release
before final follow. Native effect owner positions come from the compared actor
output. The two declared covered-state endpoints match fresh unhooked workers.
The previous 507 actor / 507 presentation windows also pass a fresh rerun.

The new recipe validates allocator pop/initializer/return, helper completion,
F76C entry, presentation return, follow and post-handler boundaries. Selected
hooks reject overflow, incomplete lifetimes, uncontracted writes and continuity
breaks. It uses explicit stack/return words rather than general call inference.
This supersedes older outstanding allocating-reversal statements for the bounded
scope in [[03_Reverse_Engineering/findings/FIND-0015-fast-reversal]]. Complete
world object competition, later +46, rendering/audio and up/down actions remain
outside native scope. Evidence: `re/reversal_validation.json`.


## Up/down action extension — session 2026-10-02-016

`project.py actions-capture local/generated/capture-qb2htq3j/recording.json`
compares 184 continuous scheduled actor calls and 184 intermediate contextual
presentation checks in unedited intervals [1615,1690) and [3230,3339). Two
separately recorded input branches from completed frame 3258 supply 72 more of
each check, covering Up+A's mailbox request and Up+B / Down+B deferred jumps.
There are no RAM/register/ROM edits. Every window/branch endpoint matches a
fresh independent unhooked worker on the frozen generation.

The raw control +14 bit 6 clears for the observed Up+A branch; its up handler
checks this after +16 jump and shared mode/cooldown gates. This remains scoped
to the verified ordinary three-button producer/configuration. Native comparison
includes actor fields, contextual callback effects, shared globals and four
mailbox words/ordered request arguments. It excludes audio consumption/playback,
world timer scheduling and full frames. Native actor state persists; controls,
parameters, globals/mailbox and scratch remain environment feeds.

The initial wider research interval [1608,1690) exposed a 12646 handler and AA50
presentation callback before 1615. The later original route allocates a reversal
at 3339; reversal lifetimes retain a separate comparator. Those phases are not
silently omitted inside an asserted continuous action window. Exact evidence,
corrected attempts and next task: [[03_Reverse_Engineering/findings/FIND-0016-up-down-actions]],
[[08_Sessions/2026-10-02-016-up-down-actions]], `re/actions_validation.json`.
Both older movie contracts pass a fresh rerun; prior up/down-outstanding claims
are superseded for this bounded scope. Native playability remains none.


## Bounded actor wrapper through caller return (session 017)

`tools/genesis_dispatch_capture.py` / `project.py dispatch-capture` extends the
action contract to [1608,1690), keeps [3230,3339) and the two explicit input
branches. **191 ordinary + 72 branch calls** pass through the actual caller RTS,
with matching intermediate presentation/selected-handler checks. 12646 is verified
as return-only handler/service; AA50 initializes before same-call airborne work.
F906/F90A load/invoke +46, F90C resumes, and the coordinate tail returns to 5F3A
or 07EC. The validator checks exact pending return, SP+4, owner, selected A0,
control writes, actor/tracking continuity and trace completeness.

Four fresh independent unhooked endpoints match. Movie evidence is active P1
with tracking selector zero; inactive and FFFF-sentinel behavior are covered by
restricted original execution and authored tests. The actor/service/tracking
sequence persists, while controls/parameters/globals/mailbox/scratch/selector are
external inputs. No full-world, hidden-device or audio equivalence is claimed.
The original F8F2 owner-pointer lookup remains an explicit adapter boundary.

Fresh report: `local/generated/dispatch-movie/run-zefqb8xw/report.json`.
The expanded `tools/genesis_movie_survey.py` additionally reads the selected +46
value at F90A and verifies A0. Its fresh full-recording report
`local/generated/movie-survey/run-gxfthj5e/report.json` sees 4139 return-only
service selections and matches the recorded unhooked final baseline. This is
**discovery only**; unknown motion selectors remain. The next lead at that checkpoint was 710E/7126
at frames 1516–1532. Exact native scope and artifacts:
[[03_Reverse_Engineering/findings/FIND-0017-actor-wrapper]],
[[08_Sessions/2026-10-02-017-actor-wrapper]], `re/dispatch_validation.json`.


## Transition actor and separate timer capture (session 018)

`project.py transition-capture` / `tools/genesis_transition_capture.py` replay
[1516,1533) of the same preserved movie without input/state edits. Seventeen
continuous native actor-wrapper calls and seventeen separate timer calls match.
710E executes once, 7126 sixteen times; the timer runs before the actor and
completion occurs at frame 1532. Hooks retain F906 across the 13208 tail and
check actual wrapper/timer returns to 6986/EBF2 with stack balance. No inferred
call-stack reconstruction or arbitrary instruction-state checkpoint is used.

Independent unhooked replay matches the final canonical hash and declared scope.
The comparator checks actor/service/tracking continuity and shared transition
fields between selected boundaries. Other world code clears dirty and changes
saved coordinates between calls; those effects are external feeds. Native timer
support excludes the palette consumer, renderer and world mode scheduler.
Evidence overflow, missing boundaries and uncontracted writes reject.

Final report: `local/generated/transition-movie/run-i6q8a7yy/report.json`.
Fresh prior wrapper regression: `local/generated/dispatch-movie/run-f8s_q4o3/report.json`
(191 ordinary and 72 branch calls, four unhooked endpoint matches). Original ROM,
movie, frozen build and 104 runtime binaries plus worker were rechecked; the
external source/runtime, user GUI and Sonic19420 were unchanged.
[[03_Reverse_Engineering/findings/FIND-0018-actor-transition]],
[[08_Sessions/2026-10-02-018-actor-transition]], `re/transition_validation.json`.
At that checkpoint the next unsupported handler was 632A; resolved below. Native playability: none.


## Deferred coasting initialization and actor capture (session 019)

`project.py coasting-capture` / `tools/genesis_coasting_capture.py` use the same
pinned unedited recording at [1742,1759). P1's 630A initializer runs after its
ordinary actor update in frame 1742, using control+0/A4 while A6 names another
object. It returns to 62F8; the following sixteen 632A wrapper calls return to
5F3A. A148 tail execution keeps the F906 return and SP unchanged until RTS.

The native sequence runs initialization first, then each wrapper without
reseeding actor/service/tracking. World context remains explicit. Tracking
selector changes at initialization; tracking coordinates change only in the
next wrapper. One P1 initializer and all sixteen updates match; independent
unhooked replay matches the covered-state endpoint. P2 initialization is observed
in the trace but is not a native P2 comparison. Surrounding world-object writes
and the later shared transition initialization are separate scope.

Final coasting report: `local/generated/coasting-movie/run-g7vzhcyq/report.json`.
Fresh transition and wrapper regressions:
`local/generated/transition-movie/run-son5h9w7/report.json` and
`local/generated/dispatch-movie/run-v23xeorr/report.json`.
The capture runner now accepts explicit recipe/comparator/window parameters;
all three contracts retain exact loaded identity, complete inputs, overflow
rejection and independent unhooked verification. No GUI/port or external-source
changes were made. [[03_Reverse_Engineering/findings/FIND-0019-coasting-handler]],
[[08_Sessions/2026-10-02-019-coasting-handler]], `re/coasting_validation.json`.
At that checkpoint the next handler was 51C8; its zero-gate path is covered below. Native playability remains none.


## Bounded tally movie capture (session 020)

`project.py tally-capture` / `tools/genesis_tally_capture.py` capture [3403,3578)
from the same pinned unedited movie. All 175 wrappers compare continuously,
including five sound requests and completion at frame 3577. Native remaining,
skip, countdown and credit persist, alongside actor/service/tracking. Controls,
scratch and other world state remain explicit inputs. No movie/RAM/register/ROM
edits; an independent unhooked replay matches the declared covered-state endpoint.

51C8 -> 5222 and 5222 -> 537C retain the same F906 pending return. A148 returns
to 522C, AF98 to 53AE, sound request to 53D4, and the full wrapper to 7EC. Complete
selected boundaries and overflow checks distinguish these from frame scheduling.
The movie does not hit the nonzero palette branch 51D0 or special allocation 5266;
that checkpoint rejected both. Session 021 now implements the palette branch
using the explicitly controlled experiments below; session 022 adds 5266.

Evidence: `re/tally_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0020-tally-handler]],
[[08_Sessions/2026-10-03-020-tally-handler]]. Fresh coasting, transition and wrapper
movie regressions retain their own scopes and unhooked comparisons. External
source/runtime, user GUI and Sonic19420 remain untouched.


## Controlled tally palette experiments (session 021)

`project.py palette-capture` / `tools/genesis_palette_capture.py` branches from
completed movie boundary 3403 with explicit compare-and-write RAM edits. The
ready scenario changes only FF33CE; the initial-wait scenario also changes
three transition words and fills the 48-byte destination with A5. It compares
17 and 20 continuous P1 wrappers respectively, with source/destination extents,
other palette banks and exact nested returns checked. Both endpoints match
fresh independent workers repeating the identical edits and inputs without
hooks. These are controlled experiments, not ordinary gameplay observations.

The script pins input/start/build identity and records exact old/new bytes and
worker edit receipts. After mutation it advances explicit movie rows directly;
it does not seek/export the unedited ReplaySession as if it described those
edits. Trace overflow rejects evidence. Source movie, ROM and frozen runtime
remain unchanged. Palette rendering/consumer and whole-frame parity are not
claimed. Evidence: `re/palette_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0021-tally-palette]],
[[08_Sessions/2026-10-03-021-tally-palette]].


## Controlled bonus-table experiments (session 022)

`project.py bonus-capture` / `tools/genesis_bonus_capture.py` branches from
completed boundary 3403. Each experiment sets remaining, skip and special gate
to zero and advances genuine A+C+Start once. Additional prefilled slots/cursor
edits distinguish five assignments, two assignments after equality-reset, and
an already-full table. Initial B+C+Start discovery did not select 5266 and is
not counted as bonus evidence. The successful input producer yields raw 1F.

Each trace checks the complete P1 wrapper, sample helper return 5282, the
six-byte selection call stack (saved D7 word plus return), scan flags/reads and
ordered table writes. Native assigned words, cursor, gate, sample request and
all prior wrapper fields match. Fresh independent workers repeat identical
RAM edits and input without hooks; all three covered-state endpoints agree.
All artifacts, receipts, identities and explicit input rows are pinned; after
mutation no unchanged ReplaySession seek/export is used. Overflow rejects.

These are controlled RAM/input experiments, not ordinary gameplay observations.
The selected 451A/4770 D2=0 paths use tables in the associated control, not a
shared actor allocator. Table consumers, other selector mode, audio playback
and whole-frame parity remain excluded. Fresh ordinary tally, transition,
coasting and 191 ordinary / 72 input-branch wrapper contracts, plus both palette
experiments, also pass. Evidence: `re/bonus_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0022-bonus-slots]],
[[08_Sessions/2026-10-03-022-bonus-slots]]. External sources/runtime, user GUI,
Sonic19420, original ROM and BK2 are preserved.


## Exit-tally movie and equality experiment (session 023)

`project.py exit-tally-capture` compares the unchanged movie at [4807,5038):
215 calls to 5132 and 16 to 5188, two sound requests, delay=60 at 4933,
transition start at 5021 and mode=1 completion at 5037. Exact nested returns
show 537C is called at SP-4/5146, with its helpers at SP-8, whereas the older
5222 path tail-enters it. 13208 still returns directly to F906; 5188 is deferred.
Actor/service/tracking, tally counters and marker persist natively throughout.
The independent unhooked endpoint matches. World feeds remain explicit.

`--equal-marker-experiment` runs one controlled wrapper at [5037,5038), editing
FF070C to FFFF and FF33CC to the current FF33C8 word. The input row is unchanged.
The expected marker clear is observed at 51BA and matches native output. A fresh
unhooked worker repeats exact edits/input and matches the covered-state endpoint.
Edits/receipts, identity, input and artifacts are pinned; no unchanged replay
seek/export occurs after direct mutation. This is not an ordinary equality hit.

A fresh 5298-row selected-PC survey observes 4,139 P1 calls/services, no handler
address outside the registered table and only 12646 services. Its endpoint
matches the recorded unhooked baseline. This is discovery with zero native
comparisons, not a whole-movie native test. Ordinary and controlled captures
retain their separate contracts and overflow rejection. Evidence:
`re/exit_tally_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0023-exit-tally]],
[[08_Sessions/2026-10-03-023-exit-tally]]. ROM/movie/runtime and user GUI/Sonic
remain preserved. 53F2, full-world timing, rendering and audio playback stay open.


## Secondary-score experiments (session 024)

`project.py score-capture` branches from preserved movie boundary 4934 into four
explicit RAM/input experiments. The eight-call branch consumes two secondary
units with two sample requests, four then one threshold advances and persistent
native score/count/scratch. Three one-call branches cover equality without award,
eight-digit score wrap and word reward-counter wrap. Total: eleven wrappers,
five tally sounds, three samples, six threshold advances. This is controlled
experiment evidence, not ordinary score hits.

Every experiment pins exact compare/write receipts, neutral input rows, start
state, settings/build and source hashes. Four independent unhooked workers repeat
identical edits/input and agree at declared covered-state endpoints. No trace
overflow. Deeper sample stack S-32/AF44 and threshold calls S-12/AE40 are checked
explicitly. The ordinary up-action sample/default snapshot contracts remain
strict; only the score validator enables its alternative ABI/control writes.
All affected replay contracts were rerun after review tightened snapshot extents.

Evidence: `re/score_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0024-secondary-score]],
[[08_Sessions/2026-10-05-024-secondary-score]]. External source/runtime, original
ROM/BK2, GUI and Sonic19420 remain untouched. No renderer or audio playback parity.


## One-seed P1 session (session 025)

`project.py session-capture` uses unchanged movie `[3100,3200)`: 100 wrappers,
600 conversions, 800 polls and 100 inactive transition-timer calls. This differs
from the earlier reset-route cadence and is scoped to this window. Producer
caller stacks identify P1/14DEE, P2/14E38, P1/313A, P1/14DEE, P2/14E38, P1/7DA,
then the wrapper returns to 7EC. No general call-tree inference is required.

Native write/poll traces drain every frame (108,064 events total), while managed
selected-instruction hooks capture exact boundaries. All 892 scratch writes
are corroborated inside P1 terrain queries. Access-event PCs are callback-time
CPU PCs, not instruction-entry PCs. Immutable shared inputs and collision
resource/address fields have write guards. Overflow/drops reject completeness.

One initial seed/resources and physical held-button rows drive native output;
there are zero per-call environment feeds. All 100 actor/scratch/tracking/control
outputs and four sound requests match per preset. Three fresh independent
unhooked endpoints agree in the declared covered-state scope. This does not
integrate the inactive timer or other world objects, nor claim rendering/audio.
`re/session_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0025-p1-session]] pin scope/provenance.
