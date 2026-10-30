---
id: NATIVE-PORTING-MAP
type: porting_map
status: partial
---
# Porting map

The RNC2/assets, 106 bounded simulation mappings, two partial mappings, two idle
initializer fragments, one actor-dispatch phase and two effect-dispatch phases have native mappings.
The simulation routines have isolated original-execution comparisons and scoped
real-game actor comparisons; a complete controller or playable game does not yet exist. `re/functions.csv` and `re/symbols.csv` are the address/name
metadata authorities; uncertain reset boundaries stay empty.

| Original evidence | Understood behavior | Native implementation | Validation |
| --- | --- | --- | --- |
| FUNC-0001, entry `0x200`; fragment ends `0x28E`, full end unknown | Partial reset initialization/table/clear behavior | None; `tools/reset_probe.py` is static research | Synthetic field checks and decoder corroboration; no execution |
| FUNC-0002, `[0x19462,0x1959E)` | RNC2 valid-stream token logic, source A0/header skip, output A1, restored saved registers | `wiz::rnc2::decode`, `src/core/rnc2.cpp`; checked host API, not original ABI/malformed-input behavior | 49 authored + first ROM block match independent codec; original CPU routine has not been executed |
| FUNC-0003/0004/0005, `0x10D8`, `0x1896`, `0x3CB6` | Conditional descriptor-zero PACK/caller chain to first RNC block | No native scene selection or pair-loader yet | Static operand/pointer/branch checks |
| FUNC-0006, `0x3D46` (partial semantic replacement) | Palette/count/pattern/opaque-record resource layout | `wiz::assets::parse_pattern_bank`, `src/assets/pattern_bank.cpp`; checked host resource instead of hardware transfers | Authored extent/count/record tests; exact 17,714-byte local load; original transfer timing not reproduced |
| FUNC-0007, `0x13754` (partial semantic replacement) | Palette byte permutation | `wiz::assets::palette_cram_word`; raw pairs and words retained | Authored distinct-channel/unused-bit checks; original nested callee `0x137CE`, ABI and palette timing excluded |
| VDP normal pattern representation, corroborated by pinned source | 8x8 indexed pattern pixels and RGB3 channel positions | `make_atlas` and explicit diagnostic color conversion | 256 single-bit patterns and 28,288 local pattern pixels agree with independent specification model; no original-screen comparison |

Evidence: [[03_Reverse_Engineering/findings/FIND-0001-reset-path]],
[[03_Reverse_Engineering/findings/FIND-0006-native-rnc2]],
[[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]]. The original RNC routine
skips all header fields and has no stream bounds/CRC checks. Native validation
is intentional host safety behavior, not an accidental gameplay divergence.
Register/CCR ABI and malformed streams are outside the codec equivalence claim.

`rnc.unclassified.0001` remains the stable logical ID for the first bank despite
its newly understood container role. ROM `[0x348B2,0x372F7)` is decoded under the
PACK wrapper at `0x348AE`. There are 442 patterns and equally many opaque records;
this is not a maximum capacity claim. Native resource loading uses stable IDs and host vectors, preserving opaque
records without imposing this bank's count as a fixed pool.

New evidence: [[03_Reverse_Engineering/findings/FIND-0008-native-pattern-bank]].
Next: [[07_Tasks/TASK-0010-grounded-controller]]. Architecture:
[[04_Native_Implementation/ARCHITECTURE]]. Coverage:
[[03_Reverse_Engineering/COVERAGE]]. No movement, objectives, audio sequencing,
scene replay or gameplay-equivalence test is implied by the codec mapping.


## Companion scene mappings

| Original evidence | Behavior | Native mapping / scope | Verification |
| --- | --- | --- | --- |
| FUNC-0004/0005 A1 path | Conditional descriptor 0/slot 0 resource pairing and decompression | Catalog links `scene.companion.0001` to base bank; no native runtime mode selection yet | Static fields/calls + second independent RNC2 comparison |
| FUNC-0008 `[0x3E14,0x3F34)` | Coordinate additions, two starts, appended patterns/records and map header | `wiz::assets::parse_scene`, `src/assets/scene.cpp`; no original ABI/device writes | Authored wrapping, extents, record and unsupported-shape tests; actual resource checks |
| FUNC-0009 `[0x3F34,0x3F60)` | 4096 word ADD/OR operations | `relocate_map_word`; logical map cells retain source words and fields | Fixed independent arithmetic cases including carry into flags; no original CPU execution |
| Column reader fragment `0x406C`, pinned VDP attribute source | Map row stride and tile attributes | `make_scene_image` diagnostic plane composition | Authored flips/base-boundary cases and all 262,144 local pixels vs independent model |

The fixed 128x32 importer is a scoped legacy format decoder. SceneResource uses
host-sized containers and stable resource links; no generic CPU or VRAM simulator
is introduced. Record contact use is now verified; other consumers remain open.
Next gameplay dependency: [[07_Tasks/TASK-0010-grounded-controller]]. Evidence:
[[03_Reverse_Engineering/findings/FIND-0009-companion-scene]].


## Terrain simulation mappings

| Original evidence | Native mapping | Compared contract |
| --- | --- | --- |
| FUNC-0010 `[0x99D4,0x9A18)` | `query_terrain` map selection | Word subtraction, x mask, signed low-word row addressing, logical map word, negative-y sentinel and scratch preservation |
| FUNC-0011 `[0x9A18,0x9A5E)` | `query_terrain` record selection | Relative record/column, H reversal, V ignored, unsigned byte and final NZVC in transport |
| FUNC-0012 `[0x9A80,0x9AAE)` | `settle_down` | Equality leaves position; mismatch increments y with word wrap, observed final comparison/MOVEQ result |
| FUNC-0013/14/15 `0x9B34/0x9B5C/0x9B84` | `probe_contact` upper/foot/lower | Position+(12,22/23/24), scratch, contact byte, one-based y comparison and NZVC |

`src/sim/terrain.hpp/.cpp` is native C++20 in `wiz_sim`, using extracted
`SceneResource`/`PatternBank` and explicit position/scratch state. No CPU library,
RAM interpreter or raw ROM dependency. Six semantic mappings are independently
compared against original execution: 614,436 cases per preset, 86/86 instruction
addresses visited. Full register ABI, device/cycle effects, out-of-resource RAM
and overflowing original pattern relocation are excluded. See
[[03_Reverse_Engineering/findings/FIND-0010-terrain-query]].

## Movement mappings

| Original evidence | Native mapping in `src/sim/movement.*` | Compared contract |
| --- | --- | --- |
| FUNC-0016/0017 `0x9A5E/0x9A6C` | `damp_horizontal`, `damp_once` | Signed speed approaches zero; DBF count+1 including 65,536 |
| FUNC-0018 `0x9AAE` with fragment `0x9AF8` | `step_horizontal` | Initial direction/count, zero settling, word overflow, continuation after transition |
| FUNC-0019/0020 `0x9AC8/0x9B04` | `step_left`, `step_right` | Position wrap, ordered foot/upper/foot probes, y adjustment and loss of contact |
| FUNC-0021 `0xAA50` | `enter_airborne` | All mode/presentation/motion/delay assignments and explicit next-handler identity |
| FUNC-0022/0023 `0xACD6/0xACE8` | `clamp_positive`, `clamp_negative` | Signed word comparisons after wrapping speed arithmetic |

282,233 comparisons per preset agree in all sixteen semantic output fields;
all 74 new instructions are visited. No full register/CCR ABI or frame timing
contract is asserted. Transactional failure and a default 1024-step budget are
explicit host policies; callers can allow the verified 64,513-step 8000 edge.
The airborne event identifies original handler `0xAAEA`, now implemented to
explicit return/continuation boundaries in the airborne section below. Paired control/actor records are established statically and are now verified for
the observed three-button producer; broader input paths remain open. Evidence: [[03_Reverse_Engineering/findings/FIND-0011-movement-step]].

## Airborne and landing mappings

| Original evidence | Native mapping in `src/sim/airborne.*` | Compared contract |
| --- | --- | --- |
| FUNC-0024 `0x9BAC`, split positive fragment `0x9C08` | `step_airborne_horizontal` | Initial count/direction, zero-speed settling and forced non-contact return for nonzero speed |
| FUNC-0025/0026 `0x9BCA/0x9C18` | `step_airborne_left/right` | Upper contact, one y decrement and counted damping; shared RTS preserved semantically |
| FUNC-0027/0028 `0xAAEA/0xAB04` | `step_airborne` | Delay/boost, damping, gated left-priority acceleration, gravity, vertical motion and landing order |
| FUNC-0029 `0xAB8A` | `resolve_landing` | Signed speed/facing, presentation assignments and all selected logical handlers |
| FUNC-0030/0031 `0xA658/0xA690` | `set_right_motion_reload`, `set_left_motion_reload` | Signed threshold counters |
| Idle entry fragments `0xA1A4/0xA22C` | Landing's explicit immediate continuation | Initializer assignments only; stop before `0xA1BE/0xA246` idle handler instructions |

415,940 original comparisons pass per preset, with all 172 new instruction
addresses visited. Ordinary returns and immediate pending continuations are
distinct outputs; the airborne API rejects grounded/idle handler execution.
Full controller/input/frame scheduling remains open. Original execution is
limited to declared code/memory, return or continuation boundaries; native code
has transactional resource/budget failures and no CPU dependency. Evidence:
[[03_Reverse_Engineering/findings/FIND-0012-airborne-update]].


## Actor dispatcher mappings

| Original evidence | Native mapping in `src/sim/actor.*` | Compared contract |
| --- | --- | --- |
| FUNC-0032/0033 `A1BE/A246` | Idle branches in `step_actor` | Drop/direction/jump priority, damping, immediate continuation and deferred directional assignment; up/down immediate entries now mapped below |
| FUNC-0034 `A1FA` | Drop helper branch | Map bit 15, scratch, +2 y, caller-return removal expressed as same-call airborne continuation |
| FUNC-0035/0048 `A27E/AA88` and presentation branches | Jump helper and dispatcher | Ordered sound requests, all presentation assignments, delay/impulse and immediate airborne execution; no audio-driver parity |
| FUNC-0036/0038 `A2A6/A33E` | Idle turn initialization | Logical handler/callback, facing and presentation; RTS defers motion |
| FUNC-0037/0039 `A2EC/A384` | Turn updates | Asymmetric damping/jump gates, acceleration and horizontal motion |
| FUNC-0040/0043 `A3D4/A512` | Ground entry | Facing, words/counters and normal handler assignment followed by RTS |
| FUNC-0041/0044 `A408/A546` | Normal grounded updates | Asymmetric reversal priority, signed thresholds, reload, same-call idle and jump |
| FUNC-0042/0045 `A4EC/A634` | Normal reversal updates | Immediate execution after reversal initialization; distinct gate behavior and deferred presentation callbacks |
| FUNC-0046/0047 `A6C8/A88E` | Fast grounded updates | Motion, slowdown assignment and fast jump; allocating reversal now mapped below through explicit owned storage |

This adds seventeen bounded mappings, not seventeen complete independent game
systems. Exact noncontiguous tails and rejected boundaries are in
`re/actor_update.json` and [[03_Reverse_Engineering/findings/FIND-0013-actor-dispatch]].
The `FCB32` mismatch path is original research execution only, not a native audio
mapping. Presentation callbacks are logical identities; their separate scheduler
and invocation boundary are implemented below.

152,093 original/native actor cases pass in each preset, with 17 independent
goldens and all 315 new scoped instructions visited (309 actor, six reference
sound-gate instructions). The independent GPGX captures compare 283 actual
invocations at F904/F906: eighteen actor/scratch fields and ordered sound
arguments. No whole-frame, complete ABI, timing or audio waveform parity follows.

## Presentation and scheduled actor mappings

| Original evidence | Native mapping in `src/sim/presentation.*` | Compared contract |
| --- | --- | --- |
| FUNC-0049 `[F76C,F850)` | `step_presentation` | Byte countdown/reload, word frame advance, old-frame target/endpoint tests, loop/bounce before callback |
| FUNC-0050/0051 `A2E8/A380` | Turn completion callbacks | Ground initializer tails; target/cycle/callback retention |
| FUNC-0052/0053 `A50E/A654` | Normal reversal completion callbacks | Facing and normal-handler change before this invocation's handler selection |
| FUNC-0054/0055 `[A774,A7A8)`, `[A93A,A96E)` | Fast-jump completion callbacks | Wrapped cycle decrement, repeat-to-begin or words 24/24/29 and counters 2/2 |
| Dispatch **fragment** `[F8F6,F906)`; inactive exit F90C | `step_scheduled_actor` | Active bit gates both phases; presentation precedes selected handler; transaction spans both |

Seven new routine mappings plus one bounded caller phase, 364 new disjoint bytes
and 90 instructions. The +46 post-handler service and whole-frame scheduler are
not mapped. 347,320 cases per preset and 507 continuous user-movie actor calls
pass; 507 additional presentation boundary checks verify the intermediate phase.
Unknown invoked callbacks reject. The native sequence transport retains actor
state and asserts continuity; shared terrain scratch and controls are external
inputs. See [[03_Reverse_Engineering/findings/FIND-0014-presentation-scheduler]].


## Fast reversal and dependent object mappings

| Original evidence | Native mapping | Compared contract |
| --- | --- | --- |
| FUNC-0056/0061 `A7A8/A96E` | Fast reversal entry in `step_actor` | Presentation/facing, allocate at pre-motion position, immediate fallthrough |
| FUNC-0057/0062 `A7EC/A9B2` | Fast reversal motion | Restore control owner, ungated jump, damping/acceleration, horizontal movement |
| FUNC-0058/0063 `A814/A9DA` | `step_presentation` callbacks | Opposite ground initializer before handler selection |
| FUNC-0059/0064 `A818/A9DE` | `make_reversal_effect` and explicit store | Asymmetric spawn offsets, fields, owner backlink |
| FUNC-0060/0065 `A87C/AA40` | `step_reversal_effect` | Owner X follow with word wrap; retain Y |
| FUNC-0066 `[F994,F9D0)` | `ReversalEffects::spawn` | Selective initialization / successful LIFO allocation; bounded exhaustion replaces hardware loop |
| FUNC-0067 `[FAA4,FABC)` | Release branch / `ReversalEffects::step` | Clear mode and return slot; preserve other modeled fields |
| **Fragments** `[080A,081C)` / `[69AA,69BC)` | `step_reversal_effect` phase ordering | Active gate, presentation, handler even after release; stop before +46 or inactive tail |

Twelve bounded mappings plus two phases add 576 disjoint bytes / 119 instructions.
203,586 original/native cases pass per debug/release/sanitize preset; all 119 new
instructions are visited. Ninety-two continuous movie actor calls and 24 effect
updates pass, with two allocations/releases and independent unhooked endpoint
agreement. The native store contains only these effects: full-world allocation,
owner destruction, +46, rendering/audio and complete scheduling remain open.
Native playability is none. See
[[03_Reverse_Engineering/findings/FIND-0015-fast-reversal]].


## Up/down action mappings

| Original evidence | Native mapping | Compared contract |
| --- | --- | --- |
| FUNC-0068/0072 `9C56/9D4E` | `action_entry` / `step_actor` | Presentation setup and immediate hold execution, retaining facing/motion/cycles |
| FUNC-0069/0073 `9C90/9D88` | Up/down hold branches | Jump before release; up shared-global/raw-byte gates and request |
| FUNC-0070/0074 `9CFA/9D96` | Release setup | Reverse mode, wrapped begin+1 target, counters, callback and wait |
| FUNC-0071/0075 `9D44/9DC4` | Deferred jump branches | Replace handler with A27E and return |
| FUNC-0076 `9DCC` (also 9D26 in FUNC-0070) | Explicit release wait handlers | Original RTS-only behavior; input ignored |
| FUNC-0077 `A196` | Contextual `step_actor_presentation` | Facing-selected idle initializer and immediate handler execution before F900 |
| FUNC-0078 `F938` | Hold callback | Mode 80 only, after old-frame target and frame advance |
| FUNC-0079 `ED6E6`, shared tail `ED6FC` | Logical `SampleRequest` plus research resource adapter | Called ABI and four overwritten mailbox words; driver consumption/playback excluded |

Thirteen disjoint ranges add 412 bytes / 81 instructions and twelve bounded
mappings. All 146,638 cases pass per preset; eighteen goldens and all new
instructions pass. Ordinary movie evidence covers 184 actor / 184 presentation
checks, with 72 more of each in labeled input branches. Native actor state stays
continuous; shared globals/mailbox/scratch are environment feeds. See
[[03_Reverse_Engineering/findings/FIND-0016-up-down-actions]].


## Bounded actor wrapper through actual return

[[03_Reverse_Engineering/findings/FIND-0017-actor-wrapper]], `re/dispatch_step.json`
and `re/dispatch_validation.json` extend the earlier actor phase. Totals at that checkpoint: 71
bounded simulation mappings / 80 indexed functions, plus the named fragments.

| Original scope | Native destination | Verified boundary |
| --- | --- | --- |
| FUNC-0080 `[12646,12648)` | `MotionUpdate::return_only`, `ActorService::return_only` | Actual RTS, explicitly mapped; unknown selectors reject |
| Existing FUNC-0021 `[AA50,AA88)` as callback | `PresentationCallback::enter_airborne` | Initialize only, return to F900; wrapper runs airborne afterward in same call |
| Actor phase `[F8F6,F938)`; new tail `[F906,F938)` | `step_actor_dispatch`, `ActorTracking` | One active gate, presentation, selected handler, selected return-only service, control +42/+44, actual RTS |

The original F8F2 control-to-actor pointer lookup remains an ownership adapter
boundary. The tail updates control coordinates on inactive calls too, compares
selector +1A6 to exact FFFF, and wraps additions as words. Unknown invoked service
rolls back earlier actor/global/scratch/effect work. Context-free presentation
accepts AA50 but continues rejecting contextual A196.

138,149 cases pass per preset, with thirteen independent goldens and all fifteen
new instructions. The recording supplies 191 ordinary / 72 input-branch calls,
with presentation and selected-handler checks and four unhooked endpoint matches.
The full-wrapper transport excludes reversal allocation; C++ supports explicit
reversal storage and tests late rollback. World scheduling, other recorded
handlers, audio consumption and native playability remain open.

## Transition actors and independently scheduled timer

[[03_Reverse_Engineering/findings/FIND-0018-actor-transition]] adds seven bounded
mappings, 342 disjoint bytes / 68 instructions. Totals at that checkpoint: **78 simulation
mappings / 87 indexed functions**, with the existing fragments unchanged.

| Original scope | Native destination | Compared boundary |
| --- | --- | --- |
| FUNC-0081 `[710E,7126)` | `MotionUpdate::transition_start` in `step_actor` | Coast, select wait for later, initialize transition immediately, actual return |
| FUNC-0082 `[7126,7154)` | `MotionUpdate::transition_wait` | Coast first; on zero direction save requested position and set shared mode=7 |
| FUNC-0083 `[A148,A16A)` | `step_transition_coast` | Fixed signed DBF count; zero returns without terrain work |
| FUNC-0084/0085 `[A16A,A180)` / `[A180,A196)` | Coasting pixel loop | Wrapped X, foot contact, conditional Y decrement, double damping |
| FUNC-0086 `[13208,1324E)` | `start_transition` | Exact shared fields and typed curve assignments; retain dirty flag |
| FUNC-0087 `[1345A,134D6)` | `step_transition_timer` | Independent word countdown/direction/level update; no palette consumer |

306,528 original/native cases pass per preset. The ordinary movie adds 17
continuous actor-wrapper and 17 separate timer comparisons, with actual caller
returns and independent unhooked equality. These handlers require explicit
transition context; completion also requires shared action globals. All contexts
commit with the actor, scratch and tracking, including rollback after a late
unsupported service. Preceding world entry, palette conversion, other objects
and mode scheduling remain outside this contract. The next selector at that
checkpoint was 632A, resolved below.

## Deferred coasting initializer and handler

[[03_Reverse_Engineering/findings/FIND-0019-coasting-handler]] adds two bounded
mappings, **42 bytes / eight instructions**. Totals at that checkpoint: **80 simulation
mappings / 89 indexed functions**, with existing fragments unchanged.

| Original scope | Native destination | Compared boundary |
| --- | --- | --- |
| FUNC-0088 `[630A,632A)` | `begin_coasting` | Explicit associated actor; set tracking selector, mode, first word and next handler; return without movement |
| FUNC-0089 `[632A,6334)` | `MotionUpdate::coast` in `step_actor` | Associated control binding; immediate A148 tail with original pending return; retained selector |

A148 physics is reused from FUNC-0083/0084/0085, without duplicate byte/function
coverage. This handler needs no shared transition/action context. Late wrapper
failure preserves actor, scratch and tracking. 87,571 cases pass per preset.
The recording supplies one P1 initializer followed by sixteen continuous native
wrapper calls with independent unhooked equality. P2 initialization is observed
but not compared; broader world state and its transition start remain separate.


## Tally path (initially partial)

[[03_Reverse_Engineering/findings/FIND-0020-tally-handler]] adds **210 bytes /
48 instructions**, three bounded helper mappings and two partial handler mappings.
Totals at that checkpoint: **83 bounded simulation mappings plus two partial tally handlers /
94 indexed functions**, alongside the existing fragments.

| Original scope | Native destination | Implemented boundary |
| --- | --- | --- |
| FUNC-0090 `[51C8,5204)` | `MotionUpdate::tally` | Zero-gate immediate common branch; palette path extended by FIND-0021 and common bonus path by FIND-0022 |
| FUNC-0091 `[5222,52B0)` | `MotionUpdate::tally_wait` / common tally branch | Coast, counter/Start decisions, mode=3 completion; 5266 table selection now covered by FIND-0022 |
| FUNC-0092 `[537C,53DE)` | `TallyState` update in `step_actor` | Signed countdown, one-time Start bypass, unit decrement, credit and sound request |
| FUNC-0093 `[AF98,AFB0)` | Word credit operation in `step_actor` | Wrapped addition then unsigned cap at 180 |
| FUNC-0094 `[4F8C,4F8E)` | Retained handler return | Shared RTS with current handler return pending |

The function index records entry fragments, with overall function ends left
unknown. Metadata separately includes the 52A6 completion fragment. Only its
six original regions contributed native/classified bytes at that checkpoint.
FIND-0021 adds 51D0 and its dependencies; FIND-0022 adds 5266 below. A148 is reused without duplicate coverage.
The tally context commits with actor, tracking, scratch and other globals; any
late service/budget/resource/unsupported-path failure rolls back all changes.
The movie comparator retains mutable tally counters, as well as actor state,
across all 175 calls. Sound requests are not audio-driver playback.


## Tally palette preparation and wait

[[03_Reverse_Engineering/findings/FIND-0021-tally-palette]] adds **232 disjoint
bytes / 56 instructions**, extends FUNC-0090, and adds four bounded mappings.
Totals at that checkpoint: **87 bounded simulation mappings plus two partial tally handlers /
98 indexed functions**. Exact metadata: `re/palette_step.json`.

| Original scope | Native destination | Implemented boundary |
| --- | --- | --- |
| FUNC-0090 extension `[51D0,5204)` | `MotionUpdate::tally` | Nonzero gate: coast/wait, fixed palette preparation, initialize transition, defer 5204 |
| FUNC-0095 `[5204,5222)` | `MotionUpdate::tally_palette_wait` | Coast/wait; select deferred 5222, no same-call countdown |
| FUNC-0096 `[1324E,13294)` | `start_tally_transition` | Direction FFFF, six-call initial countdown, zero reload/level/scope and logical tally curves; retain dirty/positions |
| FUNC-0097 `[137CE,137F6)` and FUNC-0098 `[1372C,13754)` | `prepare_tally_palette` | Fixed bank 2: sixteen source words to sixteen B/G/R intensity triplets; retain source |

Arbitrary helper banks/counts/aliasing and curve evaluation are outside scope.
All palette state participates in late-failure rollback. 214,448 comparisons
per preset and 37 continuous controlled-state wrapper calls verify the new
behavior. Both experiment endpoints match independent unhooked execution.
The ordinary movie's 175-call zero-gate tally contract still passes. At that
checkpoint 5266 was unsupported; the following pass resolves it. No
world/render/audio parity or native playability is claimed.


## Bonus control-table selection

[[03_Reverse_Engineering/findings/FIND-0022-bonus-slots]] adds **150 disjoint
bytes / 43 instructions**, promotes both tally handlers to bounded mappings,
and adds a bounded scan plus a partial selector. Totals at that checkpoint: **90 bounded
simulation mappings plus one partial selector / 100 indexed functions**.

| Original scope | Native mapping | Compared contract |
| --- | --- | --- |
| FUNC-0090/0091 shared `[5266,52A6)` | `step_actor`, optional `TallyState::bonus` | Existing sample request, special gate, up to five assignments and partial/full exhaustion; mode=3 completion reused |
| FUNC-0099 `[451A,4526)` | `allocate_bonus` availability scan | First zero or negative word, positive-prefix scan, bounded extent/work |
| FUNC-0100 `[4770,47BA)`, D2=0 only | `allocate_bonus` selection | Equality-only cursor reset, word multiply/add wrap before unsigned remainder, skip nonzero and preserve exact source word |

160,680 comparisons per preset, sixteen independent goldens and all new
instructions pass. Three controlled one-wrapper experiments from the movie
match native output and independent unhooked execution. This selects words in
control tables; it does not allocate actor objects. Malformed data/budgets and
late-service failures roll back all state. Negative sentinel completion commits
partial success. Nonzero-D2 47BA and downstream consumers remain unsupported.
Exact metadata: `re/bonus_step.json`; evidence: `re/bonus_validation.json`.


## Exit tally and conditional completion

[[03_Reverse_Engineering/findings/FIND-0023-exit-tally]] adds **150 disjoint
classified bytes / 32 instructions**. Of these, 146 bytes / 31 instructions have
successful native comparisons; the branch at 5166 reaches explicitly rejected
53F2. Totals at that checkpoint: **91 bounded simulation mappings plus two partial mappings /
102 indexed functions**. Exact metadata: `re/exit_tally_step.json`.

| Original scope | Native mapping | Compared boundary |
| --- | --- | --- |
| FUNC-0101 `[5132,5188)`, partial | `MotionUpdate::exit_tally`, `TallyState::exit_state` | Called unit consumption, last-unit countdown=60 and return, later Start/skip transition tail and deferred 5188; secondary 53F2 rejects |
| FUNC-0102 `[5188,51C8)` | `MotionUpdate::exit_tally_wait` | Coast/wait, save requested position, word-equality marker clear, mode=1; retained selector |

348,668 comparisons per preset and 231 continuous ordinary movie wrappers pass.
A separate controlled equality experiment verifies marker clearing. Independent
unhooked endpoints match. The reused 537C helper has different pending returns
when called here versus tail-entered from 5222. Late failures roll back all state.
Full-movie address discovery finds no unregistered P1 selector, which is distinct
from whole-route or whole-frame native parity. Evidence: `re/exit_tally_validation.json`.


## Secondary tally and score thresholds

[[03_Reverse_Engineering/findings/FIND-0024-secondary-score]] adds 280 new bytes /
71 instructions plus the previously classified transfer at 5166. FUNC-0101 is
promoted for bounded primary/secondary/transition behavior. Totals at that checkpoint:
**97 bounded simulation mappings plus one partial / 107 indexed functions**.

| Original scope | Native implementation | Contract |
| --- | --- | --- |
| FUNC-0103 `[53F2,5458)` | `step_actor`, optional `TallyState::score` | Secondary countdown/Start, count decrement, score call, sound request, delay=3 and tail return |
| FUNC-0104 `[ADF4,AE1A)` | `add_packed_score` via `add_score` | Valid eight-digit addition/wrap; original comparison here fixes source to 00010000 |
| FUNC-0105 `[AE1A,AE4C)` | `add_score` | Strict threshold comparison, one reward, bounded repeated threshold addition |
| FUNC-0106 `[AE4C,AE72)` | `add_packed_score` via `add_score` | Valid threshold/increment addition, scratch retention and carry/wrap |
| FUNC-0107 `[AF28,AF5C)` | `add_score` / `ActionSample::score_reward` | One request; word increment unless exactly 9; no audible-effect claim |

328,916 comparisons per preset, 20 goldens and eleven controlled movie wrappers
pass. All 72 scoped instructions execute, including the reused transfer. Invalid
consumed digits are explicit scope failures in both adapters; zero/cyclic threshold
progress fails the work budget. All caller state and requests roll back on late
failure. Existing sample/control trace defaults remain unchanged; score enables
only its explicit deeper stack/mailbox and score-write contract.
Metadata: `re/score_step.json`; evidence: `re/score_validation.json`.


## Physical input and one-seed session

[[03_Reverse_Engineering/findings/FIND-0025-p1-session]] adds 214 bytes / 54
instructions and one mapping. Totals at that checkpoint: **98 bounded simulation mappings
plus one partial / 108 indexed functions**.

| Original scope | Native implementation | Contract |
| --- | --- | --- |
| FUNC-0108 `[14E4E,14F24)` | `convert_pad_byte`, `produce_pad_control`, `src/sim/input.*` | Stateless three-button conversion, FF/00 fields, opposite-direction cancellation, scoped action combinations |
| Measured movie `[3100,3200)` P1 phase | `step_p1_session`, `src/sim/session.*` | One seed and physical inputs only; retained actor/control/tracking/scratch and ordinal; full wrapper ordering; fixed resources/gate/parameters |

1,024 converter cases and 100 one-seed movie wrappers pass per preset. Per-call
world feeds are zero for this window. New session composition is not counted as
an additional original function. The inactive timer/other world phases are
observed but not executed by this API. Unsupported actions/contexts reject
transactionally. Runtime targets remain emulator-free; native playability none.


## Level banner and retained early session

[[03_Reverse_Engineering/findings/FIND-0026-level-banner-session]] adds one
bounded request mapping: **99 bounded simulation mappings plus one partial /
109 indexed functions**. Exact boundaries/data: `re/level_banner.json`.

| Original scope | Native implementation | Contract |
| --- | --- | --- |
| FUNC-0109 `[63E2,644C)` | `request_level_banner`, `src/sim/banner.*` | Scratch Y=row; ordered logical label/number requests; difficulty 0..3; final-stage equality; wrapped arguments/destinations |
| Measured movie `[700,1067)` pre-P1 phase | optional banner in `step_p1_session` | One initial 35-field seed, then physical inputs; banner before conversion/wrapper; combined rollback |
| `[17532,17558)`, `[17568,175E8)` | research only | Original rendering callees execute with a bounded VDP write sink; no native renderer or pixel comparison |

66,880 request/scratch cases and 367 retained early wrappers pass in each
preset. Repeated fixtures can be checked with `session-compare`; it verifies
original capture hashes/contracts and labels reuse honestly. General world
scheduling and rendered/audio output remain unsupported in the session.


## Retained reversal ownership and post-P1 phase

[[03_Reverse_Engineering/findings/FIND-0027-retained-reversal-session]] composes
existing native mappings, adding no function entry. The early effect phase now
includes its observed return-only +46 tail. Seven static/observed instructions
(28 bytes) are context, not additional restricted execution coverage.

| Original evidence | Native implementation | Scope |
| --- | --- | --- |
| P1 spawn frame 1067, release 1078; loop 69A4..69CE | optional `P1SessionState::effects`, `ReversalEffects::step_active` | Persistent bounded logical P1 pool; ascending slots; presentation/follow on birth and release; combined rollback |
| Effect +46 = 12646 through actual return 69C2 | Fixed return-only effect service | No additional mutation/request; not a generic service dispatcher |
| Shared foreign allocations/releases and B126 zero clear | Research observation only | No global pool capacity/order or renderer equivalence |

390 wrappers/390 banners/twelve sound requests and twelve effect updates match
per native preset from one seed and physical inputs. One fresh original capture
and independent unhooked replay; three fresh native comparisons reuse its raw
evidence. Both facings, slot reuse/order and late ownership/budget/capacity failures
have authored checks. Totals remain 99 bounded mappings plus one partial / 109
indexed; native playability none. Evidence: `re/effect_session_validation.json`.


## Trail allocator client, random recurrence and particle

[[03_Reverse_Engineering/findings/FIND-0028-trail-allocator-client]] adds three
bounded mappings, bringing totals to **102 bounded plus one partial / 112
indexed functions**. Exact scope: `re/trail_step.json`.

| Original scope | Native implementation | Contract |
| --- | --- | --- |
| FUNC-0110 `[6D8C,6E32)` | `step_trail_emitter`, `src/sim/trail.*` | Signed countdown; both newest X/Y pairs gate allocation; two RNG calls before owner lookup; five-position history shift; transaction rollback |
| FUNC-0111 `[5A9A,5AE4)` | `make_trail_particle`, `step_trail_particle` | Explicit capacity; mode85, frames227..234, FAA4 release, fixed 5AE2 handler/12646 service; initializer delay3, emitter override2 |
| FUNC-0112 `[E918,E948)` | `next_trail_random` | Word recurrence, state and mirror retained, logical shifted result |
| Existing phase `[69AA,69C2)` | Optional emitter active/presentation phase and particle phase | Actual handler/service returns verified; release still reaches both fixed return-only selectors |

209,082 original/native cases per preset cover all 62 new instructions. One
fresh ordinary capture compares 34 retained emitter calls, eight spawns and 97
newborn particle updates in each preset. Owner position/capacity are context;
the API returns particles and release events without owning a shared pool.
Births before/after the loop iterator wait/run immediately respectively in the
reference; integrating that ordering with P1 remains the next pass. Initializer
6D22, other world clients and E948 are excluded. Native playability none.


## Retained mixed allocation and object iteration

[[03_Reverse_Engineering/findings/FIND-0029-mixed-object-pool]] composes existing
native mappings; totals remain **102 bounded plus one partial / 112 indexed**.

| Original evidence | Native implementation | Boundary |
| --- | --- | --- |
| F994 pop / FAA4 push and loop 69A4..69CE | `MixedPool`, `src/sim/mixed_pool.*` | Seeded logical slot/free order; generations, initial live particles, one forward walk and same-pass reuse |
| P1 before world loop, emitter resolves current owner | `step_mixed_session` | Banner/input/P1 then mixed phase; physical-only later rows; owner/capacity native; combined rollback |
| Thirteen fixed occupied objects, including two inactive | `ExternalReservation` | Explicit occupancy projection only; private original behavior audited, not natively executed |
| Five new private-code ranges and table, `re/mixed_session.json` | Research only | 260 code bytes / 67 instructions plus 48 data bytes; collision hit 7910 unsupported; no added native function count |

34 retained invocations, 136 trail updates, twelve reversal updates, nine
allocations/releases and 191 pool events match every preset, including complete
free-stack order. Prior dedicated-session behavior remains available and tested;
it cannot coexist with a mixed pool in one session. External reservations are
valid only under the independently checked noninterference contract. At this
checkpoint, 7808/7CA4 were the next replacements; the following section delivers
them. Native playability remains none.


## Rising and gated visibility objects

[[03_Reverse_Engineering/findings/FIND-0030-private-object-updates]] promotes
86 already classified bytes into two bounded native mappings: **104 bounded
plus one partial / 114 indexed**. No ROM bytes are counted twice.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| FUNC-0113 `[7808,783A)` | `PrivateUpdate::rising`, `step_private_object` | Full longword gate; Y reset or equality stop; signed wrapping countdown and Y decrement; opaque retained control link |
| FUNC-0114 `[7CA4,7CC8)` | `PrivateUpdate::gated_visibility`, `step_private_object` | Ordered word gates overwrite flags, then X/Y; zero preserves state |
| Existing `[69AA,69C2)` | Scheduled private API and `MixedPool` kind 5 | Active/presentation/handler/fixed RTS service; any invoked callback rejects; combined pool/session rollback |
| FF31B0/31A6/31A4 | `PrivateGlobals`, optional retained session seed | No writers in the ordinary comparison interval; gate producers remain outside native scope |

277,232 original/native cases pass per preset. The retained session matches
136 private updates and 327 total ordered pool events, including existing
particles, reversals and emitter. Four reservations become native objects;
nine remain. No per-call environment feeds are introduced. See
`re/private_step.json`, `re/private_validation.json`. Native playability none;
next reconstruct 7A88 table motion and its bounded context.


## Retained table motion

[[03_Reverse_Engineering/findings/FIND-0031-table-motion]] promotes 7A88 to
FUNC-0115: **105 bounded simulation mappings plus one partial / 115 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[7A88,7AD6)` with `[7A58,7A88)` table | `TableMotion`, `step_table_motion`, `src/sim/table_motion.*` | Full-word toggle, count+1 DBRA, logical cursor, wrapped coordinates/delta and signed countdown reversal; bounded consumed inputs |
| `[69AA,69C2)` scheduled phase | Mixed-pool kind 6 | Presentation before handler, fixed RTS service; callback79B6 rejects; whole-session rollback |
| FF31BC word | Optional `PrivateGlobals::table_loop_count`, eight-field seed | Retained once, physical-only later rows; no writes in captured interval, missing/excessive inputs reject |
| `[7A46,7A58)` / `[7CC8,7CEA)` | Research only | Reset and gated increment fragments verified; no native callback or full producer claim |

406,634 original/native cases per preset and 34 retained table updates pass.
All 361 ordered pool events match; eight external reservations remain. The
callback79B6 and collision-hit7910 boundaries stay unsupported. Writer fragments
add 52 research bytes; handler/table bytes were already classified. Native
playability none. See `re/table_motion_step.json`, `re/table_motion_validation.json`.


## Control overlap and retained miss-only collision

[[03_Reverse_Engineering/findings/FIND-0032-collision-miss]] adds FUNC-0116 and
partial FUNC-0117: **106 bounded mappings plus two partial / 117 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| AC5E..AC9C | `overlaps_control` | Unsigned inclusive word arithmetic; X-only mask; no RAM writes |
| 78EE..7910 | `step_collision_probe` | P1 then gated P2; miss return only; hit7910 rejects |
| Slot 63 / ordered world phase | `CollisionProbe`, `MixedPool`, `step_mixed_session` | Presentation, fixed RTS handler, service; P1 wrapper tracking resolves each call |

Thirteen-field seed header adds mask/gate/optional secondary tracker to the prior
eight fields. Later rows remain physical masks only. Missing consumed inputs,
invoked callbacks and hits roll back P1, banner, pool, allocations and RNG.
Seven return-only reservations remain, including two inactive occupied slots.
478,345 original/native cases per preset and fresh 34-call movie comparisons
(395 ordered events) pass; 196 Python tests and 44 CTests per preset pass.
P2 producers, callback79B6, hit7910 and whole-world/render/audio behavior remain
unsupported. Exact hashes and report paths: `re/collision_validation.json`.


## Retained return-only objects and dormant occupancy

[[03_Reverse_Engineering/findings/FIND-0033-return-only-objects]] composes the
existing `[69AA,69C2)` dispatch, F76C presentation and 12646 RTS. No new original
function mapping: totals remain **106 bounded plus two partial / 117 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| Fixed RTS handler/service, callback zero | `ReturnOnlyObject`, `step_return_only_object` | Active/presentation/two RTS calls; invoked callback rejects |
| Inactive but occupied slots 52/66 | `MixedPool`, event kind 3 | Retain fields/generation, exclude from free stack, emit inactive observation without update budget |
| Five active slots 58–62 | Pool kind 8 | Retain all represented fields, audit remaining bytes zero and exact writers |

The movie adapter no longer falls back to an external reservation. The generic
reservation type remains available to older explicitly scoped callers. Unknown
selectors/fields reject; later inputs remain physical masks. All phase/session
failures roll back state and allocation/RNG changes. 286,848 component cases and
633 ordered movie records match per preset; 198 Python tests and 46 CTests pass.
Initializers/activation producers and callback79B6/hit7910 remain unsupported.
Evidence: `re/return_only_validation.json`. Native playability none.


## F9E2 allocation and return-only pair initialization

[[03_Reverse_Engineering/findings/FIND-0034-pair-initializer]] adds FUNC-0118 and
FUNC-0119: **108 bounded mappings plus two partial / 119 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[F9E2,FA1E)` A6 pop and defaults | `MixedPool` pop inside `initialize_return_only_pair` | LIFO top, generation increment; six F9E2 fields typed; inherited fields required, never defaulted |
| `[FA1E,FA30)` endless VDP loop | Rejection | No allocation, generation, inheritance or order change; not an original return value |
| `[7B9C,7C26)` two pops and stores | `make_return_only_pair_member`, `initialize_return_only_pair` | First 161/270 916..921 4/4; second 164/270 from 919, 5/5, flags 0800 |
| `MOVE.L A6,FF31C0` | `MixedSessionState::return_only_anchor` | Logical second-member identity; mixed header 14 carries and prints it |
| Free-slot residue | `PoolSlot::inherited`, seed tag 9 | Only from verified evidence; cleared by any allocation; released slots unknown |

F994 remains the A5 allocator used by reversal/trail clients. 8,714 restricted
original/native cases per preset, ordinary frames 0..1066 and the anchored
34-call mixed window pass. The level-setup caller, 7C26, other F9E2 callers,
FA30, pool resets, 7AD6/callback79B6, overlap-hit FF31C0 readers and hit7910 are
not native. Hashes and reports: `re/pair_initializer_validation.json`.
Native playability none.


## 7C26 gated-visibility pair initialization

[[03_Reverse_Engineering/findings/FIND-0035-visibility-pair]] adds FUNC-0120:
**109 bounded mappings plus two partial / 120 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[7C26,7CA4)` two pops and stores | `make_visibility_pair_member`, `MixedPool::initialize_visibility_pair` | 287/152 frames 892..901 and 287/184 frames 902..911, 5/5, 7CA4; no flags/anchor |
| Shared two-pop transaction | `MixedPool::initialize_pair` (with 7B9C) | LIFO order, generations, inheritance required, exhaustion rejects |
| Pair identities and inheritance | `InheritedObjectFields`, `PairMember`, `ObjectPair` in `src/sim/reversal.hpp` | Shared pool identity types |

8,714 restricted cases per preset and the ordinary frames 0..1066 replay pass;
the private seed adapter verifies unrepresented bytes. Gate producers, the rest
of level setup and callbacks are not native. Hashes and reports:
`re/visibility_pair_validation.json`. Native playability none.


## 7772 rising pair initialization

[[03_Reverse_Engineering/findings/FIND-0036-rising-pair]] adds FUNC-0121:
**110 bounded mappings plus two partial / 121 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[7772,7808)` two pops and stores | `make_rising_pair_member`, `MixedPool::initialize_rising_pair(control)` | 158/262 frames 922..927; second at first X+32 (word), same Y, frames 928..933; 5/5; 7808; countdown 0 |
| Caller A5 stored at +4A | Explicit logical `ActorId control` argument | Adapter maps 0/FF0690/FF0838; unmapped rejects |
| `LEA (A6),A4` and A4-relative copies | First member's position passed to the second | A4/A6 register effects are not native state |

8,714 restricted cases per preset and the ordinary frames 0..1066 replay pass.
Gate producers, the rest of level setup and callbacks are not native. Hashes and
reports: `re/rising_pair_validation.json`. Native playability none.


## 783A collision quad initialization

[[03_Reverse_Engineering/findings/FIND-0037-collision-quad]] adds FUNC-0122:
**111 bounded mappings plus two partial / 122 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[783A,78EE)` four pops and stores | `MixedPool::initialize_collision_quad(control)` over the shared N-pop `initialize_group` template | All-or-nothing; exhaustion at any pop or unknown inheritance at any member rejects |
| First member: 78EE probe | `make_quad_probe` → `CollisionProbe` | Mode 80, (150,262), frame 912, extents 0038/0008, caller control |
| Members 2..4 via `LEA (A6),A4` copies | `make_quad_return_only` → `ReturnOnlyObject` | (X+32,Y), (X,Y+32), (X+32,Y+32) word wrap; frames 913..915; link inherited |
| Unwritten +08..+0D, +0E, +10 | `InheritedObjectFields::presentation` plus target/countdown | Required for every member; seed tag 9 gains an optional four-field tail |

Pair initializers keep their two-pop wrapper and do not need inherited
presentation. Restricted original comparisons and the ordinary frames 0..1066
replay are recorded in `re/collision_quad_validation.json`. Hits (7910), the
rest of level setup and callbacks are not native. Native playability none.


## 6EC8/6EDC dormant objects and the `[6886,68A4)` setup prefix

[[03_Reverse_Engineering/findings/FIND-0038-setup-prefix]] adds FUNC-0123/0124
and one mapped level-setup fragment: **113 bounded mappings plus two partial /
124 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[6EC8,6EDC)` / `[6EDC,6EF0)` one pop, `MOVE.L A6,FF31B4/B8`, mode cleared | `MixedPool::initialize_dormant`, `initialize_dormant(state, DormantAnchor)` → dormant `ReturnOnlyObject` | Frame 021D, flags 0; position, +08..+0D, target, countdown, link inherited |
| Unwritten +02/+04 position | `InheritedObjectFields::position`; seed tag 9 gains a two-field tail | Required, with presentation, for dormant members only |
| FF31B4 / FF31B8 | `MixedSessionState::dormant_anchors` | Retained logical identities; their reader 7AD6 is not native |
| `[6886,68A4)` LEA + six BSRs | `initialize_level_setup_prefix(state, control)` | Twelve ordered pops and three identities, all-or-nothing; `control` is FF0690's logical identity |

`wiznliz-return-only` gains `--dormant-pool`, `--prefix` and `--prefix-pool`.
Restricted original comparisons and the ordinary replay are recorded in
`re/setup_prefix_validation.json`. 7AD6, callback79B6, hit7910, the rest of
level setup from 68A4 and other F9E2 callers are not native. Native playability none.


## 6A94 pickups, 6EB6 control links and the `[68A4,68BC)` setup tail

[[03_Reverse_Engineering/findings/FIND-0039-setup-tail]] adds FUNC-0125..0129
and a second mapped setup fragment: **118 bounded mappings plus two partial /
129 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[6A94,6AF0)` record/FF31AC/FF31B0 clears and the sixteen-entry pass | `initialize_pickups(state, PickupTables, control)` | Kinds FFFF skipped; FF4C80 positions consumed densely; records in creation order |
| `[6AF0,6B44)` + `[6B44,6BB2)` + `[6BB2,6BD6)` | `make_pickup`, `MixedPool::initialize_pickup` → `Pickup` | Word MULU/ADDI frames, the 020D/0205/01FD families, cadence 1/1 only for count 2, Y + 16 wrap; target inherited |
| `[6BD6,6C00)` miss path | `step_pickup` sharing 78EE's miss logic | Ordinary-replay evidence only; hit target 6C00 rejects; not indexed until a restricted corpus covers it |
| FF447A records, FF31AC | `MixedSessionState::pickup_records`, `activation_target` | Logical entries; their consumers (6C00, 7AD6) are not native |
| `[6EB6,6EC8)` | `initialize_control_link(state, player)` → `control_links` | 6EC8's dormant shape; identity is the control's +1A2 link |
| `[68A4,68BC)` | `initialize_level_setup_tail(state, tables, control)` | 6A94 then both links; all or nothing |

`wiznliz-return-only` gains `--tail` and `--tail-pool`. Evidence:
`re/setup_tail_validation.json`. The 6C00 pickup hit, 6D22/FB06, 7AD6 and the
setup from 68BC are not native. Native playability none.


## 7DB8 setup message, 6EF0 gate and the 6BD6 pickup service

[[03_Reverse_Engineering/findings/FIND-0040-setup-message]] adds FUNC-0130..0133
and a third mapped setup fragment: **120 bounded mappings plus four partial /
133 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[7DB8,7E18)` message selection | `continue_level_setup(state, tables)` | Two players: none; FF31AA set: FRUIT RETURNED and clear; ≥ 2 kinds: MIX THOSE FRUIT |
| `[CB72,CB9A)` priority gate | Same call; `ControlMessage` (+46/+53/+56) | Signed byte compare with 0x64; refusal sets +46 to none |
| `[CB9A,CC18)` message-row clear | `MessageRowClear{vram}` request only | VDP writes research-only; destination = tilemap + 14 + row << 7 (low word) |
| `[6EF0,6F02)` pair gate (partial) | Same call | Closed gate does nothing; open gate rejects; the E918/F9E2 pair path is not native |
| `[6BD6,6C00)` pickup miss service (partial) | `step_pickup` | Shared 78EE miss logic; 6C00 hit rejects |
| `[68BC,68C4)` | `continue_level_setup` | 7DB8 then 6EF0, all or nothing |

`wiznliz-return-only` gains `--message`; `wiznliz-collision` gains
`--pickup-service` and `--pickup-scheduled`. Evidence:
`re/setup_message_validation.json`. Native playability none.


## 7FBE/7154/735E/7568 gated pairs and the `[68C4,68D4)` setup step

[[03_Reverse_Engineering/findings/FIND-0041-gated-pairs]] adds FUNC-0134..0137
and a fourth mapped setup fragment: **124 bounded mappings plus four partial /
137 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[7FBE,8040)` P2-placed pair | `MixedPool::initialize_gated_pair(GatedPair::p2_placed, …)` | Gate FF3172; partner (FF80,FF80); lead from FF0838 +3C/+3E − (8,FFE8), countdown 60, caller A5 |
| `[7154,71CE)` first fixed pair | `initialize_gated_pair(GatedPair::first_fixed, …)` | Gate FF3174; partner (0,0); lead (0310,00B0), countdown 30, FF0690 |
| `[735E,73D8)` second fixed pair | `initialize_gated_pair(GatedPair::second_fixed, …)` | Gate FF3176; lead (039C,0066) |
| `[7568,75E2)` third fixed pair | `initialize_gated_pair(GatedPair::third_fixed, …)` | Gate FF3178; lead (0234,0078) |
| `[68C4,68D4)` | `initialize_gated_pairs(state, GatedPairInputs)` | Four gated initializers in order, all or nothing |

Pops are ordered by address (slot order): the lower becomes a `ReturnOnlyObject`
partner and the higher a `GatedLead` naming it. Lead handlers 8040/71CE/73D8/75E2
(countdown, 5964 and their callbacks) are not native: an active lead rejects
when stepped. `wiznliz-return-only` gains `--pairs` and `--pairs-pool`.
Evidence: `re/setup_pairs_validation.json`. Native playability none.


## 6C00 pickup hits: carrying and swapping fruit

[[03_Reverse_Engineering/findings/FIND-0042-pickup-hit]] adds FUNC-0138..0144 and
promotes FUNC-0133 (6BD6) to bounded: **131 bounded mappings plus four partial /
144 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[6BD6,6C00)` pickup service | `walk_pickup` contact test | Now bounded: the hit continues natively |
| `[6C00,6CDA)` hit (partial) | `MixedPool::walk_pickup`, `MixedPool::step(..., PickupWorld*)` | Sound request, link test, exchange; the 020D/0205/01FD family branches reject |
| `[6D22,6D8C)` carry | `carry_pickup` | FB06 copy into the dormant link as a carrying `TrailEmitter`; the record names it |
| `[6CDA,6CF4)` / `[6CF4,6D22)` swap callbacks | `walk_pickup` phases `swapped_out` / `swapped_in` | 5964 then 2/2; re-dress from the record's kind, X + 8, same-walk service |
| `[59BC,5A06)` vanish | `begin_pickup_vanish` | Pickup use only; release through FAA4 |
| `[5964,59AE)` return | `walk_pickup` (6CDA) | Pickup use only |
| `[FB06,FB1A)` copy | `carry_pickup` | Pickup → link only |

`PickupWorld` carries the control identities, +1A2 links, FF447A records, FF312C
kinds and the FCB32 requests; without it a contact rejects as before.
`wiznliz-collision --pickup-hit` exposes the walk. Evidence:
`re/pickup_hit_validation.json`. Native playability none.


## 7910 probe hits: delivering the carried fruit

[[03_Reverse_Engineering/findings/FIND-0043-fruit-delivery]] adds FUNC-0145 and
FUNC-0146: **133 bounded mappings plus four partial / 146 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[7910,79B6)` probe hit | `MixedPool::walk_probe`, `MixedPool::step(..., PickupWorld*)` with FF31B0 from `PrivateGlobals` | Gate and dormant-link returns; delivery from an active carrying `TrailEmitter`; exhaustion and other links reject |
| `[59AE,59BC)` sparkle | `deliver_carried` → `TrailParticle` | F9E2 pop at the emitter's position − (8,8), then 59BC |
| 5964 / FB06 / F994 on the link | `deliver_carried` → `DeliveredPickup`, dormant `ReturnOnlyObject` | Mode 87 at (00A4,00F6), callback 79B6; the link keeps the copy's fields with mode 0 |
| copy walks | `step_delivered_pickup` | Presentation and RTS selectors; callback79B6 rejects |
| `78EE` walk | `walk_collision_probe` | Returns the contact for 7910; `step_collision_probe` keeps its rejecting form |

The sparkle pops before the copy from the shared stack; no FF447A record
changes. `wiznliz-collision --probe-hit` and `--delivered` expose the hit and
the later walks. Evidence: `re/delivery_validation.json`. Native playability
none.


## callback79B6 and 7AD6: the first ingredient

[[03_Reverse_Engineering/findings/FIND-0044-first-ingredient]] adds FUNC-0147 and
FUNC-0148 as partial mappings: **133 bounded mappings plus six partial / 148
indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[79B6,7A00)` + `[7A26,7A58)` callback79B6 (FF31AC zero) | `MixedPool::walk_delivered`, `MixedPool::step(..., PrivateGlobals*, ..., PickupWorld*)` | The copy becomes a `TableMotion`; D20E posted; FF31BE/FF31BC stored; the FF31AC-nonzero path (7A00) rejects |
| `[CB72,CB9A)` | `post_message` | Shared by 7DB8 and 79B6; CB9A stays a `MessageRowClear` request |
| `[7AD6,7AE6)` + `[7B22,7B42)` 7AD6 (FF31AC zero) | `walk_delivered_slot` | FB06 into the dormant FF31B4 object, FF31AC and the record name it, FAA4 releases the copy; 7AE6 (FF31B8, FF31B0, the 7B42 anchor) is not native |
| 7A88 on the released copy | `step_table_motion` (handler only) | The freed slot keeps a mode-0 table object |

`PickupWorld` gains FF31AC, FF31B4/FF31B8, both controls' message fields, the
tilemap, FF31BE and the row clears; `SetupMessage` gains `first_ingredient` and
`second_ingredient`. `wiznliz-collision --ingredient` exposes the walk.
Evidence: `re/ingredient_validation.json`. Native playability none.

## The retained level world

[[03_Reverse_Engineering/findings/FIND-0045-retained-world]] adds no mapping: it
composes the setup and every mapped object routine into one native run of the
level's pool across frames 634..1065 (**133 bounded mappings plus six partial /
148 indexed**, unchanged).

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[6886,68D4)` from the 6886-entry stack | prefix, tail, `continue_level_setup`, `initialize_gated_pairs` on one `MixedSessionState` | All 68 slots free at entry; the setup's identities seed the world |
| Object loop (69A4..69CE, all 68 slots in address order) | `MixedPool::step(owner, position, random, budget, PrivateGlobals*, CollisionInputs*, PickupWorld*)` per loop | One carried `PickupWorld`, globals and `TrailRandom`; births, releases and generations native |
| E918 calls by non-pool code (109E4/10A00, object FFFF32C2) | `next_trail_random` applied a supplied number of times | The caller is not native; its state is never supplied |
| Message producer (P1/P2 +46/+53/+56 between loops) | Explicit per-loop updates of `PickupWorld::messages` | Not native |
| P1 actor (tracking, FF1AB4 position) | Supplied per loop | `step_mixed_session` does not yet carry the world |

`wiznliz-collision --world-pool` (`tools/native/world_transport.hpp`) exposes it.
Evidence: `re/world_pool_validation.json`. Native playability none.

## The native player joined to the world

[[03_Reverse_Engineering/findings/FIND-0046-world-session]] adds no mapping
(**133 bounded mappings plus six partial / 148 indexed**, unchanged).

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| Setup identities after 68D4 | `establish_world` | Moved into `MixedSessionState::world`; one authoritative copy; identities must stay live |
| Object loop after P1's wrapper (6986 → 69A4) | `step_world_phase` from `step_mixed_session` | P1's tracking feeds 78EE/6BD6, its actor position the 6D8C owner |
| Between-loop producers | `WorldUpdates` | E918 call counts and message updates stay inputs |
| Level-start fade (1345A active, 634..668) | `P1SessionState::transition`, `step_transition_timer` before the banner (session 050) | Palette consumers 13432/1350E not native |

`wiznliz-session --world-session` exposes it. Evidence:
`re/world_session_validation.json`. Native playability none.

## The second ingredient, the spell countdown and 7CC8

[[03_Reverse_Engineering/findings/FIND-0048-spell-mixing]] promotes FUNC-0147
(callback79B6) and FUNC-0148 (7AD6) to bounded and adds FUNC-0150 (7CC8,
bounded) and FUNC-0149 (7B42, partial): **136 bounded mappings plus five
partial / 150 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[7A00,7A26)` callback79B6 (FF31AC set) | `walk_delivered_slot` | D22F through `post_message`; the copy's +32 is the negated FF31AC drift; no FF31BE/FF31BC store |
| `[7AE6,7B22)` 7AD6 (FF31AC set) | `walk_delivered_slot` | FB06 into the dormant FF31B8 object; `PickupWorld::spell` (FF31B0) and the record name it; `PrivateGlobals::rise_gate` nonzero; the FF31C0 anchor becomes a `SpellCountdown` (012C, the copy's control) |
| `[7B42,7B4E)` + 7B56 anchor handler | `SpellCountdown`, `step_spell_countdown` | Counts +10 down; 13294 and the 7B58 store at 7B4E reject |
| `[7CC8,7DB8)` (BSR from 6972 each frame) | `MixedPool::mix_spell` from `step_world_phase` before the loop | FF31BE/FF31BC countdown with FF31B0 set; the 11-field exchange of the FF31AC/FF31B0 table objects |
| FF31C0 anchor identity | `PickupWorld::anchor` (moved from the session's return-only anchor by `establish_world`) | The setup's dormant 7B9C second member |

`wiznliz-collision --second-ingredient`, `--anchor` and `--spell-mix`
(`tools/native/spell_transport.hpp`) expose them. Evidence:
`re/spell_validation.json`. Native playability none.

## The spell's completion: recipe, sparkle and exit door

[[03_Reverse_Engineering/findings/FIND-0049-spell-completion]] promotes FUNC-0149
(7B42, now continuing through 13294) to bounded and adds nine bounded and five
partial mappings (FUNC-0151..0164) and extends FUNC-0132 (6EF0) through its
allocating path: **146 bounded mappings plus nine partial / 164 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[13294,132D2)` | `start_spell_fade_out` | The level is kept; curves are the 135EA (tally) resource |
| 7B42 negative, `[7B4E,7B56)`, `[7B58,7B8A)` wait, `[7B8A,7B9C)` | `SpellPhase`, `step_spell_countdown(object, timer)` | Waits read the session's FF0B90; 7B8A's 12646 makes the anchor a `ReturnOnlyObject` |
| 7B58's completion, `[7E18,7EF4)`, `[8652,867E)`, `[95EE,9614)`, 1324E | `MixedPool::complete_spell` (`walk_anchor` for one walk) | Only recipe 8652; 9288, other effects, 9182, FF31A8 set, 9682/9614 and exhausted allocation reject |
| `[7F08,7F6A)`, `[7F6A,7FBE)` | `make_spell_sparkle`, `step_spell_sparkle`, `MixedPool::walk_sparkle` | Particles through the shared stack (5A9A); E918 from the shared `TrailRandom` |
| `[6F02,6F44)`, `[6F7A,6FB6)` | `make_door_sign`, `make_exit_door` | FF33E2 set (6F44) rejects |
| `[6FB6,6FCA)`, 5964, `[6FCA,705C)`, `[705C,7082)` | `ExitDoor`, `step_exit_door` | 6FCA raises the sign (4C08); entering (7082) and two players (7072) reject |
| `[4C08,4C52)` | `DoorSign`, `raise_door_sign`, `step_door_sign` | Fourteen-word bob table |
| The 83DA recipe table | `recipes`, `recipe_effect`, `ingredient_fruit` | All 105 pairs; effects other than 8652 named for rejection |

`MixedPool::step` takes the session's `TransitionState` (committed with the
phase); `PickupWorld` adds FF31A8, FF316C, FF33E2, FF0690's +3C/+3E,
FF31C4/FF31C6 and FF316E. `wiznliz-collision --anchor/--completion/--sparkle/--door`
(`tools/native/completion_transport.hpp`) expose them. Evidence:
`re/completion_validation.json`. Native playability none.

## Entering the exit door: the level's end

[[03_Reverse_Engineering/findings/FIND-0050-door-entry]] adds FUNC-0165 (4CA2,
bounded) and extends FUNC-0161 (705C) through its contact path: **147 bounded
mappings plus nine partial / 165 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[7082,70FE)` | `DoorStep::entered`, `MixedPool::enter_exit_door` | FF0F00 (`exit_control`), the anchor's 12646, the single-player camera words (`exit_camera`); an active +1A2 link (70FE) rejects |
| `[4CA2,4CBE)` with FAA4 and 59BC | the sign's release, `vanish_exit_door` | The door becomes a vanishing `TrailParticle` at (-8,+8) |
| 7082's tail on P1 (630A's shape, handler 710E) | `begin_exit_transition`, applied by `step_world_phase` | Selector FFFF, mode 80, frame 021D, `transition_start` |
| 710E/7126 in the joined session | `step_mixed_session` passes the session's `TransitionState` and `P1SessionState::actions` | Already native (FIND-0018); FF33E0 = 7 ends the level |

`wiznliz-collision --door` covers the entry; `wiznliz-session --world-session`
seeds and prints the curves, the saved position and FF33E0. Evidence:
`re/door_entry_validation.json`. Native playability none.

## The scene after the level: its doors

[[03_Reverse_Engineering/findings/FIND-0051-hub-doors]] adds FUNC-0166..FUNC-0175
(nine bounded, 17298 partial) and three mapped hub fragments: **156 bounded
mappings plus ten partial / 175 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[5E86,5E8E)`, `[63A4,63E2)` | `initialize_hub`, `update_hub_door_states` | FF33DE's clear is not modeled |
| `[60E6,611E)`, `[611E,61F6)`, `[6334,63A4)` | `MixedPool::initialize_hub_doors`, `make_hub_door`, `make_hub_door_numbers`, `make_hub_door_lock`, `make_hub_door_partner` | All pops commit together; exhaustion names F9E2 or F994; a number outside the 639A table rejects |
| `[61F6,621A)`, `[621A,623C)`, `[FAC4,FAE4)` with F76C and FAA4 | `step_hub_door` (`HubDoorPhase`) | Any other presentation callback and FAC4 reviving a released slot reject |
| `[623C,630A)` with FA8C, 630A and 13208 | `MixedPool::enter_hub_door`, `vanish_hub_door`, `hub_requested_position`; `step_world_phase` applies 630A to P1 | 17298 and P2's 630A are reported in `HubEntry`, not carried; a second entry in one loop rejects |
| `[5F5E,5F76)`, `[6024,6040)` | `MixedPool::step` with `HubWorld`; `hub_loop_ends`, `MixedSessionResult::scene_ended` | The hub loop has no 7CC8 or 179F8: Up/Down reach only P1's actor |

`wiznliz-collision --hub-doors/--hub-door/--hub-exit`
(`tools/native/hub_transport.hpp`) expose them; `wiznliz-session --hub-session`
builds the doors from the records and free stack and prints the pool image
after every loop. Evidence: `re/hub_validation.json`. Native playability none.

## The scene change: the level and the hub as one run

[[03_Reverse_Engineering/findings/FIND-0052-scene-change]] adds FUNC-0176..FUNC-0183
(five bounded, three partial), five mapped scene-change fragments and four
research-only executed callees (1720C, 1737E, 446C, 17284): **161 bounded
mappings plus 13 partial / 183 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| `[488,49E)` | `enter_hub_scene` reads the timer's requested position as the anchor | FF0690's +A2/+A4 themselves are not carried |
| `[17024,17058)`, `[F850,F8F2)`, `[F940,F994)` | `reset_object_pool`; the actors are rebuilt by `make_hub_actor` | 1720C's render lists are not native |
| `[16FB4,16FBA)`, `[16FF8,17004)`, `[131C2,13208)`, `[5ED4,5EDC)` | `HubSceneEntry::acceleration_gate`, `start_fade_in`, the countdown writes | 16EA4's other writes are VDP/RAM setup, not carried |
| `[9880,99D4)` with 5964 | `make_hub_actor`, `hub_actor_parameters`, tracking selector 0 | Control words +08/+0C/+18/+3A/+96/+98/+B6/+68 and 1737E's camera words are not native; P2's actor is compared, not carried |
| 5D58, 63A4/60E6, 63E2 | `enter_hub_scene`: FF33E0 = 7, `initialize_hub`, `request_level_banner` (row 000D) | Two players reject |

`wiznliz-collision --scene-change` exposes the components;
`wiznliz-session --game-session` runs the level, the scene change and the hub in
one process (switching to the hub's terrain). Evidence:
`re/scene_change_validation.json` (completed by session 056). Native
playability none.

## After the hub: the hint screen and the second level's entry

[[03_Reverse_Engineering/findings/FIND-0053-second-level-entry]] adds FUNC-0184
(14E3C, bounded) and five mapped fragments: **162 bounded mappings plus 13
partial / 184 indexed**.

| Original scope | Native implementation | Boundary |
| --- | --- | --- |
| 1959E's 16EA4 and FF0F10 = 00F0 | `enter_hint_screen` (`reset_object_pool`, P1's actor zeroed to its 12646 selectors, `start_fade_in` with 001E, the gate cleared) | The text, its scripted sprite (stride 0x90) and the VDP/graphics loading are not native |
| `[14E3C,14E4E)`, `[1972E,19766)` with 13208 | `merge_action_buttons`, `continue_hint_screen`, `step_hint_screen` (`HintScreen`) | 14DA2's device reads are `produce_pad_control` |
| E2A's 16EA4, `[E44,E52)`, 9880 | `enter_second_level`: the timer's saved position cleared, `make_hub_actor` at it | E2A's control words (+38, +78/+7A, +F2), FF4C7A and the resources are not native |
| 118C's `[11A6,11EE)` with E918, `[1356,1364)`, `[774,77C)` | `choose_action_cooldown`, `reset_actor_appearance`, FF33E0 = 0013 | 54BA, 2512, 1386, 1454, 4484, E876, 17298 are not native (their E918 draws are counted inputs) |

`wiznliz-collision --second-level|--hint-screen` expose the components;
`wiznliz-session --game-session` with the second level's scene and bank runs the
hint screen, the entry and P1 alone on the second level's captured terrain.
Evidence: FIND-0053 (checkpoint; `re/second_level_validation.json` pending).
Native playability none.
