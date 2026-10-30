---
id: FIND-0016
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Up/down actions, contextual callbacks and a deferred sample request

The bounded up/down action paths now execute natively, including hold/release,
deferred jump selection, both callbacks and the up action's shared-global and
mailbox effect. The release callback executes idle immediately with its own
return pending; the actor wrapper then invokes the newly selected handler again.
This is neither an extra frame nor a callback that merely assigns idle.
[[07_Tasks/TASK-0010-grounded-controller]] remains in progress. Native playability
is none; later world services and native audio playback remain unimplemented.

## Identity and exact scope

Immutable USA ROM: 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
`re/actions_step.json` pins **13 disjoint ranges, 412 bytes, 81 instructions and
12 direct transfers**. FUNC-0068 through FUNC-0079 add twelve bounded mappings;
ED6E6 has a discontiguous shared tail. There are 79 indexed functions / 70 bounded
simulation mappings, plus the previously named initializer/dispatch fragments.
These are scoped mappings, not twelve complete independent game systems.

| Half-open ROM range | Verified contract |
| --- | --- |
| `[9C56,9C90)` / `[9D4E,9D88)` | Up/down initialization, immediate fallthrough to hold handler |
| `[9C90,9CFA)` | Up hold, jump priority, shared gates, sample request, release decision |
| `[9CFA,9D28)` | Up release animation and RTS-only wait at 9D26 |
| `[9D44,9D4E)` | Assign A27E and return; no immediate jump |
| `[9D88,9D96)` | Down hold, jump before release test |
| `[9D96,9DC4)` | Down release animation and return |
| `[9DC4,9DCC)` / `[9DCC,9DCE)` | Assign A27E / shared RTS-only down wait |
| `[A196,A1A4)` | Facing-selected idle initializer, fallthrough into idle now |
| `[F938,F940)` | Freeze animation by setting mode 80; retain selected handler |
| `[ED6E6,ED6F6)` / `[ED6FC,ED716)` | Encode the called sample resource and write four-word mailbox through RTS |

The alternate ED6F6 entry and unused 9D28 initializer are excluded. Primary
original-68000 decoding closes the graph through prior verified ranges and
explicit stop/rejection boundaries. CPU sentinels pass; five new short GNU
corroborations cover BPL, target increment, deferred RTS, facing branch and bank
shift. Prior GNU BCHG/absolute MOVE.L limitations are not promoted into independent
corroboration. Restricted Musashi visits all 81 instructions without patching or
stubbing them. Full-machine evidence uses the unchanged GPGX worker build
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`.

## Action state and ordering

Idle retains its existing drop/direction/jump priorities. Only after damping to
zero does it check Up, then Down; Up wins if both logical fields are nonzero.
Action entry preserves facing, position, speed, vertical/delay and cycle fields.
It does not perform a terrain-settle call. Initial presentation values are:

| Action | mode | current / begin / end | target | countdown / reload | handler / callback |
| --- | --- | --- | --- | --- | --- |
| Up | 85 | 30 / 30 / 35 | 34 | 3 / 3 | 9C90 / F938 |
| Down | 85 | 36 / 36 / 41 | 40 | 3 / 3 | 9D88 / F938 |

Mode values in this note are hexadecimal; animation numbers are decimal.
F76C compares the old frame to target, advances first, then invokes F938, which
changes only mode to 80. The actor stays active and its hold handler continues.
With the default fields it freezes on frame 35 or 41 after fifteen presentation
invocations. Holding either action does not damp, move, settle or process ordinary
direction/drop input. The selected hold handler checks +16 jump first, ungated:
9D44/9DC4 assign A27E and RTS. That jump normally executes in the next actor
invocation; releasing the physical button before then does not cancel selection.

Once its own +1A/+1B field is released, the handler sets mode 87, target to
`begin + 1` with word wrap, counters 2/2, wait handler 9D26/9DCC and callback
A196. It retains current/begin/end, facing and cycles. The wait handler is an
actual original RTS and ignores input until presentation completes. Early release
can wrap from begin back to end before reaching its target; there is no authored
shortcut to idle. The up shared effect is evaluated before its release test.

A196 tests the facing bit, tails to A1A4/A22C, initializes idle, then falls
through into A1BE/A246 with the **F900 return still pending**. Idle can execute
movement, another action, drop or jump inside presentation. After return, F900
selects +16 and F904 invokes it with **F906** pending. For example ordinary frame
1629 calls down-release callback -> idle -> up entry -> up hold -> F900 -> up hold
again. Frame 3282 similarly enters down from an up-release callback. Authored
jump-completion cases integrate airborne twice in this single scheduled call.

## Shared gates and sample mailbox

Up, after its jump test, reads mode FF33E0, cooldown FF33D8 and control raw byte
+14. Only mode 19 decimal, negative signed cooldown and **clear raw bit 6** enter
the effect. It copies FF33DA to cooldown, subtracts 10 as a word, and clamps to
zero when the wrapped result has N set. This is BPL semantics, not signed BLT:
interval 8000 hex produces cooldown 7FF6, while interval FFFF produces zero.
It saves D0–D3, calls ED6E6 with D0=F0000, D1=200, D2=0F14, restores those
registers, then adds 3 to FF33DA with word wrap.

ED6E6 forms bank `D0 >> 15` and the low-word location `(D0 & 7FFF) | 8000`, then
writes D1 / D0 / D2 / D3 to FF0AD6 / FF0ADA / FF0AD8 / FF0ADC. The observed call
therefore overwrites mailbox words in ascending address order with
**200, 0F14, 8000, 001E**. The original service is executed through its RTS in the
reference; only its deferred consumption and playback are excluded. Adjacent code
at ED716 reads/clears the request before a later audio-driver path;
that consumer is a static discovery lead, not a newly native audio mapping.
Neither sample waveform, count units, audible meaning nor general sound timing
is asserted by this contract.

`ActionGlobals` gives these shared words an explicit native context. No countdown
or inter-call mode change is invented. `SampleRequest` carries logical
`ActionSample::up_action`, count and parameter. Only the research transport maps
that logical resource to the original bank/location and applies mailbox overwrite;
no original resource pointer enters the simulation. Missing required globals
reject, while a hold's higher-priority jump can run without them. Action/global/
terrain/effect changes and returned requests commit together, including failures
after callback work but before the wrapper's next handler finishes.

## Native API and comparison contracts

`step_actor` consumes action entry immediately but retains deferred jump semantics.
`step_actor_presentation` is the contextual F76C boundary. `step_scheduled_actor`
includes both the callback continuation and later selected handler, sharing the
continuation/horizontal budget. The context-free `step_presentation` can freeze
F938 but rejects an invoked A196 because it lacks movement/global context.
Unknown invoked selectors still reject transactionally.

The actor transport's old modes keep their 35-field input/output contract. New
`--actions`, `--actions-presentation`, `--actions-scheduled`, `--actions-sequence`
modes append eight inputs: mode, cooldown, interval, raw byte and four mailbox
words. Output appends three globals, four resulting mailbox words, request count
and `(logical sample, count, parameter)` triples after the old sound output.
Sequence mode retains actor state and asserts subsequent state columns; shared
world globals/mailbox/scratch and controls remain explicit environment feeds.
The action transport excludes reversal allocations; those have a separate
comparison contract. The C++ API supports both explicit contexts together.

**146,638/146,638 cases pass per debug/release/sanitize preset**, with identical
output hashes: 139,936 handler, 2,072 contextual presentation, 2,070 scheduled,
768 authored terrain and 1,792 cataloged terrain cases. Eighteen authored goldens,
all interval/cooldown words, all raw bytes, both facings, release/hold/jump,
callback-to-action/jump, word/byte wrapping and unsupported/rollback checks pass.

The unchanged movie supplies **184 continuous actor calls and 184 intermediate
presentation checks** in [1615,1690) and [3230,3339). Two explicit input branches
from completed frame 3258 supply **72 additional actor and 72 presentation checks**:
Up+A emits one sample request at 3258; Down+B defers jump at 3306. A separate
Up+B branch defers jump at 3258. These branches replace input rows, with complete
parent/edited-row provenance, and perform **zero RAM/register/ROM edits**. Their
frames overlap the original route; do not count them as unique source frames.
The raw bit-6 observation is scoped to this three-button producer/configuration.

Each of the four endpoints matches a fresh independent unhooked worker. Trace
schema/order/overflow, selected handler, explicit SP/return words, mailbox writes,
ABI arguments, control preservation and actor continuity are checked. No inferred
general call stack or partial-frame save is used. State hashes describe declared
exposed state, not every hidden device bit. Environment-fed actor parity is not
whole-frame native replay. Final capture:
`local/generated/actions-movie/run-ee3uhda0/report.json`.

The broader research [1608,1690)/[3230,3350) captures are retained under ignored
`local/generated/actions-research/`. The comparison begins after unreconstructed
12646/AA50 presentation behavior at 1608–1614 and ends before frame 3339's
allocating reversal. Those intervals are not silently skipped within a claimed
continuous native window. Fresh regressions and hashes:
`re/actions_validation.json`, [[05_Validation/RESULTS]],
[[08_Sessions/2026-10-02-016-up-down-actions]].

Next bounded task: close the measured 12646 handler / AA50 callback gap at movie
frames 1608–1614, then measure the later F906/F90A +46 service. General world
allocation, owner destruction, input scheduling and audio consumption remain
separate work. No further user recording is required for that start.
