---
id: FIND-0019
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Deferred coasting entry and the 632A handler

[[07_Tasks/TASK-0010-grounded-controller]] now supports 632A and its associated
initializer 630A. Two bounded mappings add **42 disjoint ROM bytes / eight
instructions**. Metadata and exact evidence: `re/coasting_step.json`,
`re/coasting_validation.json`, `tools/coasting_probe.py`,
`tools/coasting_compare.py`, `tools/genesis_coasting_capture.py`.

## Exact instruction and ownership boundaries

| Half-open range | Original effect | Native mapping |
| --- | --- | --- |
| `[630A,632A)` — six instructions | Control+1A6=FFFF; load associated actor from control+0 into A4; set actor mode=80, first presentation word=21D, handler=632A; RTS | `begin_coasting(ActorState&, ActorTracking&)` |
| `[632A,6334)` — two instructions | Load associated control from actor+4A into A5; tail JMP A148 | `MotionUpdate::coast` in `step_actor` |

The initializer runs on the actor associated with A5, **not the object in A6**.
Native references replace the original pointer lookup, and the capture verifies
that association. It retains position, horizontal/vertical motion, delay,
facing/flags, other presentation fields/callback/service and tracking coordinates.
Only the selector changes immediately; the later wrapper writes FF80/FF80.
The initializer neither moves the actor nor starts the shared transition.

632A executes A148 **in the same invocation**, retaining F906 as the pending
handler return. It leaves 632A selected. Input buttons, direction/facing and
shared transition completion do not select another handler or change world mode.
It requires no `ActionGlobals` or `TransitionState` to execute. The control reload
also establishes the association used by the wrapper's later tracking writes.

A148 was implemented in [[03_Reverse_Engineering/findings/FIND-0018-actor-transition]]:
fixed initial signed NEG.W/ASR.W/DBF pixel count, wrapped X, foot query, conditional
Y decrement and two damping operations per pixel. Zero speed performs no query.
The new mapping reuses that implementation, including persistent scratch,
64,513-step speed-8000 behavior, host budgets and transactional resource failures.
No duplicated physics or native interpreter was added. Unknown invoked service
still rolls back the entire wrapper after coasting.

## Static and restricted-original evidence

The exact ranges are hashed against the preserved ROM. Original-68000 decoding,
closed transfers through existing A148 dependencies and CPU sentinels pass.
Three supported GNU checks corroborate both pointer loads and the initializer
RTS. The installed GNU plugin's absolute-long JMP limitation is explicit; primary
decoding and original execution cover 632E's tail.

All **87,571 original/native cases pass per debug/release/sanitize preset**,
with eleven authored goldens and all eight new instructions visited. Entry tests
cover all selector/first-frame/vertical words in a correlated sweep, inactive
and active modes, existing handlers/callbacks and repeated initialization.
Coasting tests cover both facings, input combinations, signed count boundaries,
wrapping coordinates, above-map scratch, authored and cataloged terrain.
These are bounded corpora, not an exhaustive Cartesian state space.

Native tests verify retention and deferred motion, operation without shared
contexts, work-budget failure, unknown-service rollback and no-op zero speed.
Transport tests retain actor/service/tracking across an initializer followed by
updates and reject continuity drift. Synthetic trace tests reject missing or
misordered calls/returns, changed bindings, unexpected writes and overflow.

## Ordinary movie evidence

The owned worker captures [1742,1759) from the preserved recording with no input,
RAM, register or ROM edits. P1's initializer executes **after the ordinary actor
update in frame 1742**. It returns to 62F8. A6 is an auxiliary object; A4 becomes
the P1 actor from control+0. The same world routine also calls the initializer for
P2; that hit is retained as observation, **not native P2 validation**.

P1 then executes 632A once per frame **1743–1758**, through the full wrapper's
actual return to 5F3A. A148 keeps the original F906 return across the tail.
The native process first executes the initializer, then all sixteen wrapper
calls, retaining actor/service/tracking throughout. Shared world inputs are fed
explicitly. No actor state is reseeded at the initialization/update boundary.
All compared fields match, and an independent unhooked replay matches the final
covered-state hash. That hash does not include every hidden device bit.

`6302` calls the separate transition initializer after both actor initializers;
the surrounding world routine also touches other objects. Those world effects,
shared transition scheduling, P2 scheduling and visual palette consumption are
outside this comparison. The existing transition and wrapper movie contracts
were rerun successfully and remain separately scoped.

## Next scope

The next recorded unsupported handler is **51C8 at frames 3403–3577**. Derive its
instruction range, calls, state dependencies and return/continuation behavior
before promoting it to native code. Other remaining surveyed selectors: 5132
and 5188. General world allocation, ownership, rendering/audio and native
playability remain incomplete. TASK-0010 stays in progress.
