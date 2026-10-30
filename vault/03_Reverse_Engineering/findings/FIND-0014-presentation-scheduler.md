---
id: FIND-0014
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Presentation scheduler and callback-before-handler ordering

`src/sim/presentation.*` reconstructs the bounded presentation scheduler and six
actor callbacks. `step_scheduled_actor` composes presentation with the supported
native actor dispatcher **in the same invocation**, selecting the movement
handler after the callback. This is an actor phase, not a completed game frame.
Task: [[07_Tasks/TASK-0010-grounded-controller]]. Native playability remains none.

## Identity, scope and evidence

Original ROM: 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
`re/presentation_step.json` pins **364 additional disjoint bytes / 90 instructions**
in eight ranges, 25 direct transfers, two explicit indirect selectors and stop/
unsupported boundaries. FUNC-0049 through FUNC-0055 are seven routine mappings;
the additional dispatch fragment is separately named, not invented as a complete
function. There are now 55 indexed functions and 46 simulation routine mappings,
plus two idle initializer fragments and this scheduled-dispatch phase.

| Half-open ROM range | Role and exact boundary |
| --- | --- |
| `[F76C,F850)` | Presentation countdown, frame advance/loop/bounce and optional callback tail jump |
| `[F8F6,F906)` | Active-bit test, BSR F76C, select +16 handler and JSR; stop before F906, or before inactive F90C |
| `[A2E8,A2EC)`, `[A380,A384)` | Idle-turn callback tails to existing A3D4/A512 ground initializers |
| `[A50E,A512)`, `[A654,A658)` | Normal reversal callback tails to A512/A3D4; facing changes here |
| `[A774,A7A8)`, `[A93A,A96E)` | Fast-jump cycle countdown and later presentation assignment, through RTS |

Original-68000 static decoding includes the 68000/68020 sentinel, closed direct
edges and explicit indirect edges; unknown callback identity remains a rejected
exit. Five selected instructions also pass GNU decoding. The installed GNU
plugin rejects immediate BCHG opcode 086e, so that instruction is **not** claimed
as GNU-corroborated. Musashi's mode/bounce cases independently execute its effect;
the selected GPGX actor windows do not establish bounce-mode coverage.
The initial failed probe is retained; no original instruction was patched.

Restricted sanitized Musashi executes the original scheduler/callbacks and
active dispatch fragment. Scheduled calls stop before F906/F90C with the caller
stack still pending; no fabricated RTS. The later +46 service is excluded.
Original sound-selector mismatch behavior remains as documented in
[[03_Reverse_Engineering/findings/FIND-0013-actor-dispatch]]. Native C++ targets
never link or execute an emulator.

## Exact semantic ordering

The player wrapper tests actor mode byte +0 bit 7. An inactive actor skips both
presentation and movement. F76C itself only tests bit 0; its component API can
therefore run on non-player presentation state without imposing that wrapper.

When bit 0 is set, byte +C decrements with wrap. Nonzero returns immediately.
Zero reloads +C from +D. Thus starting counter zero wraps to 255, and reload zero
produces a full 256-invocation countdown. It does not advance every invocation.

If bit 2 is set and the **old** frame word +6 equals target +E, a callback is
pending. Frame advancement still happens first:

- Bit 1 clear increments the frame word; bit 1 set decrements it, wrapping words.
- The old frame is compared against end +A (forward) or begin +8 (reverse).
- At that endpoint, bit 3 clear loops to the opposite endpoint. Bit 3 set toggles
  direction and restores the old endpoint, holding it for another countdown.
- A pending callback is then entered by JMP through +1A. It sees the advanced
  frame/mode and returns directly to the scheduler's caller. Reaching the target
  in the current advance alone does not invoke it yet.

Four turn/reversal callbacks enter the existing normal-ground initializers:
mode 81, words 2/0/5, counters 4/4, appropriate facing and ground handler. Target,
cycles and callback identity persist. The wrapper reads +16 **after** this return
and executes the selected ground handler immediately. For example, the user's
normal reversal at movie frame 3163 completes through A50E and runs A546 within
that same scheduled actor call. Frame 4374 analogously runs A654 then A408.

Both fast-jump callbacks decrement word +10 with wrap. A nonzero result copies
begin +8 into current +6. A zero result assigns mode 81, words 24/24/29 and
counters 2/2. Neither changes the movement handler, facing, target or callback.
An initial cycle word zero becomes FFFF; it does not complete the animation.

`step_presentation` commits actor state only on success. Unknown/retained
callbacks are valid dormant values but **reject when invoked**. The scheduled
wrapper copies actor and terrain state, then commits presentation, handler
changes, shared scratch and returned sound requests together. A later handler,
resource or budget failure rolls back even an already-completed callback.
Presentation work is constant and bounded; actor continuation/terrain budgets
remain explicit. Inactive actors consume no handler budget.

## User movie and continuous native comparison

The unchanged movie from [[08_Sessions/2026-10-02-013-user-movie]] has SHA-256
`c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd`.
Its original mislabeled hash is corrected only in derived import metadata.
The new tools consume the already verified recording and pin its input digest,
5,298 input rows, complete settings, zero edits and frozen worker build
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`.

A selected-PC survey observes **4,139 active P1 actor calls** and **16,840 selected
trace events** over all 5,298 movie rows. These are different quantities. The
survey contributes zero native comparisons, rejects any overflow and matches
the earlier unhooked movie's declared covered-state hash at frame 5298.
It discovers ordinary fast reversal at A96E/frame 1067 and A7A8/frame 2189, plus
9D4E/frame 1616 and 9C56/frame 1629. Those remain research leads with unimplemented
effects, not new supported native handlers.

The dedicated native comparison uses three ordinary, unedited half-open movie
windows: **[700,1067), [3100,3200), [4360,4400)**. They contain 367, 100 and 40
calls respectively. All **507 scheduled actor outputs** match; all **507 separate
presentation outputs** match at F900. Do not add these as 1,014 game frames.
The windows observe A774 and A93A four times each, A50E and A654 once each, and
16 ordered sound requests. A2E8/A380 completion is covered by authored sequences
and Musashi, not by this movie's selected windows.

The comparator validates explicit F8FC/F900/F904/F906 boundaries, A5/A6 pairing,
stack depth, actual F900/F906 return words, callback/handler selection, phase
ordering, absence of uncontracted actor writes and continuous actor-field identity
between calls. Every contracted native actor field persists across a window.
The native sequence transport treats subsequent actor columns as **assertions**,
never replacement state, and rejects any divergence instead of reseeding.

Inputs, parameters and shared terrain scratch are sampled environment inputs
at each actor boundary. Scratch can be written by other objects between calls;
this is not a native world simulation. Terrain map/records are normalized from
original RAM; their bytes agree at the window endpoints. No claim of observing
every possible transient terrain write is made. All eighteen contracted actor/
scratch fields and ordered sound request arguments match at each return.

A fresh independent **unhooked** worker matches the declared covered-state hash
at all three window ends. Hooks, traces, checkpoints, native input/output files,
full RAM and build/source hashes are retained in ignored local storage. No GUI
control or runtime rebuild occurs. Hash equality is not full hidden-device,
whole-frame, rendered-animation or audio-waveform parity.

## Verification and next boundary

`re/presentation_validation.json` pins the reports. Each of debug, release and
ASan+UBSan passes **347,320** original/native cases, 24 authored goldens and four
exact unknown-callback rejection checks; all 90 new instructions are visited.
Across fresh regression corpora all 737 scoped instruction addresses are visited.
[[05_Validation/RESULTS]] and [[08_Sessions/2026-10-02-014-presentation-scheduler]]
record reproducible commands and results.

Next investigate fast reversal's allocation/dependent object/callback ownership
with the ordinary movie windows around frames 1067 and 2189. Up/down actions,
+46 post-handler service, world/frame scheduling and native audio remain open.
TASK-0010 stays in progress; full native playability remains none.
