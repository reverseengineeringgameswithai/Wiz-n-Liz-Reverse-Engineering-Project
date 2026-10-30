---
id: TASK-0009
type: task
status: complete
deliverable: Reconstruct the original airborne update and its bounded landing transition using verified movement and terrain primitives
acceptance: ["Validate complete selected paths from 0xAAEA and 0xAB04 through vertical movement and landing, identifying every called effect and state dependency", "Establish delay, acceleration, vertical-motion arithmetic, collision ordering and landing side effects from independently executed original cases", "Model required control fields explicitly without claiming physical pad or frame ownership before tracing their producers", "Implement deterministic native airborne and landing state transitions with explicit supported effects and rejection of unresolved behavior", "Compare authored boundary and state-sequence cases plus cataloged terrain using the pinned isolated reference and all build presets", "Update coverage and Obsidian honestly, preserve the ROM, review explicit staging and commit a clean checkpoint"]
---
# Continue from the assigned airborne handler

Prior: [[07_Tasks/TASK-0008-movement-step]]. Read
[[03_Reverse_Engineering/findings/FIND-0011-movement-step]],
[[08_Sessions/2026-10-02-008-movement-step]], `re/movement_step.json`,
`src/sim/movement.hpp/.cpp`, `tools/movement_compare.py` and the restricted
reference harness. Fourteen terrain/motion semantic mappings are now compared
with original execution; the `MotionUpdate::airborne` event still needs its
original subsequent behavior.

Discovery only: `local/generated/movement-research/aa50.txt` includes the handler
at `0xAAEA`, continuation near `0xAB04`, vertical contact helper at `0x9BAC` and
landing lead near `0xAB8A`. These ranges have not been promoted as complete
functions. Derive exact endpoints and call closure before extending the harness.

The discovery suggests delay updates at actor+0x2A, vertical motion at +0x26,
control fields including +0x16/+0x1C/+0x1D/+0x60/+0x6C, and a global gate at
effective `0xFFFF0F16`. Confirm widths, signed overflow, flags, step counts,
up/down collision probes and all landing effects. Trace producers or expose
understood fields as explicit inputs; do not invent keyboard/gamepad behavior.
Preserve scratch call order and original continuation after state changes.

Use native events only for fully understood assignments/effects; an unknown
call must not become a silent no-op. Retain transactional host errors and
explicit budgets, documenting host policies separately from original behavior.
Repeated function calls are not game frames until scheduling is verified.

After this dependency, establish the actual controller/update schedule and a
bounded native input/rendering slice toward M3. SDL3 development files and a
full-game/frame reference remain outstanding. Headless reconstruction is
unblocked; no playable native game, airborne motion or landing is yet claimed.

## Completed bounded result

[[03_Reverse_Engineering/findings/FIND-0012-airborne-update]] reconstructs delayed
boost, airborne controls/gravity, horizontal/vertical contact and landing state
assignments. Eight routine mappings and two idle initializer fragments add
706 classified bytes. All 172 new instructions are exercised; 415,940 original
comparison cases pass per preset. Existing terrain and movement regressions pass.

A zero-speed normal landing falls directly into the idle controller. The native
result preserves that as an explicit immediate continuation, and original
comparison stops before the same instruction with its caller return pending.
No unknown idle behavior is skipped or counted as an executed frame. Resolving
those continuations and landing-selected grounded handlers is
[[07_Tasks/TASK-0010-grounded-controller]]. Session:
[[08_Sessions/2026-10-02-009-airborne-update]].
