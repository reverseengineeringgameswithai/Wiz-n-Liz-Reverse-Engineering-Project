---
id: FIND-0024
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Secondary tally and packed-decimal score thresholds

5132's previously unsupported secondary tally now executes natively with explicit
score context. This extends [[03_Reverse_Engineering/findings/FIND-0023-exit-tally]].
The scope is valid packed-decimal addition operands, request effects and bounded
threshold loops. Unknown decimal encodings remain explicit failures; audio
playback and world scheduling remain outside the contract.
[[07_Tasks/TASK-0010-grounded-controller]] is still in progress and native
playability remains none.

## Instruction and dataflow evidence

Pinned ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
`re/score_step.json` records 280 new disjoint bytes / 71 instructions plus the
previously classified four-byte transfer at 5166, now successfully compared.
All 72 scoped instructions execute in the comparison corpus.

| Original interval | Instructions | Contract |
| --- | --- | --- |
| `[5166,516A)` | 1 | Existing 5132 tail branch to secondary tally, now consumed |
| `[53F2,5458)` | 20 | Start/countdown gate, decrement secondary count, add score, request sound, countdown=3, return |
| `[ADF4,AE1A)` | 13 | Four least-significant-first packed-decimal byte additions into score; X initially cleared |
| `[AE1A,AE4C)` | 14 | Add score; strict unsigned threshold comparison; one reward then repeated threshold advance |
| `[AE4C,AE72)` | 13 | Four packed-decimal byte additions into threshold; X initially cleared |
| `[AF28,AF5C)` | 11 | Sample request, equality-only reward counter limit, wrapped increment, return |

| Logical state | P1 original address | Scope |
| --- | --- | --- |
| score | control +6E / FF06FE, long | Eight packed decimal digits; 53F2 adds 00010000 (decimal 10,000) |
| threshold | control +72 / FF0702, long | Strict comparison: equality does not request a reward |
| threshold increment | control +32 / FF06C2, long | Addition operand on each loop iteration |
| reward counter | control +76 / FF0706, word | Exactly 9 stays 9; every other word increments with wrap |
| arithmetic scratch | FF443E, long | Retains the last addition operand; separate from terrain scratch at FF4442 |
| secondary remaining | control +7E / FF070E, word | Decremented only when the secondary countdown consumes a unit |

53F2 is reached only after primary remaining=0, shared FF0EFE nonzero and
secondary remaining nonzero. When skip=0 and Start is pressed it sets skip=FFFF
and consumes immediately. Otherwise a nonnegative signed countdown decrements
and returns; a negative countdown consumes. After decrement it calls AE1A with
00010000, then emits the existing sound tuple `(140,6,192,1)`, sets countdown=3,
and returns directly to the wrapper. **The last secondary unit does not start a
transition in that invocation.** The next call re-evaluates the empty count.

AE1A adds first and compares the resulting long against threshold. On strictly
greater, it calls AF28 **once**, then repeatedly adds the increment to threshold
until threshold is at least the score. The back-edge at AE48 targets AE36,
**after AF28**. Crossing several thresholds does not award several times.
This refines the earlier static lead into an executed ordering contract.

AF28 requests resource F25EA, count 230, parameter 20E4 through ED6E6. The
research adapter observes mailbox `(230,20E4,A5EA,30)` and maps a logical
`ActionSample::score_reward`. It increments the associated word unless it equals
9; values above 9 are not clamped and FFFF wraps to zero. Sample playback,
audible meaning and a broader gameplay name for that counter are unverified.
The write of 1 below the current stack pointer at AF54 is dead stack scratch,
not a persistent native gameplay field. Full CPU flags/register ABI is not a
native contract; undefined ABCD flags are not claimed.

## Boundaries and native model

For selected-handler stack S, the 5132-to-53F2 tail keeps S/F906. AE1A runs at
S-4/5428, pushes D2 and calls ADF4 at S-12/AE20. AF28 runs at S-12/AE36; its
saved D0–D3 and sample call place ED6E6 at S-32/AF44. AE4C runs at S-12/AE40.
AE1A restores D2 and returns through S-4/5428; the tally sound call runs at
S-4/544E. 5418 or 5456 returns through S/F906. Selected traces assert exact
positions and reject overflow instead of relying on inferred call trees.

`ScoreState` stores packed values, persistent arithmetic scratch and the reward
word. Decimal addition wraps after eight digits. Native digit arithmetic is
ordinary bounded C++ arithmetic, not a CPU interpreter. Invalid digits reject
only when used as addition operands; unused increment/threshold bits are not
silently normalized. The reference transport has the same explicit domain guard
before ADF4/AE4C: malformed-input rejection is a **research scope guard**, not a
claim that the original game detects invalid digits. Normal positive comparisons
execute original unpatched 68000 instructions in pinned Musashi.

`add_score` has a 4,096-advance default work budget, propagated through actor
presentation/dispatch. Zero increment and cyclic/wrapping thresholds cannot
hang native execution. Missing score context, invalid consumed digits, budget
exhaustion or later unsupported services roll back all motion, terrain scratch,
score, tally, tracking and requests. The eight-digit output wrap is retained;
there is no imposed score saturation.

Research `--score` / `--score-sequence` extend the old exit-tally row to 77 fields
within its 512-byte bound. The sequence retains/asserts score, threshold,
increment, rewards, arithmetic scratch and secondary count, as well as prior
actor/service/tracking/tally/marker state. Shared gates, equality keys, controls,
transition context and terrain scratch remain explicit world inputs. Existing
trace defaults stay strict; only this score contract permits the two score bytes
that overlap the legacy control snapshot and the deeper reward sample call.

## Validation

**328,916 original/native comparisons per debug/release/sanitize preset** pass,
with identical outputs, 20 authored goldens and all 72 scoped instructions.
Count: 313,556 flat/state, 4,608 authored-terrain and 10,752 cataloged-terrain.
Independent sweeps cover every countdown, secondary-count and reward word,
valid score encodings, equality/adjacent thresholds, gates, facings, repeated
calls and terrain. Separate sweeps are not a full Cartesian proof. ADF4's direct
original contract here uses the tally's fixed amount 00010000; the native helper's
other amounts have authored arithmetic tests, not new original entry captures.

Five malformed/nonterminating cases reject without a row in both transports:
invalid consumed score, threshold and increment; zero increment; and a repeating
threshold cycle. Native unit tests additionally verify the exact work limit,
late-service rollback, primary-before-secondary ordering, last-unit return and
next-call transition. **174 Python tests, zero skips; 32/32 CTest targets in every
preset** pass. Trace tests reject missing/nested returns, unintended writes,
wrong sample ABI, truncated snapshots and overflow.

Four **controlled RAM/input experiments**, branched at recorded boundary 4934,
compare eleven complete P1 wrappers: eight calls cross several thresholds and
consume two units; one call hits equality; one wraps the score; one wraps the
reward counter. Totals: five tally sound requests, three sample requests and six
threshold advances. The eight-call branch makes two reward requests, with four
then one threshold advances; its second award sees counter=9 and leaves it there.
Exact edits and neutral input rows are pinned. Native mutable score/count/scratch
persist across calls. Four fresh independent unhooked workers repeat identical
edits/input and match declared covered-state endpoints. These are not ordinary
secondary-score hits or full-frame native comparisons.

Static byte/transfer/closed-graph checks and four new GNU checks pass, including
ABCD and both strict BHI branches. Earlier decoder limitations remain historical;
no external runtime was rebuilt. Evidence: `re/score_validation.json` and
[[08_Sessions/2026-10-05-024-secondary-score]].

## Remaining scope and direction

The bounded 5132 mapping is promoted; five new helper mappings bring totals to
**97 bounded simulation mappings plus one partial / 107 indexed functions**.
Classified ROM bytes: **24,575 / 1,048,576**. 4770's alternate mode remains partial.
No claim covers invalid decimal arithmetic, hidden CPU/device state, arbitrary
score callers, palette/table consumers, world/P2 scheduling or audio playback.

Next: implement a bounded native P1 session with measured physical-input
conversion and invocation order, replacing per-call control feeds in an existing
movement/jump replay window. Account for shared-state writers and frame cadence
before integrating timers/effects. This is the agreed shift toward a playable
slice after closing the explicit score dependency. See [[01_Project/NEXT_ACTIONS]].
