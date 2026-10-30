---
id: FIND-0025
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Physical input conversion and a retained P1 session

A native session now runs the unchanged movie's `[3100,3200)` movement/jump
window from one initial actor/control/terrain seed. Each subsequent row contains
only physical held buttons. All 100 actor-wrapper outputs and four ordered sound
requests match original execution in debug, release and sanitize. This removes
per-call state/environment feeds for this specific window; it does not establish
a general world scheduler or native playability.

## Static conversion contract

ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
`re/input_conversion.json` pins `[14E4E,14F24)`: **214 bytes, 54 instructions**,
closed internal branches, no calls and one RTS at 14F22. A5 names the control
record. The only consumed input is its combined active-low byte at +14.

| Input bits, low to high | Produced control bytes |
| --- | --- |
| Up, Down, Left, Right | +1A, +1B, +1C, +1D; opposing axes both clear |
| B, C, A, Start | +1F, +20, +1E, +21 |
| A OR B OR C | +15 |
| B OR C | +16 |
| A | +17 |

Produced fields are FF/00. The routine clears +1A..+21 before populating them,
then writes +15..+17. +14, +18/+19 and other control bytes remain unchanged.
There is no previous-button input or edge detection. D0/CCR are scratch;
D1..A6 and the caller's return are preserved. Native logical buttons deliberately
have a separate representation from the combined device byte.

14DA2 performs physical device reads and invokes this conversion for P1/P2.
The observed ordinary USA three-button configuration maps P1 to FF0690 and
P2 to FF0838. Native code replaces the held-button-to-byte mapping, not the
hardware I/O transaction. Alternative remapper 14E3C remains outside scope.
Static callers at 312E/3134 and 7C4/7D4 explain two hardware-read pairs plus two
extra P1 conversions in this movie window. The later P1 conversion returns to
7DA, before 5716, 57E6 and the wrapper call at 7E6. Those intervening helpers
are not reconstructed by this pass; measured inputs remain unchanged.

## Measured invocation order and writers

Owned independent workers replay the unchanged BK2-derived recording. Per row:

1. One inactive transition-timer invocation: 1345A -> 134B0 -> actual return EBF2.
2. Conversion pairs with `(A5, pending return)`: P1/14DEE, P2/14E38, P1/313A,
   P1/14DEE, P2/14E38, P1/7DA.
3. One full P1 wrapper F8F6 through presentation/selected handler/service/tracking
   and actual return 7EC. Pending returns and stack depths are checked explicitly.

Totals are **100 video frames, 600 producer invocations, 800 input polls,
100 P1 wrappers and 100 inactive timer calls**. These differ from the earlier
1983–2119 route's 408/544/136 counts; they are scoped observations, not a global
cadence claim. Repeated P1 conversions are stateless with the same held input;
the native session produces the final control record once before its wrapper.
It neither simulates P2 nor pretends to execute the other world calls.

Managed selected-instruction events are paired with a native write/poll trace
drained every frame. **108,064 native events** fit their per-frame capacities;
no dropped event or hook error is accepted. All **892 scratch writes** target
FF4442/4444 from the P1 terrain query. The managed 99DE/99E4/99EA snapshots
corroborate their values and position inside the wrapper. Native access-event PC
is the CPU's PC during the write callback (99E4/99EA here), not an instruction
entry; it is not mislabeled as the writer instruction itself.

The write trace rejects writes to pinned movement parameters, gate, action
globals, mailbox, tracking selector, inactive transition context, terrain map,
collision records and terrain addressing fields. Actor/tracking continuity is
checked across wrappers; terrain scratch persists and is compared after each
wrapper. Terrain endpoints also match. Other world memory remains outside the
native contract. Separate unhooked replay agrees on the declared covered-state
endpoint in every preset; this is not proof of every hidden device bit.

## Native ownership and limits

`src/sim/input.*` implements `convert_pad_byte`, `produce_pad_control` and the
actor-input adapter. `src/sim/session.*` owns actor, control, terrain scratch,
tracking and invocation ordinal. `P1SessionConfig` supplies a fixed parameter
set and gate, with explicit invocation and actor-work budgets. Conversion,
presentation, selected handler, service and tracking commit together. Late
failure leaves every session field unchanged.

`wiznliz-session` reads extracted scene/bank resources and one 32-field seed,
then one logical held-button mask per invocation. It cannot reseed later rows.
The CLI caps a session at 600 invocations. Pause and nonzero up/down actions
reject because their world scheduling is not integrated. Allocation/effect,
transition and tally paths require contexts that this session intentionally does
not supply; existing handler guards reject them. Their isolated native components
remain implemented. No CPU interpreter or raw-ROM execution enters native targets.

## Validation and uncertainty

- **1,024 original/native conversion cases per preset**: every raw byte with
  four starting fills (00/55/AA/FF), distinct initial CCRs, preserved bytes and
  registers checked. All 54 scoped instructions execute.
- Authored tests cover both facings, idle-to-ground, jump press/hold/release,
  reversal, same-call landing and presentation callback, word-wrapped tracking,
  late rollback, unsupported inputs/effects and invocation/work-budget failures.
- **100 one-seed movie wrappers per preset**, identical native output hashes;
  four requests per window, no per-call environment feeds. Three independently
  repeated unhooked endpoints agree. No controlled RAM experiment is needed.
- Six fresh sanitized regression corpora and full three-preset suites pass;
  exact counts and report hashes: `re/session_validation.json`.
- Static decoder `rasm2 5.9.8` (linux-x86-64): primary/closed graph and three
  GNU checks pass. GNU's plugin
  rejects immediate memory BTST at 14E58 and ignores CPU-model selection.
  The initial attempted fourth GNU check failed honestly; its output/limitation
  is recorded. Primary decoding plus pinned original-68000 execution covers it.

Next: extend the retained session into the earlier `[700,1067)` window by
identifying and reconstructing the intervening terrain-scratch writers and their
invocation order. Discovery found 364 changes between its 367 actor calls,
whereas this pass's chosen window has none. Do not restore per-call scratch
feeds or count an unobserved no-op as a reconstructed world update.
See [[08_Sessions/2026-10-05-025-p1-session]],
[[04_Native_Implementation/PORTING_MAP]], [[05_Validation/RESULTS]] and
[[07_Tasks/TASK-0010-grounded-controller]]. Native playability remains none.
