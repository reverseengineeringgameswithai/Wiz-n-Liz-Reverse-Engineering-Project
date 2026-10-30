---
id: FIND-0011
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0008
---
# Original horizontal movement and airborne transition

Task: [[07_Tasks/TASK-0008-movement-step]]. Eight additional routine mappings
now execute independently and match native C++ state transitions. Paired actor
and control slots are statically identified; physical input identity, frame
scheduling and the next airborne handler remain outside this result.

## Identity and exact scope

ROM-LOCAL-0001 remains 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
No original bytes changed. Ranges below are half-open direct ROM/file offsets;
`re/movement_step.json` pins every range digest, instruction count and transfer.

| Function / range | Behavior | New executed instructions |
| --- | --- | --- |
| FUNC-0016 `[0x9A5E,0x9A6C)` | Counted damping | 4 |
| FUNC-0017 `[0x9A6C,0x9A80)` | One unit toward zero | 7 |
| FUNC-0018 `[0x9AAE,0x9AC8)` and `[0x9AF8,0x9B04)` | Horizontal dispatcher, including zero-speed settling | 13 |
| FUNC-0019 `[0x9AC8,0x9AF8)` | One left pixel and terrain response | 15 |
| FUNC-0020 `[0x9B04,0x9B34)` | One right pixel and terrain response | 15 |
| FUNC-0021 `[0xAA50,0xAA88)` | Airborne state assignment | 10 |
| FUNC-0022 `[0xACD6,0xACE8)` | Signed positive limit | 5 |
| FUNC-0023 `[0xACE8,0xACFA)` | Signed negative limit | 5 |

These are 260 new disjoint bytes / 74 instructions. The dispatcher has two
fragments separated by the left-step routine; its CSV contiguous full end stays
empty. The metadata records both fragments without double-counting the child.
Including the previous six terrain routines, the closed executable graph has
160 instructions. Closure validates every successor's instruction boundary;
it is not a full stack-sensitive control-flow proof.

Six static-only context fragments add 390 bytes / 84 instructions:
`[0xF940,0xF96A)`, `[0x9880,0x98DE)`, `[0x98DE,0x98E6)`,
`[0x9952,0x99D4)`, `[0xA1BE,0xA1FA)`, `[0xA246,0xA27E)`.
They establish bindings, initializer values and callers, not executed function
coverage or complete handler boundaries. The probe verifies 55 transfers and
ten selected short GNU corroborations, including NEG.W, ASR.W, DBF and CMP.W.

## Ownership and state

The binding fragment at `0xF940` explicitly pairs A5=`0xFFFF0690` with
A6=`0xFFFF1AB4`, and A5=`0xFFFF0838` with A6=`0xFFFF1B02`, storing each actor
pointer at control+0. Actor stride is 0x4E. Initializer `0x9952` loads A6 from
control+0 and stores the A5 backlink at actor+0x4A. It clears actor+0x12/+0x22.
This confirms two associated control/actor records, not which physical pad or
named player owns either one. Native code uses semantic state, not RAM pointers.

| Owner + offset / width | Verified role |
| --- | --- |
| actor+2/+4, words | x/y position, word wrapping |
| actor+0x22, word | signed horizontal speed |
| actor+0x26, word | vertical motion value, cleared by transition |
| actor+0x2A, word | airborne delay, assigned FFFF |
| actor+0x16, long | next update handler, assigned `0xAAEA` |
| actor+0, byte | mode, assigned 81 |
| actor+6/+8/+A, words | presentation values assigned 3A/3C/3D; rendering consumer untraced |
| actor+C/+D, bytes | paired counters, assigned 6/6 |
| control+0x5A/+0x5C, words | signed positive/negative limits, initialized to 192/-192 |
| control+0x66, word | damping count minus one, initialized to 3 |

The initializer reduces limits to 96/-96 when control+0x30 is nonzero.
Right/left idle caller fragments both call damping before horizontal movement
on the reviewed paths; they also reference control fields and further handlers
outside this pass. They do not establish the complete input or frame schedule.

## Ordering and arithmetic

1. Damping once changes nonzero signed speed by one toward zero. The driver uses
   DBF with control+0x66, hence count+1 calls, including 65,536 for FFFF. Native
   damping computes the equivalent result directly; it does not interpret CPU
   instructions or iterate after reaching zero.
2. Horizontal dispatch reads the initial speed once. Zero tail-calls verified
   one-pixel settling. Nonzero selects a direction once, negates negative speed
   as a word, shifts arithmetically by five, and executes the body before DBF.
   Ordinarily this is `floor(abs(speed)/32)+1` steps. The word `0x8000` remains
   negative after NEG.W, shifts to `0xFC00`, and executes **64,513** steps.
3. A single step first changes x by +/-1, then checks the foot probe at
   position+(12,23). Equality ends the step. Otherwise it checks upper contact
   at +(12,22); equality decrements y and ends the step. Otherwise y increments
   and the foot probe runs again. Equality ends the step.
4. A final mismatch adds +/-4 to the speed word, applies the direction's signed
   limit, and tail-calls `0xAA50`. Overflow happens before the signed clamp;
   even unusual wrapped speed inputs retain that behavior.
5. `0xAA50` makes all assignments in the table above and returns to the original
   caller. **The outer DBF loop continues after speed and handler changes.**
   It does not recalculate direction/count or stop at the first transition.

The native `MotionUpdate::airborne` value represents the assigned next handler.
It does not execute or silently replace `0xAAEA`. Presentation fields retain
neutral names until their rendering consumers are established. Terrain scratch
remains explicit and follows the verified call order, including sentinel paths.

## Native implementation and host limits

`src/sim/movement.hpp/.cpp` extends `wiz_sim` with motion state/parameters,
damping, clamps, left/right steps and horizontal dispatch. All word operations
avoid signed C++ overflow. State and terrain scratch update transactionally:
unsupported map access or a rejected work budget leaves both unchanged.
That rollback is a host API policy, not original malformed-RAM behavior.

The default horizontal budget is 1024, sufficient for every speed except 8000.
That exceptional original behavior requires an explicit larger budget; the
comparison transport uses 65,536 and verifies the full 64,513-step execution.
No dummy side effects, CPU runtime, raw ROM input or external handler execution
are hidden inside this component.

`wiznliz-movement scene-id scene.bin bank-id bank.bin` accepts ten unsigned fields
per line: `op x y speed positive_limit negative_limit damping_count_minus_one
scratch_x scratch_y repeats`. Operations 0–7 are dispatcher, left, right,
damping driver, damping once, positive clamp, negative clamp and transition.
Repeats 1–16 invoke the same selected entry on retained state; they are not frames.
Outputs are sixteen fields: position, speed, vertical motion, delay, logical
handler, mode, three presentation words, two counters, two scratch words, step
count and transition count. Other actor fields are outside the native contract.

## Independent execution and results

The separate restricted harness `re/reference_scripts/terrain_reference.c`
gains `--movement`; pinned Musashi revision remains
`313ebf1bd9f4d0d93341eb5ce21fd8a119e9dbdd`. Sources, harness, lock, builder and
executable hashes are verified. No new external source was downloaded this pass.
The reference executes actual 68000 instructions with actor at effective
`0xFFFF1AB4`, control at `0xFFFF0690`, explicit fixture map/records/scratch/stack
and exact permitted writes. It rejects code/read/write escapes and unbalanced
return stack, verifies D2 preservation, and limits each call to 16 million
instructions. Both the reference and sanitizer native build use Clang ASan/UBSan.

| Corpus | Cases per preset | Executed horizontal steps | Airborne entries |
| --- | --- | --- | --- |
| Flat authored fixture, arithmetic sweep and 26 hand-worked goldens | 262,265 | 65,582 | 6 |
| Authored slopes, empty records, flags and seeded sequences | 8,192 | 30,016 | 17,460 |
| Cataloged terrain positions and repeated calls | 11,776 | 36,035 | 30,553 |
| Total | **282,233** | **131,633** | **48,019** |

All sixteen output fields agree in debug, release and sanitizer presets.
Native output hashes are identical across presets; release is invoked from
`/tmp`. All 74 new instructions are visited (149 overall in this corpus; the
lower contact probe's 11 instructions belong to the previous terrain corpus).
Every signed speed word is compared for both damping entries and both clamps.
Horizontal movement itself is not exhaustive over all state/speed combinations.
Both processes explicitly reject an out-of-map movement input without output.

106 Python tests pass with no skips. All 10 CTest targets pass in each preset,
including authored motion goldens, full signed speed sweeps, 8000 budgeting,
post-first-step transactional rollback and malformed transports/resources.
The modified reference also passes all **614,436** prior terrain cases with the
sanitized native build. Metadata passes the split dry-run. No full game or
register/CCR ABI, cycle, device, frame or input equivalence is claimed.

Reproduce with existing local tools and extracted resources:

```sh
python3 tools/build_terrain_reference.py
python3 tools/project.py build --preset debug
python3 tools/project.py test --rom --preset debug
python3 tools/project.py movement-probe --disassemble
python3 tools/project.py movement-compare --rom --preset debug
python3 tools/project.py terrain-compare --rom --preset sanitize
```

Repeat build/test/movement comparison for release and sanitize. `--rom` adds
cataloged terrain; routine ROM is required for every original comparison.
Exact commands, durations and cross-preset hashes:
`local/logs/movement-step/commands.json` and `reproduction.json`. Report locations
and limitations: [[05_Validation/RESULTS]]. Next:
[[07_Tasks/TASK-0009-airborne-update]]. Native playability remains none.
