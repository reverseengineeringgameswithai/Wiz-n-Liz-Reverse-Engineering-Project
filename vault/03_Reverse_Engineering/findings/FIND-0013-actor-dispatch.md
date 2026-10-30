---
id: FIND-0013
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Native actor invocation, grounded transitions and jump requests

Task: [[07_Tasks/TASK-0010-grounded-controller]]. `src/sim/actor.*` executes one
selected actor handler invocation, including its immediate continuations.
This closes the zero-speed landing-to-idle boundary from
[[03_Reverse_Engineering/findings/FIND-0012-airborne-update]]. It does not execute
the surrounding animation/frame scheduler. Native playability remains none.

## Identity, exact scope and evidence

ROM-LOCAL-0001 is 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Original bytes are unchanged. `re/actor_update.json` pins 21 disjoint ranges,
1,542 bytes / 315 instructions and every direct transfer. Its combined graph
has 647 instructions and explicit rejected exits to `9C56`, `9D4E`, `A7A8`,
`A96E` and `FCB42`. Six instructions belong to the restricted sound-selector
mismatch path; 309 implement newly compared actor behavior. The prior movement
metadata already classified 116 idle-handler bytes statically, so this adds
**1,426 newly classified bytes**, not 1,542. No disassembly dump is tracked.

Seventeen new bounded native mappings are indexed as FUNC-0032 through FUNC-0048.
Together with previous work there are 48 indexed functions, 39 simulation
mappings and two idle initializer fragments. A mapping with tail continuations
or rejected paths has no invented full-function end in `re/functions.csv`.

| Range or entry (hex, half-open ranges) | Verified behavior / boundary |
| --- | --- |
| `[A1BE,A1FA)`, `[A246,A27E)` | Idle priorities, damping, movement; up/down action exits reject |
| `[A1FA,A22C)` | Drop helper; conditional caller-return removal and immediate airborne entry |
| `[A27E,A2A6)` | Idle jump presentation, tail to shared jump requests |
| `[A2A6,A2E8)`, `[A33E,A380)` | Opposite-facing idle turn initialization, handler and presentation callback assignment, RTS |
| `[A2EC,A33E)`, `[A384,A3D4)` | Turn updates and jump presentation; distinct damping order |
| `[A3D4,A408)`, `[A512,A546)` | Normal grounded initialization and RTS |
| `[A408,A452)`, `[A546,A590)` | Normal grounded dispatch through idle/movement/fast/reverse/jump branches |
| `[A460,A50E)`, `[A59E,A654)` | Fast-mode assignment, normal jump presentation, reversal assignment/update tails |
| `[A6C8,A72A)`, `[A88E,A8F0)` | Fast grounded handlers; allocation-producing reversal exits reject |
| `[A738,A774)`, `[A8FE,A93A)` | Fast jump presentation and deferred callback identities |
| `[AA88,AAEA)` | Two ordered sound requests, delay/impulse initialization, fallthrough into airborne |
| `[FCB32,FCB42)`, `[FCB7A,FCB7E)` | Original sound selector mismatch return, research fixture only |

Static evidence uses original-68000 decoding, the 68000/68020 sentinel, seven
GNU corroborations and range/transfer hashes. Restricted Musashi execution and
full-machine GPGX captures independently check the native actor outputs.
Commands, current run counts and artifact paths: [[05_Validation/RESULTS]] and
[[08_Sessions/2026-10-02-011-grounded-controller]].

## State and ordering

Existing motion/terrain words retain their prior contracts. New control words
are ground acceleration at A5+5E (default 8), jump impulse at +62 (28), and jump
delay at +64 (10). Defaults are from the pinned initializer at `9952`; parameters
remain unsigned words with explicit signed comparisons and wrapping arithmetic.
Controls are +16 jump/held boost, +17 drop request, +1A/+1B up/down and +1C/+1D
left/right. The observed ordinary three-button producer maps these to B-or-C,
A, Up/Down and Left/Right respectively; see [[09_References/GENESIS_DEBUGGER]].
This does not generalize to other producer paths or multiplayer scheduling.

ActorState preserves target/cycle words at +E/+10 and a logical callback
identity corresponding to +1A, in addition to every existing MotionState field.
The native runtime has no original pointers or RAM layout. Presentation callbacks
are assigned and retained, not invoked by `step_actor`.

- Idle first calls the drop helper. Within the remaining idle path the
  same-facing direction wins, then opposite direction, then jump. Directional
  initialization returns without moving that call. With neither direction nor
  jump, damping runs; up/down actions are tested only if speed became zero.
- Drop queries the map at +(12,23). **Map-word bit 15**, not a contact byte,
  blocks the drop. Otherwise the original discards the helper's caller return,
  adds two to y, calls the airborne initializer and enters `AAEA` immediately.
  This does not resume the remainder of the idle/grounded handler. Terrain
  scratch persists, including above-map behavior.
- A408 checks gated jump before reversal. A546 checks reversal before gated
  jump. Both fast handlers check gated jump before reversal. These priorities
  are deliberately asymmetric. The gate does not suppress ordinary grounded
  directional acceleration.
- Normal movement damps first. With the same direction held, speed **after
  damping** greater than 144 (right) or less than -144 (left) selects fast
  presentation and skips that call's acceleration. Otherwise wrapped ground
  acceleration precedes the signed speed limit. Reload follows. Zero speed
  initializes idle and executes idle immediately, which can damp a second time.
- Fast movement damps, optionally accelerates and clamps, then tests the signed
  144/-144 thresholds. Slowdown assigns a normal handler, words 0/0/5 and
  counters 1/1, then moves; it does not execute the normal handler that call.
- Ground reversal initializes mode 87, words 23/19/23, target 19 and counters
  3/3, then executes its reversal handler immediately. Its facing bit is retained
  until the deferred presentation callback. Idle turns instead use words
  47/42/47 and target 42, change facing immediately and return.
- A384 damps before testing jump; A2EC tests gated jump before damping. A4EC
  accepts jump without the global gate. A634 with jump and a nonzero gate tails
  directly to horizontal motion, bypassing both damping and acceleration.
- Jump assigns the verified presentation, emits the two requests below, loads
  delay and impulse, and **falls through** into delayed airborne motion in the
  same invocation. The first delay decrement, +5 held boost, damping, airborne
  acceleration, gravity and motion all happen immediately. Held versus released
  input remains a byte, not a newly invented edge detector.
- Airborne zero-speed landing executes idle immediately. Other landing-selected
  handlers are assignments followed by RTS. Loss of contact inside horizontal
  movement also assigns airborne for later execution; its original pixel loop
  continues. The dispatcher does not execute every newly assigned handler.

## Effects and explicit exclusions

Jump writes two four-word argument blocks at `FFFF0A9E..FFFF0AA5` and calls
`FCB32` after each: `(60,1,192,1)` then `(107,1,192,2)`. `ActorResult` returns
these ordered `SoundRequest` values transactionally. They are a service request
boundary, **not native sound playback**. No host callback performs irreversible
work during simulation, and no requests publish if a later continuation fails.

The restricted reference executes the actual instructions with sound selector
`FFFF0AB6=0`, which mismatches both selectors and returns via `FCB7A`. It does not
patch, skip, intercept or fake an RTS. Active sound routing at `FCB42` and calls
to `ED974`/`ECFE4` remain outside that fixture. Full-machine captures leave the
actual sound driver enabled and compare the request arguments and actor fields,
not the driver's state or generated waveform.

Fast reversal `A7A8/A96E` calls `A818/A9DE`, which calls allocator `F994` and
may initialize another object and backlink. The allocator, dependent object
updates and presentation scheduling are not native here; the **whole invocation
rejects atomically** on those branches. Up/down actions `9C56/9D4E` select
additional handlers; the up path also consults globals `33D8/33DA/33E0`, raw
control+14 and audio-related call `ED6E6`. These branches reject before native
state commits. Their exploratory disassembly is discovery evidence only.

Callback assignments `A2E8/A380/A50E/A654` target normal grounded
initializers. Fast jump callbacks `A774/A93A` decrement presentation+10 and
change animation fields. Their invocation ordering is now reconstructed in
[[03_Reverse_Engineering/findings/FIND-0014-presentation-scheduler]]. The separate
`step_scheduled_actor` runs presentation before selecting the handler; this
handler-only dispatcher retains its original contract.

## API, host policies and comparisons

`step_actor` performs one semantic invocation corresponding to the selected
handler called by `F904` and returned at `F906`. It consumes supported immediate
continuations internally. There is no successful "pending idle" result. All
state, scratch and returned effects commit together only on success.

Defaults: at most 32 handler/continuation passes, a cumulative 1024 horizontal
pixels per invocation, and 4096 downward iterations per airborne phase. Host
budgets and invalid-resource rejection are intentional policies. Explicit
larger horizontal budgets permit the prior 8000-word arithmetic edge. The
continuation budget also rejects artificial jump/landing cycles.

`wiznliz-actor scene-id scene.bin bank-id bank.bin` accepts 35 decimal integer
fields in `tests/actor_cases.py::FIELDS` order. Every presentation input is
explicit. It follows up to sixteen handler invocations with the same inputs,
preserving state/scratch; no animation or video-frame progression is implied.
Outputs are sixteen actor fields, scratch x/y, horizontal/settle/landing counts,
sound-request count, applied invocation count, then four words per request.
The native executable reads extracted resources only, never a ROM or CPU core.

Full-machine comparisons use fresh ordinary routes and explicitly labeled RAM
experiments from a frame-1983 checkpoint. Selected pre-instruction events at
F904, the exact stored handler, and F906 prove the call boundary using A5/A6,
SP, and the actual F906 return address. All eighteen contracted actor/scratch
fields and ordered sound requests match. Remaining actor bytes must preserve
identity. Terrain records/map are captured from RAM and normalized to logical
resources; they must be unchanged at the end of each capture. Drops, overflow,
hook errors, unmatched boundaries, bad stack relations and binary mismatch
reject evidence. Hooked/unhooked replay compares only the declared covered-state
hash, not hidden device state. The ordinary routes now hit A27E and both fast
handlers; edited landing cases separately verify both idle continuations.
