---
id: FIND-0018
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Actor transition, coasting and shared timer

[[07_Tasks/TASK-0010-grounded-controller]] now implements 710E/7126, their A148 coasting and 13208 initializer,
and the separately scheduled 1345A timer. These are seven bounded mappings,
four disjoint ROM ranges, **342 bytes / 68 instructions**. Static hashes and
closed transfer graph: `re/transition_step.json`; reproducible original/native
and movie evidence: `re/transition_validation.json`. Native playability is none.

## Exact boundaries and ordering

| Half-open range | Verified behavior |
| --- | --- |
| `[710E,7126)` | Reload associated control from actor+4A, call A148, assign 7126, tail JMP 13208 with the selected-handler return still pending |
| `[7126,7154)` | Reload control, call A148, test FF0B90; if zero copy FF4446/48 to control+A2/A4 and write mode FF33E0=7; RTS |
| `[A148,A16A)` | Fixed initial horizontal pixel count; zero speed returns without a query; sign chooses a pixel helper |
| `[A16A,A180)` / `[A180,A196)` | Wrapped X minus/plus one, 9B5C foot contact, decrement Y if equal, call then tail to 9A6C for two damping operations |
| `[13208,1324E)` | Initialize shared transition fields and curve identities, RTS directly to the actor caller |
| `[1345A,134D6)` | Shared direction/countdown/level update, separate from actor execution |

710E **does not execute 7126 in the same invocation**. Its tail executes 13208
immediately and returns to F906. The wait handler always coasts before checking
completion, ignores current pad fields, and retains itself even after mode=7.
That mode's subsequent world dispatch is outside this native contract. Actor+4A
is an explicit caller-bound associated-control context, not a native RAM pointer.

A148 differs from ordinary 9AAE movement. It never settles at zero speed and does
not run the upper probe, speed-limit, boost or airborne-entry paths. Its NEG.W,
ASR.W and DBF count is fixed before damping: speed 32 still moves two pixels;
speed 8000 requires 64,513 pixels. Host budgets reject transactionally. Terrain
scratch persists, including above-map queries; coordinates and speed wrap as words.
Presentation, facing, vertical motion and airborne delay are retained.

## Shared transition state

13208 writes direction FF0B90=1, level FF0B96=14, countdown FF0B92=1,
reload FF0B94=1 and palette scope FF0EDE=0. Curve pointers FF0B98/9C become
1356A and FF0BA0 becomes 135AA. It **preserves dirty FF0EDC**, requested coordinates
and saved coordinates. Native curves are typed logical resources; raw original
addresses occur only in research adapters. Unknown retained curves are never
dereferenced by these phases.

1345A does nothing for zero direction. Otherwise a nonzero countdown decrements
as a word and returns. At zero countdown, negative direction targets level 14
with +2; positive direction targets level 0 with -2. Exact endpoint equality
clears direction and sets dirty=FFFF. Other levels wrap by two, set dirty=FFFF
and reload countdown. There is no clamp: odd or malformed levels need not reach
the endpoint. The timer does not read curves or update palette scope.

Static context identifies 13432 as a later dirty consumer and 1350E as curve-based
palette conversion. **Those consumers, curve contents, palette/device writes and
world scheduling are not implemented or counted as reconstructed.** The native
timer is called explicitly; it is never silently inserted inside actor updates.
`ActionGlobals::mode` remains the single modeled FF33E0 word.

## Independent original and movie execution

The project-owned Musashi harness executes original bytes, exact read/write
allowlists and actual returns with stack checks. No substitute RTS or ROM patch
is used. All **306,528 comparisons pass in each of debug/release/sanitize**;
all 68 new instructions execute. Sixteen authored goldens cover deferred entry,
completion, both coasting directions, input independence, timer endpoints/wrap
and dirty retention. Sweeps exhaust direction, countdown and level words independently (not their
Cartesian product), with boundary reload values; movement checks DBF bucket boundaries, signed overflow,
word wrapping, persistent scratch, authored and cataloged terrain. Native tests
also require rollback on missing context, mid-coast terrain failure, exhausted
budget and late unknown service after transition initialization/completion.

The preserved ordinary movie supplies **17 continuous wrapper calls and 17
separate timer calls at frames [1516,1533)**. It reaches 710E once and 7126 sixteen
times. The timer returns to EBF2 before the actor invocation. The wrapper returns
to 6986; its selected handler keeps F906 pending, including the initializer tail.
At 1532 the timer clears direction and the actor writes saved coordinates 0/48
and mode=7 in that same frame. These are two verified calls, not a native frame.

The native sequence retains actor, service and tracking coordinates across all
17 calls. Shared transition words match between actor and timer boundaries;
other game code clears dirty between phases and changes saved coordinates
between invocations. These environmental effects are supplied explicitly, not
claimed as native scheduling. Hooks check exact pending returns and stack
positions; overflow, missing boundaries and unknown writes reject evidence.
Fresh independent unhooked replay matches the hooked final covered-state hash.
No RAM/register/ROM edits or input branches were used for this capture.

## Remaining scope

The preceding 70D2 entry and dependent world objects, palette conversion and
later mode scheduler remain unimplemented. Next derive **632A at movie frames
1743–1758**. Other observed unmapped selectors are 51C8, 5132 and 5188. General
allocation, owner lifetime, multiplayer scheduling, rendering and sound playback
remain open. TASK-0010 stays in progress; no further recording is needed.

Update (session 049): the ordinary recording runs this timer with negative
direction right after the level setup: FF0B90 = FFFF at 634, FF0B92 counts 0014
to 0000, then FF0B96 steps 0 to 0E by two every other frame (writers 13472,
1348E, 134A0, 134A8) and FF0B90 is 0000 from 669
([[03_Reverse_Engineering/findings/FIND-0046-world-session]]). The P1 session
does not schedule the active timer yet.

Update (session 050): the session now runs this timer before the banner each
call when it carries one; the joined world session matches all 432 timer states
of 634..1065 ([[03_Reverse_Engineering/findings/FIND-0047-level-start-fade]]).
