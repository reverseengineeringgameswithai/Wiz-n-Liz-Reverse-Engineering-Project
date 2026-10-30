---
id: FIND-0012
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0009
---
# Airborne movement, landing and immediate idle continuations

Task: [[07_Tasks/TASK-0009-airborne-update]]. The native simulation now executes
the delayed and falling airborne entries, terrain-dependent horizontal/vertical
motion and landing assignments. Original execution agrees through RTS or an
explicit **same-call idle continuation**. That boundary is preserved as an
event; it is not silently treated as a completed frame or a next-tick update.

Later work in [[03_Reverse_Engineering/findings/FIND-0013-actor-dispatch]] adds
`step_actor`, which consumes this component's pending idle work in the same
invocation. The smaller airborne API and historical comparison boundary below
remain unchanged.

## Exact scope and identity

ROM-LOCAL-0001 remains 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
No original changes. Half-open ROM/file ranges and transfers are pinned in
`re/airborne_update.json`. This pass classifies **706 additional disjoint bytes,
172 instructions**. It adds eight function mappings and two initializer
fragments; complete grounded/idle handlers are not included.

| Mapping / ranges | Compared native behavior | Instructions |
| --- | --- | --- |
| FUNC-0024 `[0x9BAC,0x9BCA)` and `[0x9C08,0x9C18)` | Airborne horizontal dispatcher | 15 |
| FUNC-0025 `[0x9BCA,0x9C08)` | Airborne left pixel; mismatch shares RTS at `0x9C54` | 17 |
| FUNC-0026 `[0x9C18,0x9C56)` | Airborne right pixel and shared RTS | 17 |
| FUNC-0027 `[0xAAEA,0xAB04)` | Delay/boost prefix, falls through into FUNC-0028 | 7 |
| FUNC-0028 `[0xAB04,0xAB8A)` | Airborne controls, damping, gravity and movement; landing continuation follows | 38 |
| FUNC-0029 `[0xAB8A,0xAC5E)` | Landing selection/assignments; zero speed can branch into idle initialization | 42 |
| FUNC-0030 `[0xA658,0xA690)` | Right-facing presentation reload from signed speed | 14 |
| FUNC-0031 `[0xA690,0xA6C8)` | Left-facing presentation reload from signed speed | 14 |
| `[0xA1A4,0xA1BE)` and `[0xA22C,0xA246)` | Right/left idle initialization fragments | 8 |

Noncontiguous/shared-tail or bounded handler mappings leave the CSV full end
empty. The two initializer fragments have symbols but do not increase the
function count. New routine ranges account for 654 bytes / 164 instructions;
initializer fragments account for 52 bytes / 8 instructions. No double count
of the shared RTS. The combined graph contains 332 instructions, with exactly
two explicit outgoing fallthrough edges to `0xA1BE` and `0xA246`.

`airborne-probe --disassemble` checks eleven range hashes, 54 reviewed transfers,
the combined graph, original-68000/68020 decoder sentinel and twelve short GNU
corroborations. As before, graph closure is structural, not a full stack-sensitive
proof. The actual return/continuation stack boundary is checked during execution.

## Inputs and state ownership

The paired control/actor records remain those in
[[03_Reverse_Engineering/findings/FIND-0011-movement-step]]. Newly consumed fields:

| Original effective owner / offset | Native meaning and width |
| --- | --- |
| A5+0x16, byte | Nonzero enables delayed boost; observed producer is B OR C (see later reference) |
| A5+0x1C / +0x1D, bytes | Left/right acceleration requests, tested for nonzero |
| A5+0x60, word | Acceleration amount, initialized to 12 |
| A5+0x6A, word | Contact damping count minus one, initialized to 11 |
| A5+0x6C, word | Gravity subtraction, initialized to 4 |
| RAM `0xFFFF0F16`, word | Nonzero suppresses horizontal acceleration requests |
| A6+0x12, word | Flags; bit 0800 selects right-facing landing |

Defaults come from the already pinned static initializer at `0x9952`, not a
captured game state. Parameters remain explicit words; unusual signed values
are preserved in comparison cases. Other flag bits remain unchanged. The BTST.B
at actor+0x12 tests bit 3 of the **high byte**, hence word bit 0800, not 0008.
Input producers were untraced in this pass; later scoped producer/cadence
evidence is in [[09_References/GENESIS_DEBUGGER]]. Complete scheduling remains open.

## Verified update ordering

1. Delayed entry `0xAAEA` decrements the delay word and tests the resulting sign
   bit with BMI, not a signed less-than comparison. If negative it assigns
   handler `0xAB04`. Otherwise a nonzero boost byte adds 5 to vertical motion.
   Thus delay 8000 wraps to 7FFF and remains in the delayed handler.
2. Both entries apply the existing counted horizontal damping. If the global
   gate is zero, left takes priority over right: clear/set flag 0800, subtract/
   add the acceleration word, then apply the corresponding signed speed limit.
   Word overflow occurs before the limit comparison.
3. If signed vertical motion is at least -48, subtract the gravity word. There
   is no post-subtraction clamp: the default -48 becomes -52. Values below -48
   remain unchanged. All additions/subtractions retain word wrap.
4. Airborne horizontal motion fixes its initial direction/count using the same
   NEG.W/ASR.W/DBF rule as the previous movement pass, including 64,513 steps at
   speed 8000. Each nonzero-speed pixel probes upper contact at +(12,22).
   Equality decrements y and damps speed by contact-count+1. The loop continues
   even after speed reaches zero. Its returned Z is always clear; a contact
   during that loop is not a landing indication.
5. At zero horizontal speed, the helper tail-calls one-pixel settling and exposes
   its equality result. Negative vertical motion lands immediately on that
   equality. Otherwise it performs `ceil(abs(vertical)/8)` settling calls,
   landing at the first equal comparison. The maximum is 4096. The zero-speed
   helper can already have made one additional downward pixel before this loop.
6. Nonnegative vertical motion still executes the horizontal helper first, then
   subtracts `(vertical >> 3)+1` from y as a word. There is no additional ceiling
   probe in this selected path. Zero vertical motion is included in this branch.

Neither landing nor idle initialization clears vertical motion or the delay.
The sequence contract therefore retains those values rather than inventing a
reset. Native scratch state follows every original query in order.

## Landing outputs and the bounded continuation

| Facing / signed speed | Presentation assignments | Assigned handler / native identity |
| --- | --- | --- |
| Right, speed greater than positive limit | Mode 0x81; words 0x06/0x0C/0x11; both counters 2 | `0xA6C8`, `fast_right` |
| Left, speed less than negative limit | Same fast presentation assignments | `0xA88E`, `fast_left` |
| Right, within limit and nonzero | Mode 0x81; words 0/0/5; reload from signed speed | `0xA408`, `ground_right` |
| Left, within limit and nonzero | Same normal presentation assignments | `0xA546`, `ground_left` |
| Normal landing with zero speed | Normal assignments, then mode 0x80, first word 2; facing retained | `0xA1BE` / `0xA246`, `idle_right` / `idle_left`, **immediate continuation** |

Normal landing preserves the first counter. Right reload thresholds are signed
32/64/96, selecting 4/3/2/1; left thresholds are -32/-64/-96 with the corresponding
strict greater-than comparisons. Fast names mean beyond the respective limit;
the future grounded handler behavior has not been inferred from those names.

For zero-speed normal landing, the original branches to `0xA1A4` or `0xA22C`,
initializes idle fields and then falls directly into its idle handler. The
research harness stops **before executing** `0xA1BE` or `0xA246`, retaining the
pending caller return and checking SP=`0xFFFFF000`; ordinary RTS checks
SP=`0xFFFFF004`. No instruction is patched/skipped and no fake RTS is inserted.
Native `AirborneResult::immediate_continuation` expresses exactly this boundary.
Calling `step_airborne` on any grounded/idle identity rejects explicitly.

## Native API and comparison transport

`src/sim/airborne.hpp/.cpp` extends `wiz_sim`; `MotionState` gains a flags word
and explicit logical handler identities. `AirborneParameters`, `AirborneInput`
and `AirborneBudget` expose understood inputs without original RAM or CPU state.
All public motion updates commit state and scratch together only on success.
Default budgets are 1024 horizontal / 4096 downward iterations. Explicit larger
horizontal budgets allow the 8000 edge. Budgets and atomic failure are documented
host policies; original invalid-RAM behavior is not emulated.

`wiznliz-airborne scene-id scene.bin bank-id bank.bin` accepts 21 unsigned fields:
`op x y speed vertical delay flags handler positive_limit negative_limit damping
acceleration contact_damping gravity boost left right gate scratch_x scratch_y
max_calls`. Operations 0–6 select update, horizontal helper, left pixel, right
pixel, landing, right reload and left reload. Initial handler IDs are 1 delayed
or 2 falling. Only update accepts up to sixteen calls; it follows the assigned
airborne handler and stops at any grounded/idle transition. Applied call count
and pending immediate continuation are outputs, so a stopped sequence is visible.
These calls are not game frames.

Outputs compare position, both motion words, delay, handler identity, all changed
presentation fields, scratch, flags, horizontal-step/settle-call/landing counts,
applied calls, immediate continuation, and helper Z-as-contact for operation 1.
No complete register/CCR ABI, frame timing, full idle execution or game reachability
is claimed. Native code consumes extracted resources without a CPU dependency.

## Execution evidence

Pinned Musashi remains revision `313ebf1bd9f4d0d93341eb5ce21fd8a119e9dbdd`, in a
separate restricted Clang ASan/UBSan process. Its `--airborne` mode adds only the
declared code, gate read and flags write to existing permissions. Code/memory
escapes, wrong CPU, D2 corruption, bad stack boundary and excessive instructions
fail. Source/harness/lock/build hashes and exact inputs/outputs are recorded.

| Corpus | Cases per preset | Applied calls | Landings | Immediate idle boundaries |
| --- | --- | --- | --- | --- |
| Flat authored/goldens/word sweeps | 393,924 | 393,925 | 196,706 | 65,585 |
| Authored slopes/empty records/control sequences | 10,240 | 13,976 | 1,643 | 326 |
| Extracted terrain and repeated updates | 11,776 | 15,578 | 331 | 120 |
| Total | **415,940** | **423,479** | **198,680** | **66,031** |

Every delay word and vertical-motion word is exercised, plus all speed words
for both landing directions and both reload helpers. This is not an exhaustive
Cartesian state/input test. Thirty-six hand-worked goldens exercise all 172 new
instructions; the full corpus visits 246 addresses including previous helpers.
The three simulation corpora together visit 332 addresses, including the two
initializer fragments. All 21 outputs agree in debug/release/Clang ASan+UBSan;
all native output hashes match across presets, including release from `/tmp`.

111 Python tests pass with zero skips; all 12 CTest targets pass per preset.
The extended reference retains 282,233 movement and 614,436 terrain regression
passes with sanitized native builds. Out-of-map inputs reject in both processes.
One initial two-call hand expectation omitted the second gravity subtraction
and final y; original and native already agreed. Arithmetic review corrected
that expectation to y109 and vertical -8, without changing implementation.
The initial failed calculation is retained in local research logs.

Reproduce with existing local tools/resources:

```sh
python3 tools/build_terrain_reference.py
python3 tools/project.py build --preset debug
python3 tools/project.py test --rom --preset debug
python3 tools/project.py airborne-probe --disassemble
python3 tools/project.py airborne-compare --rom --preset debug
```

Repeat native build/test/comparison for release and sanitize. `--rom` adds
cataloged terrain; every comparison needs exact original routine ROM. Reports,
hashes and command/status logs: `local/logs/airborne-update/commands.json`,
`reproduction.json`, and [[05_Validation/RESULTS]]. Next:
[[07_Tasks/TASK-0010-grounded-controller]]. Native playability remains none.
