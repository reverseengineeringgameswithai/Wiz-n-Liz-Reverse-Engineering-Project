---
id: FIND-0015
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Fast reversal and the lifetime of its dependent effect

Both fast reversal directions, their motion/animation callbacks and dependent
objects now execute natively. Allocation is an explicit bounded service with
logical owners and generation-checked handles. The caller must provide storage;
missing storage, exhaustion, invalid ownership and later failures reject
transactionally. [[07_Tasks/TASK-0010-grounded-controller]] remains in progress;
up/down actions and broader world services are still incomplete.

## Identity and exact scope

Original ROM: 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
`re/reversal_step.json` pins fourteen disjoint ranges, **576 new bytes, 119
instructions and 23 direct transfers**, plus the expanded known indirect
scheduler selectors. FUNC-0056 through FUNC-0067 add twelve bounded mappings;
there are now 67 indexed functions / 58 simulation mappings, two idle initializer
fragments, one scheduled actor phase and two bounded effect phases. A bounded mapping is not a complete
world subsystem or proof of a whole function's extent.

| Half-open range | Contract |
| --- | --- |
| `[A7A8,A7EC)`, `[A96E,A9B2)` | Fast reversal entry, allocate effect and fall through immediately |
| `[A7EC,A814)`, `[A9B2,A9DA)` | Restore control owner, jump/damp/accelerate/move |
| `[A814,A818)`, `[A9DA,A9DE)` | Presentation callback tails to opposite normal-ground initializer |
| `[A818,A87C)`, `[A9DE,AA40)` | Original allocation call and dependent object initialization |
| `[A87C,A88E)`, `[AA40,AA50)` | Follow owner X only, through RTS |
| `[F994,F9D0)` | Successful free-stack pop and selective initialization |
| `[FAA4,FABC)` | Clear activity and push released object on free stack |
| `[080A,081C)`, `[69AA,69BC)` | Active gate, presentation and selected effect handler; stop before +46 service or inactive tails 0822/69C2 |

Original-68000 decoding closes the graph against previously verified ranges and
explicit rejected exits. Both CPU decoder sentinels pass. Five new instructions
have independent GNU corroboration (control reload, left offset, predecrement
free-stack test, release push and BMI). The installed GNU plugin misdecodes
absolute MOVE.L opcode 23c8 at F9A0; that instruction is **not** GNU-corroborated.
The primary decoder and independent original Musashi/GPGX execution establish
its effect. The earlier immediate-BCHG limitation also remains recorded.
Bulk disassembly is ignored, not embedded into native runtime code.

## Actor ordering

A right-running actor reversing left enters A7A8; left-running reversing right
enters A96E. Both assign mode 85, current/begin/end 52/52/57, target 57 and
countdown/reload 3/3. They retain the cycle word and unrelated flags, explicitly
set the original facing, select A7EC/A9B2 and callbacks A814/A9DA, then allocate.
The allocation call returns into the reversal update **in the same actor call**.
The object is positioned using the actor's position before that call's movement.

Both reversal updates reload the paired control record from actor +4A because
allocation leaves A5 naming the new object. Jump +16 is checked first and ignores
the acceleration gate here, entering the original fast-jump path immediately.
Otherwise damping precedes opposite-direction acceleration/clamping and horizontal
movement. These handlers do not call the drop helper or perform the normal
fast-to-ground speed threshold check. Terrain may still replace the handler.
Existing initial fast-handler drop/jump priorities remain unchanged.

A814/A9DA tail to A512/A3D4. The presentation phase changes facing and selects
normal ground; the wrapper executes that newly selected handler immediately.
If another transition replaced the callback beforehand, no deferred turn
completion is synthesized. Authored/Musashi cases cover both completion tails,
all direction/jump/gate combinations and jump during reversal.

## Allocation, fields and owner lifetime

F994 saves A0, reads the free-stack head at FF311C and tests the preceding long.
A successful call decrements the global head and returns that object in A5.
It initializes only mode 80, no-op selectors +16/+46 = 12646, words +12/+14 = 0
and frame +6 = 541. Other object bytes retain their previous contents. Its last
flag-setting write is positive 541, so the helper's BMI is not a reachable
success outcome. Empty stack does **not** return a benign allocation failure:
F9D0 loops on VDP writes. Restricted reference execution stops before F9D0;
native exhaustion instead throws without changing actor, scratch or pool.

Effect setup assigns mode 85, current/begin/end 215/215/220, target 220,
countdown/reload 2/2, follow handler A87C/AA40, release callback FAA4 and owner
backlink +22. Allocator-cleared flags are then set to 0800 for the right variant
or zero for the left. Spawn offsets are asymmetric:

- Reversing from right: owner X +22, owner Y +15.
- Reversing from left: owner X −6, owner Y +16.

Coordinates wrap as words. Later follow updates copy owner X plus that same
horizontal offset; **Y stays at its spawn value**. The effect does not read the
owner's facing or movement selector, so it can outlive a terrain-induced change
to airborne. Untouched cycle/opaque bytes are checked as retained in original
fixtures; they are not invented as new native state dependencies.

Both observed object loops (0810/0816/081A/081C and
69B0/69B6/69BA/69BC) gate activity before presentation, then invoke the selected
handler without testing activity again. F76C advances/loops first; when its old
frame matches target, FAA4 clears mode and pushes the object into the free stack.
**The final X-follow still executes after release within that invocation.**
A subsequent invocation skips the inactive object. With these defaults, each
observed object receives twelve updates, including its spawn frame.
Two bounded loop-body phases are executed directly by the restricted original
reference. These are fragments, not complete native world-loop mappings. Their later +46 services remain outside the compared boundary.

## Native architecture and explicit limits

`src/sim/reversal.*` owns `ReversalEffect`, `ActorId`, `EffectId` and
`ReversalEffects`. The pool uses bounded host vectors, LIFO reuse and generation
checks. It supports up to 4096 slots as a host work limit, not an inferred
original capacity. Stable owner IDs replace original backlinks; the supplied
owner identity must match before following. Releasing twice does not duplicate
a free entry, and reused handles invalidate older generations.

`step_actor` / `step_scheduled_actor` accept optional `ReversalContext` and return
spawned handles. Their transaction includes actor state, shared scratch, effect
storage and ordered sound requests. A failure after internal allocation rolls
back that allocation too. `advance_presentation` shares the previously verified
field update with actor and effect scheduling. `step_reversal_effect` models
active gate, presentation/release and final follow; a pool step publishes release
only after successful state calculation.

This store contains reversal objects only. General world object allocation,
competition with other object types, owner destruction, complete scheduling,
rendering, +46 services and sound playback are not reconstructed. The original
free-stack addresses are normalized only in research tooling. No native target
loads a raw ROM or contains emulator code. These exclusions prevent a claim of
whole-frame or full-pool capacity parity. **Native playability remains none.**

## User movie and original-execution verification

Movie SHA-256:
`c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd`.
Canonical input SHA-256:
`34434f0aa0b1ebc7dbf4e464cd044ac52436b944bf6a01cdc24c811e1f6c3a88`.
The preserved 5298-row recording has complete settings, verified loaded binaries,
zero edits and an unhooked source baseline. Frozen Genesis build:
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`.

`reversal-capture` uses independent owned workers and ordinary windows
**[1048,1090)** and **[2170,2220)**. All **92 continuous actor calls** and
**24 continuous dependent-effect updates** match. Actor and effect state persist
between calls; later input state columns assert continuity and never reseed.
Each effect's owner position comes from the compared native actor output.
There are two allocations/releases and two ordered sound requests.

The left-running reversal creates FF2C12 at frame 1067 and releases it at 1078;
A9DA completes the actor turn at 1085. The right-running reversal creates FF2A3E
at 2189 and releases it at 2200. Terrain changes that actor to airborne before
its turn completion; A814 is **not observed** in this ordinary window, though
its semantics pass authored/Musashi comparisons. Both live object-loop variants
are observed. Missing phases, return/stack mismatch, wrong owners, unexpected
writes, broken continuity and any trace overflow reject evidence.

Fresh independent unhooked replays match both window-end declared covered-state
hashes. Inputs, parameters and shared terrain scratch still come from the
surrounding emulated world; terrain resources are equal at window endpoints.
None of this is whole-game native replay or hidden-device state parity.

**203,586/203,586** restricted original/native comparisons pass per debug,
release and ASan+UBSan preset, with identical output hashes and all 119 new
instruction addresses visited. Ten hand-calculated goldens and four exact
exhaustion rejections pass per preset. The corpus includes all owner-X words,
all mode/countdown bytes, animation/coordinate wrap, release ordering, boundary
speeds/acceleration, repeated actor calls and authored/cataloged terrain.
Exact reports and fresh regressions: `re/reversal_validation.json`,
[[05_Validation/RESULTS]], [[08_Sessions/2026-10-02-015-fast-reversal]].

Next bounded task: up/down actions 9D4E/9C56 around movie frames 1616/1629,
including shared globals, additional handlers and called effects. Keep rejecting
those paths until their entire bounded contract is understood.
