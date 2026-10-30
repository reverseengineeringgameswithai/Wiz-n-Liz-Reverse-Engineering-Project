---
id: TASK-0008
type: task
status: complete
deliverable: Reconstruct a bounded original actor movement step using the verified terrain probes and independently executed state transitions
acceptance: ["Identify the A5/A6 state owners and callers before describing them as a player controller", "Validate the horizontal-step and collision-response chain near 0x9AAE, 0x9AC8, 0x9AF8 and 0x9B04 including all exits and called effects", "Establish position and velocity widths, signed arithmetic, DBF step counts and update ordering from original execution", "Implement a deterministic native movement step with explicit state/events and no invented fallback for unknown effects", "Compare authored boundary/collision cases and actual terrain sequences with pinned isolated original execution", "Keep frame timing, input and full playability claims separate; run sanitizers and commit synchronized Git/Obsidian checkpoint"]
---
# From terrain primitives to an actual movement update

Prior: [[07_Tasks/TASK-0007-terrain-query]]. Read
[[03_Reverse_Engineering/findings/FIND-0010-terrain-query]],
[[08_Sessions/2026-10-02-007-terrain-query]], `src/sim/terrain.hpp/.cpp`,
`re/terrain_query.json`, `tools/terrain_compare.py` and the isolated harness.

Confirmed native primitives now cover map/record query, three contact probes and
the one-pixel settling routine. Their callers use A6+2/+4 for position; player
ownership is not established merely by those offsets. The query's scratch
persists above the map, so preserve actual call ordering explicitly.

Discovery disassembly under `local/generated/terrain-research/9a5e.txt` shows:

- `0x9AAE` reads A6+0x22, separates sign/zero paths, shifts by 5 and uses DBF;
  do not assume a conventional fixed-point loop count or overflow behavior.
- `0x9AC8` / `0x9B04` decrement/increment x, call the foot/upper probes, adjust y,
  then on further mismatch modify A6+0x22 and call `0xACE8` / `0xACD6`, eventually
  transferring to `0xAA50`. All side effects and exits need bounded validation.
- Another chain begins at `0x9BAC`; the duplicate probe fragment at `0x2908`
  and the priority test near `0xA210` are context leads.

These leads are not verified complete functions. Initial discovery dumps contain
truncated endpoints; derive exact ranges and hash them before promotion.
Expand the research harness only for validated code/data ranges and output
contracts. Do not turn the native simulation into a CPU/RAM interpreter.
Prefer explicit native events for understood external side effects; unsupported
effects must fail rather than silently disappear.

Once one real movement update is established, integrate SDL3 input/rendering and
investigate audio toward M3. A terrain gallery or invented platformer does not
replace this task. SDL3 development dependency and original frame scheduling
remain outstanding; bounded headless reconstruction can proceed now.

## Completed result

[[03_Reverse_Engineering/findings/FIND-0011-movement-step]] establishes explicit
control/actor pairs and reconstructs eight original damping, horizontal-step,
limit and airborne-transition routines. Native semantic state and transition
counts match 282,233 original executions per preset; all 74 new instructions
are visited. The previous 614,436 terrain cases still pass. 106 Python tests
and 10 CTest targets pass, with debug/release/sanitizer comparison agreement.
Physical input ownership, the actual airborne handler and full frame scheduling
remain open. No complete controller or playability claim. Next:
[[07_Tasks/TASK-0009-airborne-update]]. Session:
[[08_Sessions/2026-10-02-008-movement-step]].
