---
id: TASK-0010
type: task
status: in_progress
deliverable: Resolve immediate idle continuations and grounded motion handlers into an explicit native actor update dispatcher
acceptance: ["Trace 0xA1BE and 0xA246 including their calls, same-call transitions and input dependencies", "Validate landing-selected grounded handlers at 0xA408, 0xA546, 0xA6C8 and 0xA88E and the jump-entry lead at 0xA27E with exact ranges and explicit effect boundaries", "Consume the pending idle continuation without delaying it to another tick or silently skipping its behavior", "Implement only verified handler paths and expose any remaining understood continuation explicitly; unknown effects must reject", "Compare authored control sequences and cataloged terrain using original execution, including landing-to-idle and jump-to-airborne transitions", "Keep physical pad mapping and frame scheduling claims separate, run sanitizer/regression checks, and commit synchronized Git and Obsidian"]
---
# Continue the actor state machine through grounded motion

Current checkpoint: [[08_Sessions/2026-10-23-055-scene-change]] and
[[03_Reverse_Engineering/findings/FIND-0052-scene-change]]. **In progress**:
substantial native behavior is implemented, but the complete controller is not.
Component validation counts below retain their historical pass; the latest
session results and next task are stated in the final sections and current status.

## Implemented actor dispatcher

`src/sim/actor.*` now consumes zero-speed landing's immediate idle continuation
within the same invocation. Supported idle, normal/fast ground, idle turns,
normal reversals, drop helper and jump paths execute through their return.
Handler assignments followed by RTS remain deferred. Jump's delay/impulse and
first airborne update happen immediately, with explicit ordered sound requests.
Seventeen new bounded mappings join the previous 22 simulation mappings.

`re/actor_update.json`, `tools/actor_probe.py`, `tools/actor_compare.py` and
`tools/genesis_actor_capture.py` retain exact scope, static evidence, original
execution and real-game actor comparisons. The actor transport includes all
presentation fields/callback assignments, scratch, motion and sound requests.
Unknown effects and work-budget/resource failures preserve state and scratch.

Independent full-machine capture **exists**. The new ordinary routes hit
`A27E`, `A6C8` and `A88E`; edited landing cases separately verify both same-call
idle continuations. Physical pad fields are verified for the observed USA
three-button producer at `14F22`. Older statements that full-machine reference
capture and all physical input mapping were outstanding are superseded by
[[09_References/GENESIS_DEBUGGER]]. Broader scheduling/modes remain unverified.

## Implemented presentation phase

`step_presentation` now implements F76C and callbacks A2E8/A380/A50E/A654/A774/A93A.
`step_scheduled_actor` performs the active gate, presentation and newly selected
handler in one transaction. It retains countdown/frame/cycle wrap, target timing,
loop/bounce order and same-call callback-to-ground transitions. Unknown invoked
callbacks still reject. The older `step_actor` API keeps its handler-only scope.

347,320 comparisons pass in each native preset, with all 90 new instructions
visited. The user's recorded input route supplies 507 continuous scheduled actor
comparisons and 507 separate presentation boundary comparisons. Native actor
state persists throughout each window; only environment controls/parameters and
shared scratch are supplied anew. All three windows match independent unhooked
replay at their declared covered-state boundaries. See the current finding.

## Implemented fast reversal and owned effects

`step_actor` / `step_scheduled_actor` now support A7A8/A96E through immediate
A7EC/A9B2 execution with an explicit `ReversalContext`. The native effect store
uses typed owner IDs, bounded allocation, LIFO reuse and generation guards.
Both completion callbacks and dependent object lifetimes are implemented.
The final follow still executes after the release callback within that same
object invocation; spawn Y is retained. Failure after internal allocation rolls
back actor, scratch and effect storage. Missing storage/exhaustion reject.

203,586 original/native cases pass per preset, including all 119 new instructions,
ten authored goldens and exact original/native exhaustion boundaries. The movie
supplies 92 continuous actor calls and 24 complete effect updates across ordinary
windows [1048,1090) and [2170,2220), matching independent unhooked endpoints.
The previous 507-call actor/presentation windows also pass freshly. The new pool
is scoped to reversal objects; full shared object competition remains open.

## Implemented up/down actions

Up/down entries and hold/release handlers now execute natively. F938 freezes only
animation mode; A196 enters facing-selected idle within presentation, then the
wrapper executes the newly selected handler again. Hold jumps assign A27E and
return, preserving the deferred boundary. Explicit shared globals, raw +14 bit 6,
wrapped arithmetic and a logical sample request implement the up action's gated
mailbox effect. Requests/global/actor/scratch/effect changes roll back together.
Context-free presentation rejects the contextual idle callback.

146,638 cases pass per preset with eighteen authored goldens and all 81 new
instructions. The movie supplies 184 continuous actor calls / presentation checks;
two input branches add 72 of each, with zero memory edits and four independent
unhooked endpoint matches. All six prior corpora and both prior movie contracts
pass freshly. Audio consumption and complete world timing remain excluded.

## Implemented bounded wrapper through return

The verified 12646 RTS now has explicit handler/service identities; AA50's
presentation callback initializes airborne, then the wrapper executes the newly
selected handler in the same call. The native wrapper includes +46 invocation
and the wrapped control-coordinate tail through actual RTS. Inactive actors
still update tracking. Unknown invoked services reject transactionally, including
after sample requests or reversal allocations. The original F8F2 pointer lookup
remains an explicit ownership adapter boundary.

138,149 cases pass per preset, with thirteen authored goldens and all fifteen new
instructions. The recording supplies 191 ordinary wrapper calls and 72 explicit
input-branch calls, each with presentation/handler checks and independent
unhooked endpoint agreement. All seven previous corpora and both older movie
contracts pass freshly. Native playability remains none.

## Implemented transition handlers and timer

710E/7126 now coast through A148, start the shared transition and wait for its
completion. Starting tails through 13208 immediately but defers 7126; completion
saves requested coordinates to the associated control and sets shared mode=7.
A148 has a fixed initial pixel count and double damping, distinct from ordinary
movement. A separate native 1345A timer preserves word wrap and exact endpoints.
Typed transition context commits transactionally with actor, globals and tracking.

306,528 cases pass per preset, all 68 new instructions and sixteen goldens.
The unedited movie supplies 17 continuous actor and 17 separate timer comparisons
with an independent unhooked endpoint match. All eight previous corpora and the
191 ordinary / 72 input-branch wrapper contract pass freshly. Current totals:
78 bounded simulation mappings / 87 indexed functions. Palette conversion and
world mode dispatch remain outside the implemented timer/actor contract.

## Implemented deferred coasting entry and handler

630A now initializes the explicitly associated actor's mode/first word/handler
and tracking selector, preserving the remaining state and deferring movement.
632A executes the existing A148 coasting immediately as a tail, retains itself,
and ignores shared transition completion and pad state. No shared action or
transition context is required. Unknown late service rolls back the wrapper.

87,571 original/native cases pass per preset, with eleven goldens and all eight
new instructions. The recording supplies one initializer at 1742 followed by
16 continuous wrappers at 1743–1758, with independent unhooked equality. Nine
prior corpora and both prior movie contracts pass freshly. Totals are now
80 bounded simulation mappings / 89 indexed functions. P2 initialization is
observed but not compared; the surrounding world routine remains separate.

## Implemented bounded tally path

51C8's zero-gate branch now executes 5222 in the same invocation, then coasts,
counts remaining units, accumulates wrapped/capped credit and waits for Start.
537C preserves signed countdown and the one-time shared-skip bypass; consuming
the last unit does not complete the mode until a later call. Sound requests and
all shared state commit with actor/tracking/scratch. At that checkpoint the
palette and bonus paths were unsupported; both are now implemented below.

231,475 comparisons pass per preset, nineteen goldens and all 48 new instructions.
The preserved recording supplies 175 continuous wrappers, five sound requests
and completion at 3577, matching independent unhooked replay. Counters persist
through the native sequence. Totals: 83 bounded simulation mappings plus two
partial tally-handler mappings / 94 indexed functions. Neither partial handler
is claimed fully implemented. See the current finding for exact intervals.

## Implemented tally palette path

The nonzero 51D0 path now coasts/waits, converts exactly sixteen color words to
B/G/R triplets, initializes the tally transition and assigns deferred 5204.
5204 coasts/waits and assigns deferred 5222. The original same-call zero-gate
branch is unchanged. Palette state commits with every actor/context field;
late service failure, missing contexts and budgets roll it all back.

214,448 comparisons per preset, sixteen goldens and all 56 new instructions
pass. Two explicitly edited movie experiments compare 17 and 20 continuous
wrappers and match independent unhooked endpoints. The ordinary 175-call tally
regression also passes. Totals: 87 bounded simulation mappings plus two partial
tally handlers / 98 indexed functions. Native playability remains none.

## Implemented bonus-table path

5266 now requests the existing sample, sets FF0104 and fills up to five empty
control-owned slots through 451A/4770 D2=0. This is table assignment, not object
allocation. Negative-sentinel exhaustion commits partial success. Word arithmetic,
equality-only cursor reset, source zero/negative values and exact same-call
completion are preserved. Missing context, bounds/budgets and late service
failure roll back tables, gate, requests and all prior actor contexts.

160,680 comparisons pass per preset, sixteen goldens and all 43 new instructions.
Three controlled RAM/input experiments from the preserved movie demonstrate
five writes, partial/reset completion and exhaustion, with independent unhooked
matches. Twelve prior corpora and applicable movie regressions pass freshly.
Both tally mappings are now bounded; 4770 remains partial for its other mode.
Totals: 90 bounded simulation mappings plus one partial selector / 100 indexed
functions. Native playability remains none.

## Implemented bounded exit tally and wait

5132 now calls the shared tally helper and sets countdown=60 on consuming the
last unit, then returns. Later Start/skip initializes the existing transition
immediately and assigns deferred 5188. 5188 coasts/waits, saves requested
coordinates, conditionally clears the associated marker and sets mode=1.
That initial scope left secondary-score branch 53F2 explicitly unsupported;
the secondary-score pass below supplies its bounded implementation. The shared
timer never advances implicitly.

348,668 comparisons per preset, 22 goldens and all 31 successful new instructions
pass. The ordinary recording supplies 231 continuous wrappers; one separately
edited equality experiment covers marker clearing. Independent unhooked endpoints
match. Thirteen prior corpora and applicable movie regressions pass freshly.
Totals at that checkpoint: 91 bounded simulation mappings plus two partial
mappings / 102 indexed functions. 5132 was the second partial mapping; the next
section supersedes that state. Native playability remains none.

## Implemented secondary tally and score

53F2's valid packed-decimal path now consumes the secondary count, adds decimal
10,000 with eight-digit wrap, conditionally requests one reward and advances
threshold until sufficient. Equality does not award; the counter only stops at
exactly 9. A 4,096-step default budget bounds threshold loops. Missing context,
invalid consumed digits, nontermination and late services roll back state and
requests. The last unit returns with countdown=3 before a later transition.

328,916 original/native comparisons per preset, 20 goldens and four controlled
movie branches / eleven wrappers pass. Independent unhooked endpoints agree.
Totals: 97 bounded simulation mappings plus one partial / 107 indexed functions.
5132 is promoted; 4770's alternate mode remains partial. Native playability is none.

## Exact next bounded pass

Superseded historical text formerly named the 78EE/AC5E pass, now delivered
below. The current next pass **continues the native setup from 68C4 with the
four gated pair initializers**, stated in the final section and
[[01_Project/NEXT_ACTIONS]]. Keep callback79B6, 7AD6,
overlap-hit FF31C0 readers, gate producers and collision-hit7910 unsupported. Preserve
physical-only later inputs, retained state, allocation order and rollback.

## Acceptance still open

The scoped dispatcher, immediate/deferred distinctions, jump transitions,
original/native comparisons, physical-evidence separation and sanitizer checks
are delivered, along with the bounded presentation scheduler and callbacks.
Bounded fast reversal and its dependent objects, plus up/down actions and their
mailbox effect, now also pass. The measured wrapper tail is now implemented, but wider shared services and
world/input scheduling are incomplete. Do not mark this task complete or
describe the native controller as fully playable. Preserve the historical airborne component's
bounded API: `step_airborne` still returns its explicit continuation; callers
needing the supported handler invocation should use `step_actor`, and callers
including the preceding presentation phase should use `step_scheduled_actor`.

After this controller work, extend measured scheduling beyond the captured
single-player interval and build a bounded SDL3 input/render/audio slice toward
M3. SDL3 development files were absent at the earlier check; recheck when needed.
Native playability remains none;
original/enhanced profiles are not runnable.

For the verified +46 service and control-coordinate tail through actual return,
use `step_actor_dispatch` with explicit `ActorTracking` and service identity.


## Retained P1 session and native physical input

14E4E now has a native stateless converter: 214 bytes / 54 instructions,
1,024 original comparisons in each preset. A new P1 session owns actor,
tracking, control, scratch and invocation ordinal with one initial parameter/
resource seed, then physical held sets only. All 100 wrappers in unchanged
movie `[3100,3200)` and four ordered sound requests match in every preset.
600 producer calls, 800 polls and 100 inactive timer calls are counted separately.
All 892 scratch writes are the P1 query; write-level guards reject mutation of
fixed shared inputs/collision data. Independent unhooked endpoints agree.

179 Python tests (zero skips), 34 CTest targets per preset and six sanitized
regression corpora pass. Total: 98 bounded simulation mappings plus one partial /
108 indexed. GNU's memory-BTST decoder limitation is documented, not hidden.
Evidence: `re/session_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0025-p1-session]].

At session 025: pause/up/down world actions, allocating effects and
transition/tally scheduling were not integrated. The next section resolves the earlier scratch gap without per-call reseeding. Native playability
remains none; this pass supplies an initialized headless session, not game boot.


## Level banner and earlier retained session

63E2 now emits native centered-label and optional number requests, preserving
word wrap and its shared scratch-Y write. The earlier inter-call writer was the
banner, not another terrain-query actor. It executes before input/P1 in the
session; failed later work rolls the phase back. FUNC-0109 adds 25 native-scope
instructions. Rendering callees execute only in restricted research.

66,880 banner comparisons per preset and 367 one-seed early wrappers per preset
pass, including 367 banners and twelve sound requests. Two fresh ordinary
worker captures independently match unhooked endpoints; debug revalidates one
of those captures. The late 100-call session also passes a fresh debug replay.
181 Python tests, 34 CTests per preset and seven sanitized regressions pass.
`session-compare` verifies saved capture hashes/contracts before comparing a
fresh native build, avoiding unnecessary repeated instrumented replays.

Totals: 99 bounded simulation mappings plus one partial / 109 indexed. Evidence:
`re/banner_session_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0026-level-banner-session]]. Native
playability remains none. At session 026, allocation/effect ownership beyond
frame 1067 was the next integration step; the following checkpoint implements it.


## Retained reversal session

The session now owns a bounded optional P1 reversal pool and updates active slots
after the full wrapper, including birth and release invocations. Native actor,
control, tracking, scratch, ordinal and pool commit or roll back together. The
single 36-field seed is followed only by physical held masks. Ordinary movie
[700,1090) passes 390 wrappers, 390 banners, twelve sounds and one complete
twelve-update reversal lifetime in all presets, using one fresh original capture
and its independent unhooked replay. Both facings/slot reuse/failure boundaries
have authored tests and fresh 203,586-case reversal comparisons per preset.
184 Python tests and 34 CTests per preset pass; eight sanitized regressions pass.

Shared original pool competition remains observational: 38 foreign allocations,
36 foreign releases and 47..53 available pointers excluding the zero sentinel.
Do not claim shared capacity or allocation-order parity for the dedicated native
pool. Three context fragments add 28 classified bytes; mapping totals stay 99
bounded plus one partial / 109 indexed. See
[[03_Reverse_Engineering/findings/FIND-0027-retained-reversal-session]] and
`re/effect_session_validation.json`. TASK-0010 remains in progress and full
native playability remains none.


## Trail allocator client and spawned lifetime

6D8C now runs natively with its signed countdown, five-position history, linked
owner and exact allocation/RNG ordering. 5A9A initializes typed particles;
E918 retains its state/mirror with wrapped arithmetic. Owner lookup follows
allocation and both RNG calls; capacity or late owner failure rolls back the
emitter and RNG together. Fixed particle presentation/release and return-only
handler/service execute through the measured object phase.

Three mappings add 288 bytes / 62 instructions. **209,082 original/native cases
pass per debug/release/sanitize**. One fresh ordinary movie capture plus
independent unhooked replay supplies **34 retained emitter calls, eight spawns,
sixteen RNG calls and 97 newborn particle updates**, compared in all presets.
Four lifetimes complete and four remain partial. Six earlier-slot births wait
until the next frame; two later-slot births run the same frame. These timings
are validated component invocations, not yet a native shared-pool scheduler.

**187 Python tests, zero skips; 36 CTests per preset**, nine sanitized regression
corpora and the previous 390-call P1/reversal session in all presets pass freshly.
The emitter still receives owner position and capacity per call. Initializer
6D22, alternate RNG E948 and other world clients remain open. Totals: **102
bounded mappings plus one partial / 112 indexed**. TASK-0010 remains in progress;
native playability remains none. Evidence: `re/trail_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0028-trail-allocator-client]].


## Retained mixed pool and initial live particles

The mixed session now owns P1, trail emitter/RNG, all initial and newborn trail
particles, reversals and ordered shared slots/free stack. One initial seed is
followed only by physical held masks. Emitter owner position/capacity no longer
come from per-call reference inputs. Slot-sensitive births, release/reuse,
generation guards and transactional rollback are implemented natively.

In `[1066,1100)`, every preset matches **34 P1/emitter calls, 136 trail updates,
twelve reversal updates, nine allocations/nine releases and 191 ordered pool
events**, plus full free-stack order. One final fresh ordinary capture and
independent unhooked replay support all three native comparisons. Thirteen
explicit external reservations omit their audited private state; unknown
selectors/clients/occupancy changes and collision-hit behavior reject evidence.
This is scoped allocation parity, not a complete world simulation.

190 Python tests (zero skips), 38 CTests per preset, 209,082 trail and 203,586
reversal comparisons per preset, eight additional sanitized corpora and the older
390-call P1 fixture per preset pass freshly. No new native function count is
added for composition; five static audit ranges/table add 308 classified bytes.
TASK-0010 remains in progress; native playability none. Evidence:
`re/mixed_session_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0029-mixed-object-pool]].


## Native 7808 and 7CA4 private objects

Both private handlers now execute natively with full-width shared gates,
wrapping signed countdown, equality-only stop, flag replacement and preceding
presentation. The logical control link is retained without dereferencing it.
Unknown invoked callbacks/handlers and missing shared inputs reject atomically.
Four objects move from reservations into retained native storage; nine remain.

**277,232 original/native cases per preset** execute all twenty handler
instructions. Fresh ordinary movie `[1066,1100)` and independent unhooked replay
support **136 private updates / 327 ordered pool events** per native preset,
with unchanged P1, particles, reversals, allocation/free order and RNG contracts.
All three gates stay zero with no writes; their producers are still outside
scope. Nonzero paths are covered by restricted execution, not ordinary gameplay.

192 Python tests (zero skips), 40 CTests per preset, trail/reversal corpora per
preset, eight other sanitized regressions and the old 390-call P1 fixture per
preset pass freshly. Totals: **104 bounded mappings plus one partial / 114
indexed**. The 86 promoted bytes were already classified; no added byte count.
Evidence: `re/private_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0030-private-object-updates]]. TASK-0010
remains in progress; native playability none. Next: 7A88 table motion.


## Retained 7A88 table motion

The 24-word table cycle, full-word toggle, wrapped X/Y, signed countdown reversal
and FF31BC+1 DBRA loop now execute natively. Native logical cursors replace ROM
pointers; a 4,096-iteration default budget bounds work. Presentation precedes
motion, and invoked callback79B6, invalid cursor, missing input or excess work
roll back with P1, allocation, scratch and all pool state. Slot 67 is retained;
eight external reservations remain, including two inactive occupied slots.

406,634 original/native cases per debug/release/sanitize pass; all nineteen
handler instructions execute. Two FF31BC writer fragments have 131,422 separate
restricted-original arithmetic checks per comparator run, not native parent
routine mappings. Ordinary `[1066,1100)` keeps FF31BC=0 and FF31BE=80 with no
writes; its producer prefix enters 34 times with FF31B0=0. One seed followed by
physical masks reproduces 34 table updates and 361 ordered pool events per preset,
with an independent unhooked endpoint match. Callback79B6 and collision-hit7910
remain unsupported. 194 Python tests / 42 CTests per preset and all selected
regressions pass. Totals: 105 bounded plus one partial / 115 indexed. Evidence:
`re/table_motion_validation.json` and [[03_Reverse_Engineering/findings/FIND-0031-table-motion]].
TASK-0010 remains in progress; native playability remains none.


## Retained 78EE miss service and AC5E overlap

AC5E now implements unsigned inclusive overlap, wrapped word thresholds and
X-only masking. The partial 78EE service checks P1 control tracking, then P2
only after a miss and nonzero full-word gate. Slot 63 retains native typed state;
the P1 wrapper supplies current tracking without reference reseeding. The
scheduled scope includes presentation and the fixed RTS handler. Hits, invoked
callbacks and missing consumed input reject with whole-session rollback.

478,345 original/native comparisons per preset exercise all 28 new instructions.
Fresh ordinary `[1066,1100)` and independent unhooked replay support 34 collision
updates / 395 ordered pool events per preset. The helper has 32 X misses and two
Y-only misses; the 68 P1 tracking writes are known wrapper sites. Mask, gate and
P2 tracking have no writes. P2 production remains unsupported. 196 Python tests
and 44 CTests per preset, selected regressions and older P1 fixtures pass.

Totals: 106 bounded mappings plus two partial / 117 indexed; 96 bytes promoted
from existing classification. Evidence: `re/collision_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0032-collision-miss]]. Seven external
reservations remain. Next replace their return-only presentation/occupancy state,
including inactive occupied slots, with verified typed state. Callback79B6 and
collision-hit7910 remain unsupported; TASK-0010 in progress, native playability none.


## Retained return-only and inactive occupied objects

All seven formerly reserved return-only objects now have typed retained state.
Five active objects advance presentation then invoke fixed RTS handler/service;
the two dormant occupied slots remain unavailable to allocation and emit inactive
state observations without consuming update budget. Invoked callbacks and unknown
selectors/private fields reject. No initializer, activation producer or release
is implied by the new type. Existing whole-session rollback remains intact.

286,848 original/native cases per debug/release/sanitize pass, exercising all
42 supported successful instructions in the existing dispatch/presentation/RTS
composition. 198 Python tests / 46 CTests per preset pass. Final fresh ordinary
capture and independent unhooked replay support 633 ordered records: 565
spawn/update/release events plus 68 inactive observations. Added active work is
170 return-only updates. The seven slots' 271 writes are fully audited; dormant
slots have none. All earlier input/RNG/free-order contracts remain in force.

There are zero external reservations in this interval; this does not establish
whole-world parity. Totals remain 106 bounded mappings plus two partial / 117
indexed; no new function or classified byte. See `re/return_only_validation.json`
and [[03_Reverse_Engineering/findings/FIND-0033-return-only-objects]]. Next bound
F9E2 allocation and the 7B9C return-only pair initializer. Callback79B6 and
collision-hit7910 remain unsupported. TASK-0010 in progress; native playability none.


## F9E2 allocation and the 7B9C pair initializer

7B9C now runs natively as two ordered F9E2 pops from the shared LIFO stack.
F9E2 returns its object in A6 and writes only mode/frame/flags/render/selectors;
target, countdown, link and private bytes are inherited from the slot, so the
native pool accepts only verified inherited fields. The second member is kept as
the logical FF31C0 anchor in the retained mixed session. Exhaustion, which loops
forever at FA1E in the original, rejects natively with no allocation.

8,714 restricted original/native cases per debug/release/sanitize execute all
37 successful instructions. A fresh replay of frames 0..1066 verifies 65 F9E2
and 32 F994 calls, both ordinary 7B9C runs with exact write audits, and the
frame-629 pair's 432 retained updates to the 1066 seed. The fresh 34-call mixed
capture carries the anchor; 205 Python tests / 46 CTests per preset pass.
Totals: 108 bounded mappings plus two partial / 119 indexed. Evidence:
`re/pair_initializer_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0034-pair-initializer]]. Next the 7C26
private-pair initializer. Callback79B6, 7AD6, overlap-hit FF31C0 readers and
collision-hit7910 remain unsupported. TASK-0010 in progress; native playability none.


## The 7C26 gated-visibility pair

7C26 now runs natively as two ordered F9E2 pops sharing the 7B9C transactional
template, building two 7CA4 private objects with verified inherited fields and
no flags or FF31C0 store. 8,714 restricted cases per preset pass (21 new
instructions). The same fresh frames 0..1066 replay verifies both 7C26 runs,
including a VBlank exception frame inside the frame-156 run, and follows slots
57/56 with 59/58 through 432 walks to the 1066 seed with zero observed gates.
The private seed adapter now verifies unrepresented bytes. 207 Python tests /
46 CTests per preset pass. Totals: 109 bounded mappings plus two partial / 120
indexed. Evidence: `re/visibility_pair_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0035-visibility-pair]]. Next the 7772
rising pair. Callback79B6, 7AD6, overlap-hit FF31C0 readers, gate producers and
collision-hit7910 remain unsupported. TASK-0010 in progress; native playability none.


## The 7772 rising pair

7772 now runs natively through the shared two-pop template, storing the caller's
control as an explicit logical input, clearing the countdown and deriving the
second position from the first; only the target is inherited. 8,714 restricted
cases per preset pass (27 new instructions). The fresh frames 0..1066 replay
verifies its single ordinary run (frame 629, slots 65/64) with an exact 43-write
block and follows six retained slots through 432 walks to the 1066 seed with zero
observed gates. 208 Python tests / 46 CTests per preset pass. Totals: 110
bounded mappings plus two partial / 121 indexed. Evidence:
`re/rising_pair_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0036-rising-pair]]. Next the 783A
four-object initializer. Callback79B6, 7AD6, overlap-hit FF31C0 readers, gate
producers and collision-hit7910 remain unsupported. TASK-0010 in progress;
native playability none.


## The 783A collision quad

783A now runs natively through a shared N-pop F9E2 template: a 78EE collision
probe storing the caller's control, then three return-only objects placed at +32
offsets from it. Every member inherits +08..+0D, target and countdown (the last
three also the link), so the pool now requires verified inherited presentation
for this initializer. 8,746 restricted cases per preset pass (31 new
instructions). The fresh frames 0..1066 replay verifies its single run (frame
629, slots 63..60) with an exact 65-write block; native matches 189 retained
walks, then **rejects at frame 823 where the ordinary movie reaches unsupported
hit7910** (nine hits through 831, which rewrite and deactivate slot 53). Original
continuity of all ten retained slots still reaches the 1066 seed. 209 Python
tests / 46 CTests per preset pass. Totals: 111 bounded mappings plus two partial
/ 122 indexed. Evidence: `re/collision_quad_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0037-collision-quad]]. Next the 6EC8/6EDC
dormant initializers and the native `[6886,68A4)` setup prefix. Hit7910,
callback79B6, 7AD6, overlap-hit FF31C0 readers and gate producers remain
unsupported. TASK-0010 in progress; native playability none.


## The 6EC8/6EDC dormant objects and the `[6886,68A4)` setup prefix

6EC8/6EDC now run natively as single dormant pops (position, +08..+0D, target,
countdown and link inherited) with retained FF31B4/FF31B8 identities, and the
whole `[6886,68A4)` fragment composes all six initializers as twelve ordered,
all-or-nothing pops. 8,748 restricted prefix cases per preset pass (15 new
instructions). The fresh frames 0..1066 replay verifies the ordinary prefix at
frame 629 as one exact 216-write block, and native builds it from the 6886-entry
stack. Slot 66 stays dormant to 1066; slot 67 is overwritten at frame 853 by
unsupported 7AD6 copying slot 47, so native follows it for 219 walks. 212 Python
tests / 46 CTests per preset pass. Totals: 113 bounded mappings plus two partial
/ 124 indexed, plus one mapped setup fragment. Evidence:
`re/setup_prefix_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0038-setup-prefix]]. Next extend the
prefix through 68BC (6A94, 6EB6 ×2). 7AD6/callback79B6, FB06, hit7910, overlap-hit
FF31C0 readers and gate producers remain unsupported. TASK-0010 in progress;
native playability none.


## The 6A94 pickups, 6EB6 control links and the `[68A4,68BC)` setup tail

6A94 now runs natively: record/FF31AC/rise-gate clears, then one `Pickup` per
FF312C kind other than FFFF (6AF0 with 6B44 frames and 6BB2 cadence, positions
consumed densely); 6EB6 creates the P1/P2 control-linked dormant objects. The
whole `[68A4,68BC)` tail commits all or nothing. 8,820 restricted cases per preset
pass (92 new instructions). The fresh frames 0..1066 replay verifies the ordinary
tail at frame 629 (pickups 55/54, links 53/52) as one exact 153-write block, and
native builds it from the 68A4-entry stack, then matches 146 walks before
rejecting at the first unsupported 6C00 pickup hit (frame 780, which also turns
link 53 into the trail emitter). 214 Python tests / 46 CTests per preset pass.
Totals: 118 bounded mappings plus two partial / 129 indexed, plus two mapped
setup fragments. Evidence: `re/setup_tail_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0039-setup-tail]]. Next 7DB8 and 6EF0
from 68BC. The 6C00 hit, 6D22/FB06, 7AD6/callback79B6, hit7910, overlap-hit
FF31C0 readers and gate producers remain unsupported. TASK-0010 in progress;
native playability none.


## The 7DB8 setup message, the 6EF0 gate and the 6BD6 pickup service

7DB8 and CB72 now run natively: with one player, FRUIT RETURNED (clearing FF31AA)
or, with at least two pickup kinds, MIX THOSE FRUIT goes through CB72's signed
priority gate on FF0690+53, and CB9A becomes a logical message-row clear request.
6EF0's closed gate does nothing; its open allocating path rejects. The 6BD6 pickup
miss service now has a restricted corpus. 4,717 message cases and 136,848 pickup
service cases per preset pass (82 new instructions, 32 of them research-only
rendering). The fresh frames 0..1066 replay verifies frame 629: MIX THOSE FRUIT
shown at VRAM E00E with exact RAM writes and 29 reported VDP writes, matched
natively. 215 Python tests / 46 CTests per preset pass. Totals: 120 bounded
mappings plus four partial / 133 indexed, plus three setup fragments. Evidence:
`re/setup_message_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0040-setup-message]]. Next the four gated
pair initializers 7FBE/7154/735E/7568 from 68C4. TASK-0010 in progress; native
playability none.


## The 7FBE/7154/735E/7568 gated pairs and the `[68C4,68D4)` setup step

7FBE, 7154, 735E and 7568 now run natively: each returns at once while its gate
word (FF3172..FF3178) is zero; open, it pops two objects ordered by address into
a return-only partner and a `GatedLead` naming it (7FBE from the P2 control's
+3C/+3E with the caller's A5, the others at fixed positions with FF0690). The
whole `[68C4,68D4)` step commits all or nothing; the lead handlers reject. 8,941
restricted cases per preset pass (110 new instructions). The fresh frames
0..1066 replay verifies frame 629: all four gates closed, exactly four return
pushes, no allocation, matched natively; every earlier bound reproduces. 216
Python tests / 46 CTests per preset pass. Totals: 124 bounded mappings plus four
partial / 137 indexed, plus four setup fragments. Evidence:
`re/setup_pairs_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0041-gated-pairs]]. Next the 6C00 pickup
hit for ordinary kinds. The lead handlers, 6EF0's allocating path, 6D22/FB06,
7AD6/callback79B6, hit7910, overlap-hit FF31C0 readers and gate producers remain
unsupported. TASK-0010 in progress; native playability none.


## The 6C00 pickup hit: carrying and swapping fruit

6C00 now runs natively for ordinary kinds through `MixedPool::walk_pickup` and an
explicit `PickupWorld`: a sound request, then a dormant control link becomes the
carrying 6D8C emitter (6D22/FB06) while the pickup vanishes (59BC) to its FAA4
release, or a carrying emitter exchanges with the pickup, which vanishes,
returns (6CDA/5964) and is re-dressed (6CF4) and tested in the same walk. 6,576
restricted cases per preset pass (115 new instructions). The fresh frames 0..1066
replay compares both ordinary hits (780, 980; both conversions of link 53) and
all 62 hit-pickup walks to their releases natively, chained walk to walk. The
capture shows hit7910 at 823 resetting link 53, refuting the expected 980
exchange. 217 Python tests / 46 CTests per preset pass. Totals: 131 bounded
mappings plus four partial / 144 indexed, plus four setup fragments. Evidence:
`re/pickup_hit_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0042-pickup-hit]]. Next hit7910 (the fruit
delivery). The family branches, 7AD6/callback79B6, the gated-pair leads, 6EF0's
allocating path, overlap-hit FF31C0 readers and gate producers remain
unsupported. TASK-0010 in progress; native playability none.


## The 7910 probe hit: delivering the carried fruit

7910 now runs natively through `MixedPool::walk_probe` (and `step` with a
`PickupWorld` and FF31B0): it returns while FF31B0 is set or the touching
control's link is dormant; with a carrying emitter it requests sound 008C, pops
the 59AE sparkle (a `TrailParticle`) and the F994 copy (a new `DeliveredPickup`,
mode 87 at (00A4,00F6), callback 79B6) and leaves the link dormant. 8,557
restricted cases per preset pass (40 new instructions). The fresh frames 0..1066
replay compares all nine ordinary hits (823 delivers into slots 54 and 47;
824..831 return) and all 60 later walks of the sparkle and the copy natively,
chained; the copy's 79B6 callback at 853 rejects natively. 218 Python tests / 46
CTests per preset pass. Totals: 133 bounded mappings plus four partial / 146
indexed, plus four setup fragments. Evidence: `re/delivery_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0043-fruit-delivery]]. Next callback79B6
and 7AD6's first-ingredient path (frame 853). 7AD6's 7B42 anchor handler, the
6C00 family branches, the gated-pair leads, 6EF0's allocating path, overlap-hit
FF31C0 readers and gate producers remain unsupported. TASK-0010 in progress;
native playability none.


## callback79B6 and 7AD6: the first ingredient

A delivered copy's walk now runs natively through callback79B6 and 7AD6 when no
ingredient is collected yet (FF31AC zero): the copy becomes the table-motion
sprite, FIRST INGREDIENT COLLECTED! is posted through CB72 (`post_message`,
shared with 7DB8; CB9A as a row-clear request), the dormant FF31B4 object takes
it and FF31AC and its record name it, the copy is released, and FF31BE/FF31BC
are stored (the pool step's private globals are now mutable shared state).
4,172 restricted cases per preset pass (29 new instructions). The fresh frames
0..1066 replay compares the 853 walk and all 213 later walks of slot 67
natively. 218 Python tests / 46 CTests per preset pass. Totals: 133 bounded
mappings plus six partial / 148 indexed, plus four setup fragments. Evidence:
`re/ingredient_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0044-first-ingredient]]. Next: run the
retained setup pool natively past its hits (a `PickupWorld` and the emitter's
inputs in the continuity). The second-ingredient paths and 7B42, the 6C00 family
branches, the gated-pair leads, 6EF0's allocating path, overlap-hit FF31C0
readers and gate producers remain unsupported. TASK-0010 in progress; native
playability none.


## The retained level world: every object loop from the setup to 1066

The whole retained world now runs natively: `wiznliz-collision --world-pool`
builds the `[6886,68D4)` setup from its entry stack (all 68 slots free) and
steps every object loop of frames 634..1065 in that one pool with one carried
`PickupWorld`, private globals and E918 state. Its only per-loop inputs are 78EE
tracking, the emitter owner's position, a count of E918 calls by non-pool code
(the object at FFFF32C2, five calls) and the message producer's field updates
(four). The fresh frames 0..1066 replay matches the setup and all 432 loops:
5,732 walk updates, 33 births, both 6C00 hits, the 823 delivery and the 853
first ingredient, with the free stack, generations and world state after every
loop; pool bytes change only inside walks; sabotaging any input fails. No `src/`
change and no new ROM routine (totals unchanged). 224 Python tests / 46 CTests
per preset pass. Evidence: `re/world_pool_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0045-retained-world]]. This met the pool
part of the [[06_Decisions/ADR-0001-presentation-shell]] trigger; the ADR was
then rejected (2026-10-23) and SDL3 stays. Next: join the native P1 session to the world. The second-ingredient
paths and 7B42, the 6C00 family branches, the gated-pair leads, 6EF0's
allocating path, overlap-hit FF31C0 readers and gate producers remain
unsupported. TASK-0010 in progress; native playability none.


## The native player joined to the retained world

`MixedSessionState` now carries the world (`establish_world`), one object loop
runs through `step_world_phase` with explicit `WorldUpdates`, and
`step_mixed_session` feeds it P1's own tracking and position. `wiznliz-session
--world-session` builds the setup, runs loops 634..668 with supplied tracking
(the level-start fade timer FF0B90 is active there and the session does not
schedule it), then from 669 runs P1 from one seed and physical held sets. A fresh
P1 capture joined with the world capture matches all 397 P1 calls and all 397
joined loops, cross-checked against the world capture's tracking and 128 owner
positions; `--world-pool` output is unchanged. 225 Python tests / 46 CTests per
preset pass. Evidence: `re/world_session_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0046-world-session]]. Next: schedule the
level-start fade so P1 joins from 634. The second-ingredient paths and 7B42, the
6C00 family branches, the gated-pair leads, 6EF0's allocating path, overlap-hit
FF31C0 readers and gate producers remain unsupported. TASK-0010 in progress;
native playability none.


## The level-start fade: the world native from its first loop

The session now carries the shared 1345A timer (`P1SessionState::transition`)
and runs it before the banner each call. With it, the joined world session runs
from the first object loop with no supplied loops: a fresh P1 capture of
634..1066 matches all 432 fade-timer states, all 432 P1 calls and all 432
object loops consuming P1's own tracking and position; the fade's eight palette
requests match its level steps. The session validator gained `active_timer`, so
the mixed, early/late P1 and effect sessions were recaptured fresh and pass.
226 Python tests / 46 CTests per preset pass. Evidence:
`re/fade_session_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0047-level-start-fade]]. Next: extend the
joined run past 1066. TASK-0010 in progress; native playability none.


## The second ingredient and the spell mix: native to 1433

callback79B6 and 7AD6 now take their second-ingredient paths natively (D22F, the
negated drift, the FF31B8 object named in FF31B0, the FF31C0 anchor's 7B42
countdown), and 7CC8 runs once per frame before the loop (`mix_spell`: the
FF31BE/FF31BC countdown and the exchange of the two ingredients). 10,420
restricted cases per preset match. P1's reversal effect joins the world pool.
A fresh joined capture of 634..1433 matches all 799 timer states, P1 calls and
object loops with no supplied loops, through the second delivery, the second
ingredient and 46 exchanges. 79B6/7AD6 promoted, 7CC8 bounded, 7B42 partial:
136 bounded plus five partial / 150 indexed. 228 Python tests / 46 CTests per
preset pass. Evidence: `re/spell_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0048-spell-mixing]]. Next: reconstruct
the spell's completion at 1433 (13294, 7B58, D269, 7E18, 1324E, 7B8A).
TASK-0010 in progress; native playability none.


## The spell's completion: native to the exit door

The FF31C0 anchor now continues through 13294 (the fade-out, from the session's
timer), 7B58 and 7B8A; 7B58's completion posts D269, consumes both ingredients
(7E18/7ED6), looks up their fruits in the 83DA recipe table and casts recipe
8652 (fruits 6 and 5): 7F08's sparkle with its particles and 6F02's door
(6FB6's countdown, 5964's puff, 6FCA's dressing, 705C's AC5E) and sign (4C08,
4C34). 14,720 restricted cases per preset match. A fresh joined capture of
634..1515 matches all 881 timer states, P1 calls and object loops with no
supplied loops, P1's evidence split after the world's two timer writes. 7B42
promoted, nine bounded and five partial mappings added: 146 bounded plus nine
partial / 164 indexed. 229 Python tests / 46 CTests per preset pass. Evidence:
`re/completion_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0049-spell-completion]]. Next: P1 enters
the door at 1515. TASK-0010 in progress; native playability none.


## Entering the door: native to the level's end

705C's contact path (7082 with 4CA2) is native: the sign released, the door
vanishing, FF0F00, the camera words and P1 handed to its exit handler; the
session then runs P1's already native 710E/7126 with its timer and action
globals. The session validator accepts P1's exit handlers. A fresh joined
capture of 634..1533 matches all 899 timer states, P1 calls and object loops
through the level's end (FF33E0 = 7 at 1532). 4CA2 bounded, 705C's partial
extended: 147 bounded plus nine partial / 165 indexed. 230 Python tests / 46
CTests per preset pass. Evidence: `re/door_entry_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0050-door-entry]]. Next: the scene after
the level. TASK-0010 in progress; native playability none.


## The scene after the level: its doors, native from setup to exit

The scene between levels (5D30) was surveyed from the level's end to its exit.
Its door setup (63A4, 60E6 with 611E and 6334), the doors' walks (61F6, 621A,
623C with 17298, FA8C, 630A and 13208, FAC4/FAE2) and its loop's exit test
(6024) are native; the hub loop lets P1's Up/Down reach its actor. 7,571
restricted cases per preset match. A fresh capture of 1562..1759 matches the
setup's 24 objects, all 196 P1 calls, timer states and pool images with one
P1 seed, P1 entering door 0 at 1742 and the scene's end at 1758. Nine bounded
and one partial mapping added: 156 bounded plus ten partial / 175 indexed. 236
Python tests / 46 CTests per preset pass. Evidence: `re/hub_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0051-hub-doors]]. Next: join the level's
run to the hub through the scene change. TASK-0010 in progress; native
playability none.


## The scene change: the level and the hub as one native run

The scene change (0x488, 16EA4's 17024/F850/FF0F16/131C2, 9880 with 9952 and
5964, 63A4/60E6, 63E2, 5ED4) is native as `enter_hub_scene`; 8,583 restricted
cases per preset match (1,012 of them the scene change). An offline joined
comparison (a fresh scene-change capture with session 054's level and hub
captures) runs the level from its setup, the scene change and the hub in one
native run from one P1 seed: 1,095 P1 calls and loops, P1 never reseeded at the
hub; across the scene change the carried state changes only inside the
reconstructed routines. The tool's fresh all-in-one capture, interrupted by a
restart, was completed by session 056 with its fixtures on every preset. Five
bounded and three partial mappings added: 161 bounded plus 13 partial / 183
indexed. 239 Python tests / 46 CTests per preset pass. Evidence:
`re/scene_change_validation.json` and
[[03_Reverse_Engineering/findings/FIND-0052-scene-change]].

## After the hub: the hint screen and the second level (in progress)

Session 056's survey ([[03_Reverse_Engineering/findings/FIND-0053-second-level-entry]])
finds the hint screen (1959E, 1758..2067), E2A (2067..2106) and 754's head
(2106) between the hub and the second level, whose loop (0x792, FF33E0 = 0013)
runs from 2107; 6664 is not reached. Native work is in progress. TASK-0010 in
progress; native playability none.
