---
id: NATIVE-ARCHITECTURE
type: architecture
status: partial
---
# Native architecture

Native components now include a bounded RNC2 codec and structured pattern-bank
loader, companion scene parsing/headless map composition, and a terrain/contact
and actor movement simulation library. There is no
playable game.
`wiz_rnc2` is a C++20 static library with a span input, explicit size limits,
vector output and precise decode errors. `wiznliz-rnc2` is a headless file/stdout
transport for extraction; Python owns catalog IDs, original ROM validation,
expected hashes, process reporting and atomic publication. Native resource
identity is not a ROM address. No emulator is embedded.

## Selected stack

Use the requested C++20, SDL3, CMake and Ninja stack, with Python 3 for local
analysis, extraction and validation. GCC and Clang both passed a small C++20
feature probe on this Fedora 44 x86_64 host. SDL3 development files are missing;
the installed SDL3 runtime alone is insufficient to build an SDL3 application.
Exact observations and the unexecuted dependency-install command are in
[[02_Workflow/ENVIRONMENT]]. No alternative framework or language is adopted.

The official SDL3 CMake documentation identifies `SDL3::SDL3` as the supported
target and provides system-package discovery with `find_package(SDL3 ... CONFIG)`.
Use and verify the installed revision's APIs when introducing the actual
platform implementation. Documentation consulted is recorded in
[[09_References/SOURCES]]. The headless codec configures successfully; an SDL3
application has not been built.

On 2026-10-05 an engine analysis found no SDL usage in any native target and no
dependency of the simulation, assets or verification on a window, audio device
or engine. [[06_Decisions/ADR-0001-presentation-shell]] proposed binding this C++20
library to a Godot 4.7.2 shell instead; it was **rejected on 2026-10-23**, so
the selected stack above stands: the presentation layer will be SDL3.

## Boundaries for the first implementation

Introduce components only as evidence makes them useful:

- Deterministic simulation consumes explicit input/state and runs without a
  window or audio device. Reconstructed routines carry mappings to ROM evidence
  and independently derived expected behavior.
- Asset loading consumes extracted resources with stable logical IDs. Source
  offsets belong in extraction metadata, not host runtime object identity.
- Rendering, audio and input/platform integration provide host services. Timing
  and simulation stepping remain separate from presentation.
- Mod overrides, saves and configuration gain versioned bounded formats when
  the first actual resources or behavior can use them.
- Narrow compatibility helpers represent only verified arithmetic/data
  semantics. They must not grow into a hidden CPU interpreter.
- Reference emulation remains a research/testing path outside the runtime.

The original profile will preserve verified behavior and form the regression
baseline; enhanced behavior must be explicit and independently tested. Neither
profile currently exists as a runnable interface.

## Build, reference separation and remaining work

`CMakeLists.txt` and `CMakePresets.json` build actual debug/release/sanitize
library, CLI and test targets. `configure` and `build` in `tools/project.py` are
implemented, with no downloads. `test --preset NAME` adds mandatory native
CTest cases; missing/stale builds fail. The wrapper records source and executable
hashes under ignored `build/NAME/provenance.json`. Default extraction uses this
verified build; generic game `run` and broad `extract` remain unimplemented.

The codec's implementation is a declarative prefix grammar with checked cursor
and output operations. Read/write widths and overlap semantics are explicit;
no 68000/Z80 instructions are interpreted. Reference source inspection informed
understanding; no third-party implementation is copied/linked into this target.
This project is not clean-room. Provenance and tested limits:
[[03_Reverse_Engineering/findings/FIND-0006-native-rnc2]].

Pinned ScummVM GPL reference code remains in ignored local research tooling,
separately compiled and launched for comparison or explicit reference extraction.
It is no longer required by the default extraction path. Its unsafe accesses
remain contained by sanitizer/process checks, not accepted in production code.

The codec now maps to original routine `0x19462` through FIND-0007. Its checked
host API replaces valid-stream behavior while refusing unsafe malformed inputs.
The structured loader is now implemented by TASK-0005. Next gate:
[[07_Tasks/TASK-0010-grounded-controller]]. Further movement reconstruction requires observed
state/inputs and independent expected behavior; codec tests do not satisfy that
claim. Add SDL3 rendering/input/audio when evidence and dependencies support a
useful slice. Neither game behavior profile is runnable yet.


`wiz_assets` owns `PatternBank` and `Atlas` without ROM or platform dependencies.
`wiznliz-bank-atlas` is a headless transport; the future SDL3 renderer can consume
indexed patterns and palette state without importing ROM addresses. Pattern-bank
v1 is a legacy asset importer, not a permanent restriction on enhanced resources.
Opaque records and source palette bits survive loading; unknown meanings remain
visible. Palette-update hardware effects, scene flips/priority and analog color
response are excluded from this first diagnostic renderer.

Python owns catalog/hash/path/provenance validation and atomic publication. It
wraps native RGBA in PNG without changing pixel values. Native build provenance
schema2 records all seven executable hashes. `tools/bank_reference.py` is an independent
source-derived specification check, not part of the future native runtime. No
MAME code is linked or executed. See FIND-0008 via
[[03_Reverse_Engineering/findings/FIND-0008-native-pattern-bank]].


`SceneResource` now holds source/translated coordinate pairs, two state starts,
additional patterns/opaque records, dimensions and structured map cells. Logical
base-bank links replace hardware resource addresses. `wiznliz-scene-preview`
consumes two extracted assets and emits a native diagnostic single-plane raster;
Python handles catalog validation, independent specification checks and PNG.
Scene composition preserves H/V flips and alpha. Priority is retained as data;
other layers, entities, camera and gameplay are not simulated.

`relocate_map_word` is a narrowly scoped original-word semantic helper, separate
from native logical pattern IDs. Bounds reject unresolved palette references,
missing patterns and unsupported import shapes. This completes native asset/map
infrastructure for one actual scene resource and exposes the next simulation
boundary. Terrain/contact, horizontal and airborne movement, and bounded landing
transitions now work; the supported grounded dispatcher is described below.
Complete presentation/controller/frame scheduling remains.


`wiz_sim` now owns native deterministic terrain/contact behavior. `TerrainScratch`
models verified persistent query state; `Position`, `TerrainSample`, `Contact`
and `SettleResult` express the semantic contracts without original RAM/register
storage. Narrow word/byte arithmetic preserves wrap and branch flags. Invalid
resource addresses fail before state mutation. The import/query shape remains
128x32 until broader evidence justifies an enhanced world model.

`wiznliz-terrain` is a headless comparison/inspection transport taking extracted
scene/bank inputs and authored case lines. It does not read raw ROM. Pinned
Musashi is compiled separately by an explicit research builder and is used only
by `terrain-compare`, `movement-compare`, `airborne-compare` and `actor-compare`; no normal build/test links or starts it. This establishes
six native terrain/contact routine mappings, including one original movement
primitive, without inventing a controller or frame scheduler. Evidence:
[[03_Reverse_Engineering/findings/FIND-0010-terrain-query]].

`MotionState` and `MotionParameters` now express actor movement independently
of original memory layout. `MotionPresentation` preserves assignments whose
rendering consumer remains unknown; `MotionUpdate::airborne` identifies the next
handler explicitly. The airborne component below now implements that entry. Horizontal movement calls
the existing terrain primitives in original order, preserving scratch and word
semantics. It fixes direction/count at entry and continues after state changes.
State/scratch commit together only after success. Default work limits reject
the exceptional 8000 speed before mutation; an explicit budget permits its
verified 64,513 iterations. The separate `wiznliz-movement` transport enables
resource-based inspection and comparison, without raw ROM or a CPU runtime.
See [[03_Reverse_Engineering/findings/FIND-0011-movement-step]].

`AirborneParameters` and `AirborneInput` extend semantic actor motion with verified
gravity, acceleration, contact damping and control fields. The native airborne
component preserves delay/word overflow, sign-bit decisions, original probe order
and landing state assignments. `MotionState::flags` preserves non-direction bits.
`AirborneResult::immediate_continuation` means the original has reached an idle
handler within the same call; it must not be delayed to a later tick. Grounded
identities are explicit pending work and are rejected by the airborne update API.

The research harness stops before the idle instruction at the exact equivalent
boundary, preserving the pending caller return; no instructions or external
effects are stubbed. Ordinary return and continuation cases are compared as
different outcomes. `wiznliz-airborne` follows up to sixteen airborne handler
invocations, stops visibly on grounded/idle transitions and reports applied
calls. Those are semantic call sequences, not a frame scheduler. All normal
native APIs and tests remain independent of raw ROM and CPU emulation. See
[[03_Reverse_Engineering/findings/FIND-0012-airborne-update]].


## Actor invocation boundary

`ActorState` wraps MotionState with the additional presentation target/cycle
words and logical callback identity. `ActorParameters`/`ActorInput` preserve
verified word/byte semantics. `step_actor` executes a selected handler through
its RTS, consuming supported immediate continuations internally. It does not
advance animation or a game frame. Existing `step_airborne` retains its smaller
contract; the new dispatcher consumes its immediate result in the same call.

The result carries ordered `SoundRequest` values for the jump service boundary.
No audio driver, scheduler or chip synthesis is implemented. State, scratch and
effects publish only on successful completion. Budgets bound continuation work
and terrain loops. Up actions require the explicit shared globals described
below; allocating fast reversal requires explicit owned storage.

`wiznliz-actor` and authored units/transports are ROM-free native targets.
`actor-compare` uses a restricted original Musashi process; `actor-capture`
uses the independent existing GPGX runtime. Neither is linked or launched by a
normal native build/test. Eighteen actor/scratch fields and sound arguments are
compared at real dispatcher boundaries; timing/audio and complete frame parity
are outside that contract. See
[[03_Reverse_Engineering/findings/FIND-0013-actor-dispatch]].

## Presentation before actor selection

`step_presentation` operates on ActorState using logical callback identities.
It preserves byte/word wrapping, compares the old frame to target/endpoints,
advances or loops/bounces, then invokes a supported callback. Unknown dormant
callbacks remain retained; attempting to invoke one fails without state mutation.

`step_scheduled_actor` adds the player's active bit and executes presentation
before selecting the actor handler. Its outer transaction spans both phases,
so a handler/resource/budget failure rolls back callback changes as well. This
maps only F8F6 through F906 or the inactive F90C boundary, excluding the +46
service, other objects and frame timing. It introduces no CPU runtime dependency.

`wiznliz-actor --presentation/--scheduled/--sequence` extend the existing authored
transport (flags follow the four resource arguments). Sequence mode initializes
actor state once, then requires each row's state columns to equal retained native
state. Environment parameters, inputs and shared terrain scratch are supplied
per row; a continuity failure never silently reseeds the actor. The 35-field
input and existing output shape stay unchanged. Presentation-only repeats count
scheduler invocations, not movement handler entries or game frames.

`presentation-compare` uses restricted original execution; `movie-actor-capture`
compares three unedited user-movie windows with independently replayed GPGX.
The standalone `genesis_movie_survey.py` is discovery, not a native comparator.
See [[03_Reverse_Engineering/findings/FIND-0014-presentation-scheduler]].


## Owned fast-reversal effects

`ReversalEffect` stores logical owner, side, position, presentation, target and
flags. `ReversalEffects` supplies bounded host storage, LIFO reuse and generation
checked `EffectId` handles. `ReversalContext` binds an actor invocation to a
store and stable `ActorId`. Successful `ActorResult` values publish spawned
handles. Failed allocation, ownership, terrain or continuation work preserves
actor, scratch and the entire store, including presentation-phase changes.

`advance_presentation` is the shared field-update primitive; callbacks remain
typed actor/effect behavior. `step_reversal_effect` applies activity gating,
presentation/release and X following in original order, including the last
follow after release. Y stays fixed. `ReversalEffects::step` publishes the freed
slot only on success. Stale handles and missing owners reject; double release
does not add duplicate free entries. No hardware address enters native state.

This is a reversal-only store, not an implementation of the complete shared
world pool. Its 4096-slot ceiling is an explicit host work bound. Other object
competition, owner destruction and full scheduling remain unimplemented. The
research reference stops original exhaustion before its non-returning VDP loop;
the native version throws transactionally instead.

The existing actor transport output stays unchanged unless a new reversal mode
is selected. `--reversal` and `--reversal-scheduled` supply a 16-slot authored
store; `--reversal-sequence` retains actor/store state across rows. They append
spawn count and twelve logical fields per spawned effect. `--reversal-empty`
is the exhaustion fixture. `--effect` / `--effect-sequence` accept sixteen
fields and return twelve effect fields, release count and invocation count.
Sequence columns assert continuity. The movie comparator binds effect owner
positions to the already compared native actor outputs. It does not integrate
unimplemented world objects, +46 service, rendering or sound playback.
See [[03_Reverse_Engineering/findings/FIND-0015-fast-reversal]].


## Contextual action presentation and deferred sample request

Up/down actions extend the existing typed actor dispatcher with four logical
handlers and two callbacks. Hold handlers do not integrate motion; their jump
branches only replace the next handler. `ActionGlobals` supplies shared mode,
cooldown and interval words. `ActorInput::raw_buttons` preserves the observed
producer byte; no countdown/producer scheduling is invented inside the actor.
The up effect emits a `SampleRequest` with logical `ActionSample::up_action` and
its two arguments. Original bank/address adaptation belongs to the research
transport; audio-resource extraction and playback remain unimplemented.

`step_actor_presentation` adds the required context to F76C. An invoked A196
callback initializes idle and executes it before returning from presentation.
`step_scheduled_actor` then invokes the newly selected handler, even when that
handler ran inside the callback. Budgets and the outer transaction span both
executions, including shared globals, terrain scratch, reversal storage and all
returned requests. The context-free `step_presentation` rejects invoked A196
instead of discarding its movement/effects. F938 only sets mode 80.

New action transport modes take 43 fields: the old 35 plus mode/cooldown/interval,
raw control byte and four input mailbox words. They append globals, resulting
mailbox and request triples after the old actor/sound output. `--actions-sequence`
retains actor state, asserts continuity and accepts explicit per-call environment
feeds; it does not reconstruct world-global scheduling. Reversal allocations
remain in the separate reversal transport contract, while the C++ API accepts
both contexts. Details: [[03_Reverse_Engineering/findings/FIND-0016-up-down-actions]].


## Actor service and control-coordinate tail

`step_actor_dispatch` extends `step_scheduled_actor` through the wrapper's actual
RTS. `ActorState::service` is a typed logical selector with unsupported default;
only the verified return-only service executes. It is distinct from the new
return-only motion handler. `ActorTracking` stores selector +1A6 and output
coordinates +42/+44; all words preserve original wrap. Actor ownership is an
explicit API reference, replacing the original F8F2 pointer lookup boundary.

The initial active gate covers presentation, handler and service. Tracking runs
even when inactive. No later activity recheck is invented. A successful wrapper
commits actor/tracking/scratch/globals/reversal storage and publishes requests;
late service failure rolls all of them back. The existing narrower APIs retain
their previous scopes and do not silently acquire later service behavior.

AA50 is now a presentation callback using existing `enter_airborne`; it returns
without moving. The scheduled handler performs the subsequent airborne update.
This differs from A196, whose idle continuation executes within presentation.

Research `--dispatch` / `--dispatch-sequence` modes add four fields to the
43-field action transport: service, tracking selector, tracking X/Y. Outputs
append the same four. Sequence mode retains actor/service/tracking coordinates,
asserts their incoming columns and accepts world inputs/selector independently.
The native C++ API can use action and reversal contexts together; the action/
dispatch capture transport still rejects reversal allocation. See
[[03_Reverse_Engineering/findings/FIND-0017-actor-wrapper]].

## Transition context and coasting

`sim/transition.*` provides `TransitionState`, `step_transition_coast`,
`start_transition` and `step_transition_timer`. State includes shared transition
words, typed curve identities and the explicitly bound associated control's
requested/saved coordinates. The caller binds the correct control context;
full actor ownership and multiplayer scheduling remain separate. Mode FF33E0
continues to use `ActionGlobals`, avoiding competing copies of the same word.

All contextual actor/presentation/wrapper APIs accept optional transition state.
Invoked transition handlers require it; wait completion additionally requires
shared action globals. Their transaction includes both, actor, terrain scratch,
tracking and effects. Late service failure publishes no partial initialization
or destination write. Coasting has its own pixel budget and transactional
terrain access, zero-speed no-op and fixed initial count despite per-pixel damping.

`--transition` / `--transition-sequence` extend the 47-field dispatch transport
with thirteen words: direction, countdown, reload, level, three logical curves,
dirty, palette scope, requested X/Y and saved X/Y. Outputs append those thirteen
fields. Sequence mode retains actor/service/tracking; all transition environment
inputs are explicit because observed world code also mutates them. The separate
`--transition-timer` mode runs only the timer and preserves actor/tracking state.
No timer is inferred from an actor tick and no palette rendering is implied.
See [[03_Reverse_Engineering/findings/FIND-0018-actor-transition]].

## Deferred coasting entry

`begin_coasting(ActorState&, ActorTracking&)` models 630A's explicit associated
actor binding. It sets selector FFFF, mode 80, first word 21D and `MotionUpdate::coast`;
all other state, including tracking coordinates, remains unchanged. The next
actor invocation performs the movement and later wrapper coordinate writes.

`MotionUpdate::coast` tails into the existing transactional coasting routine.
It ignores pad state and shared transition completion, and needs neither shared
transition nor action globals. Budget and late-service failures retain the
existing outer transaction. This does not reconstruct the preceding world routine.

Research `--coast-entry` uses the existing 60-field transition transport but runs
only the initializer. `--coast-sequence` executes initialization for the first
row and the complete wrapper for subsequent rows, retaining actor/service/tracking
coordinates and asserting incoming state. Per-call world context remains an
explicit environment feed. `--transition` can execute the new coasting selector
as a standalone wrapper case. The movie comparator binds initialization to P1
using control+0/A4 and verifies A148's pending F906 return. P2 scheduling remains
outside the comparison. See [[03_Reverse_Engineering/findings/FIND-0019-coasting-handler]].


## Tally context

`TallyState` adds an explicit associated remaining-unit counter and shared skip,
countdown, credit, palette-routing and special gates. `ActorInput::start` is
separate from raw buttons. It is appended to preserve older aggregate input
callers. Optional tally context flows through presentation, selected-handler and
full-wrapper transactions; defaults preserve prior callers. Consuming the last
unit returns before mode completion. 51C8's zero-gate branch executes 5222 in the
same invocation and retains its selector. The nonzero gate now has explicit
palette context (below); bonus selection uses explicit table context (below).

Research `--tally` adds six context words and a Start byte to the old 60-field
transport. `--tally-sequence` retains actor/service/tracking and remaining/skip/
countdown/credit, treating incoming columns as assertions. Palette/special gates,
controls, terrain scratch and other world state remain explicit feeds. The native
runtime contains no emulation or bus pointers. The shared trace validators accept
an explicit completion-mode allowlist, empty by default; the tally comparator
permits mode 3 and then compares all modeled shared outputs exactly.
See [[03_Reverse_Engineering/findings/FIND-0020-tally-handler]].


## Fixed tally palette context

`PalettePreparation` contains 16 raw color words and 16 blue/green/red byte
triplets. Its fixed-size conversion is independent of curve evaluation, CRAM
writes or rendering. The associated actor path uses logical `tally` curves and
`tally_palette_wait`; ROM indices and addresses stay in research adapters.
Palette, transition, tally, actor, scratch, tracking and effects copy/commit
through every actor phase, including late service failure. Only preparation
requires palette storage; a busy initial wait and the 5204 handler do not.
The shared transition timer never advances implicitly with an actor call.

`--palette` extends the research transport to 131 numeric fields, with a 1024-byte
line limit. `--palette-sequence` asserts/preserves the destination and tally
counters across calls; palette source and transition fields are explicit world
feeds. Existing transports keep their old shapes. Curve identity 3 is appended;
unknown identities still reject. Source words and intensity triplets are not
presented as a rendered palette. See
[[03_Reverse_Engineering/findings/FIND-0021-tally-palette]].


## Bonus control tables

`sim/bonus.*` defines `BonusSlots`, ordered `BonusAssignment` results and bounded
`allocate_bonus`. It is unrelated to the reversal object store. `TallyState`
optionally owns table state; only 5266 requires it. Host vectors preserve word
contents while replacing bus offsets. Assigned/choice extent, count and cursor
are explicit. The outer actor/wrapper transaction includes table writes, special
gate and sample requests; negative sentinel completion commits partial success,
whereas malformed data, budget exhaustion and late service failure commit nothing.

`ActorBudget::bonus_probes` bounds availability reads and selection-loop entries,
including equality-reset iterations. `ActorResult` reports ordered assignments
and work counts. Presentation's combined actor phase aggregates both and passes
only the remaining budget. No implicit timer tick or actor allocation is added.

`--bonus` / `--bonus-sequence` use 91 numeric fields (1024-byte line limit): the
67-field tally case plus count, cursor, eleven assigned and eleven choice words.
Sequence mode retains/asserts mutable tables/cursor/special gate and prior tally,
actor/service/tracking state. Choices/count and other world state are feeds.
These eleven-word research extents are separate from native host storage bounds.
The alternate 4770 mode is unsupported. Trace validators permit the exact sample
return 5282 only when requested by this capture contract; older defaults remain
unchanged. See [[03_Reverse_Engineering/findings/FIND-0022-bonus-slots]].


## Exit tally and conditional completion

`MotionUpdate::exit_tally` / `exit_tally_wait` append two logical selectors.
`ExitTallyState`, optionally held by `TallyState`, owns the associated marker
and carries explicit secondary gates/count plus equality keys. The existing
unit-consumption helper is shared between the old tally and this new called
path. Its caller can overwrite countdown=60 after the last unit and return;
it cannot collapse that return into transition start. 13208 initializes now,
while the assigned wait handler executes later. Timer scheduling stays external.

All exit fields participate in the existing transaction, including saved
coordinates and mode/marker writes before a failing late service. Unsupported
53F2 rejects after coasting internally but publishes no partial motion/scratch.
`--exit-tally` / `--exit-tally-sequence` use 72 fields and retain/assert the marker,
mutable tally counters and actor/service/tracking. Shared transition state,
equality keys and secondary gates are explicit world feeds. No BCD score state
is invented in this pass. See [[03_Reverse_Engineering/findings/FIND-0023-exit-tally]].


## Packed score state and secondary tally

`ScoreState` is optional tally context with packed score/threshold/increment,
shared arithmetic scratch and a reward word. `add_score` uses bounded native
arithmetic, with eight-digit wrap and explicit invalid-consumed-digit failure.
The single reward decision precedes a separately budgeted threshold loop; its
back-edge never requests another reward. No score saturation is introduced.

`ActorBudget::score_advances` defaults to 4,096 and is consumed across actor
phases, like the existing motion/bonus budgets. State copies propagate through
the full actor transaction. A late service failure rolls back count, score,
threshold, reward, scratch, motion and requests. New sample identity
`ActionSample::score_reward` resolves only in the research resource adapter;
mailbox consumption/audio playback remain separate.

The 77-field `--score-sequence` transport asserts and retains all score fields
and secondary count alongside the existing actor/tally state. Shared gates,
controls, equality keys and world/transition/terrain inputs remain explicit.
A consumed decimal operand with an invalid nibble rejects; unused fields are
not normalized. See [[03_Reverse_Engineering/findings/FIND-0024-secondary-score]].


## One-seed P1 movement session

`ThreeButtonPad` separates logical held buttons from the observed active-low
byte. `PadControl` exposes the verified fields; `actor_input` supplies the actor
adapter. `P1SessionState` owns actor, tracking, scratch, latest control and ordinal.
`P1SessionConfig` pins parameters/gate and supplies explicit work/invocation
budgets. `step_p1_session` converts input before the full wrapper and commits all
state together. No shared global is silently decremented or reset.

The native `wiznliz-session` research CLI uses structured scene/bank resources,
one seed row and physical-only later rows. It has a 600-invocation cap. Start,
up/down world actions and missing world/effect contexts explicitly reject.
The verified movie window has immutable shared inputs and only P1 scratch
writers, checked by per-frame native reference write traces. Broader scheduling,
boot, rendering and audio remain separate. See
[[03_Reverse_Engineering/findings/FIND-0025-p1-session]].
