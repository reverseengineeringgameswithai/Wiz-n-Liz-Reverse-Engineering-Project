---
id: FIND-0023
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Exit tally, deferred transition and conditional completion

The ordinary recorded 5132/5188 path now executes natively through the complete
P1 wrapper return. This extends [[03_Reverse_Engineering/findings/FIND-0022-bonus-slots]]
and reuses the existing tally, coasting and transition helpers.
[[07_Tasks/TASK-0010-grounded-controller]] remains in progress; native playability
remains none. 5132's secondary-score branch at 53F2 still rejects explicitly.

## Exact instruction scope

`re/exit_tally_step.json` pins **150 new disjoint bytes / 32 instructions**:

| Interval | Instructions | Evidence |
| --- | --- | --- |
| `[5132,5166)` | 13 | Native/original compared: coast, remaining-unit call, last-unit delay, secondary gate tests |
| `[5166,516A)` | 1 | Original branch to unsupported 53F2; static and expected rejection boundary, not a successful native path |
| `[516A,5188)` | 6 | Native/original compared: skip/Start decision, deferred handler assignment and immediate transition tail |
| `[5188,51C8)` | 12 | Native/original compared: coast/wait, save coordinates, conditional marker clear and mode=1 |

Thus **146 bytes / 31 instructions** are in successful comparison paths. No
classified or instruction coverage is duplicated for A148, 537C, AF98, 13208,
4F8C or the existing sound-request boundary.

5132 reloads associated control +4A, coasts, then checks control +84. Nonzero
remaining calls 537C with a nested return, preserving the existing signed
countdown, Start bypass, wrapped/capped credit and sound request. If the call
consumes the last unit, 5132 overwrites FF340A with 60 and returns. **It cannot
start the transition in that same invocation**, even when Start/skip is active.
An already-empty invocation first checks FF0EFE and control +7E; both nonzero
select unsupported 53F2. Otherwise skip FF0F0E or Start +21 selects 5188 and
immediately tails through 13208, which initializes the shared transition.
**5188 itself executes on a later invocation.**

5188 coasts and waits while FF0B90 is nonzero. When ready, it saves requested
FF4446/FF4448 into associated +A2/+A4, compares FF33C8 and FF33CC as words,
clears associated +7C only on equality, then sets shared mode FF33E0=1. The
handler remains 5188. Input, remaining units and secondary gate do not gate
this completion. The timer is a separate world invocation, never an actor tick.

| New explicit field | P1 address | Scoped role |
| --- | --- | --- |
| secondary gate | FF0EFE | Enables the unsupported secondary path when count is also nonzero |
| secondary remaining, control +7E | FF070E | Second nonzero gate; untouched by this native scope |
| marker, control +7C | FF070C | Cleared by 5188 only when equality keys match |
| selection / target selection | FF33C8 / FF33CC | Exact equality keys, no broader world meaning claimed |

## Exact return boundaries

For selected-handler stack pointer S, both coast helpers use S-4 and pending
513C or 5192. Unlike 5222's tail into 537C, **5132 calls 537C with S-4 / 5146**.
Its AF98 credit helper and FCB32 request therefore use S-8 with returns 53AE
and 53D4. 53A2/53DC return to 5146, which resumes at S / F906. Last-unit RTS
5156 or the ordinary 4F8C RTS retains F906. 13208 is a tail at S / F906 and its
1324C RTS returns to the wrapper. 5188's 51C6 RTS also retains F906. The full
ordinary wrapper finally returns to 7EC. Selected traces assert these positions
rather than relying on inferred general call trees. Overflow rejects evidence.

## Native representation and limits

`MotionUpdate::exit_tally` and `exit_tally_wait` append stable logical selectors.
Optional `TallyState::exit_state` holds five word fields in `ExitTallyState`.
The verified unit helper is shared with the old tally implementation, preserving
its previous semantics. Main remaining-unit work needs only tally context;
secondary routing needs exit fields; transition start needs transition context.
A busy 5188 wait needs no exit fields, but completion requires them and shared
action globals. Unknown paths, missing contexts, coasting budgets and later
unsupported services reject the entire actor/context transaction.

Research `--exit-tally` and `--exit-tally-sequence` extend the 67-field tally row
with five words (72 fields, 512-byte bound). The sequence retains/asserts
actor/service/tracking, remaining/skip/countdown/credit and marker. Secondary
gates/count and equality keys, controls, transition timer/positions and scratch
remain explicit world feeds. No score arithmetic, implicit palette consumption,
world scheduler or emulator is added to the native runtime.

## Validation and progress assessment

**348,668 original/native cases per debug/release/sanitize preset** pass with
identical outputs, 22 authored goldens and all 31 compared instructions visited.
Groups: 333,308 flat/state, 4,608 authored-terrain and 10,752 cataloged-terrain.
Every countdown, remaining and direction word is swept. Every equality key is
checked equal and unequal; marker boundaries, both facings, activity, gate/input
combinations, repeated invocations and terrain/arithmetic edges are covered.
Separate sweeps are not an exhaustive Cartesian proof. Start-released and
Start-pressed secondary paths reject in both transports at the explicit 53F2
boundary without publishing a row.

The unchanged movie supplies **231 continuous wrappers at [4807,5038)**:
215 in 5132 and 16 in 5188. Two sound requests occur. Last-unit consumption
sets delay=60 at 4933; Start selects 5188/initializes transition at 5021; the
first wait invocation is 5022, and completion is 5037. Mutable native tally and
marker state persist throughout. An independent unhooked worker matches the
declared endpoint. The ordinary route has unequal keys and retains marker=2.

One separate **controlled RAM-edit experiment** at [5037,5038) sets marker to
FFFF and target key to the current selection, preserving the movie input row.
The original and native both clear the marker and complete mode=1. A fresh
unhooked worker repeats identical edits/input and matches the endpoint. All
identities, receipts, original/new bytes and selected artifacts are pinned.
This is not an ordinary equality hit or full-frame native comparison.

**169 Python tests, zero skips; 30/30 CTest targets per preset** pass. Authored
sequences cover last-unit return, deferred wait, separately invoked timer,
equality/inequality, held input, missing contexts and rollback after completion.
Synthetic traces reject missing boundaries, wrong nested stacks, unintended
writes, unsupported secondary execution and overflow. Thirteen prior corpora
pass freshly under sanitizers; fourteen corpora visit **1,206 scoped successful
instruction addresses**, including six reference-only sound guards. The single
rejected transfer at 5166 is not added to that successful instruction total.

Static byte/transfer/closed-graph checks pass. Two new GNU checks pass (BSR/RTS).
The installed GNU plugin rejects JMP abs.l at 5182 and CMP.W abs.l at 51B2;
these limitations are recorded, not called decoder agreement. The main decoder
and original execution cover both. The earlier presentation BCHG limitation
remains. An initial synthetic fixture lacked sentinel tracking coordinates;
correcting the fixture made the final suite pass. No original/native mismatch.

A fresh 5298-row survey observes 4,139 P1 calls/services and **no handler address
outside the registered native selector table**. All services select 12646.
It matches the recording's unhooked final covered-state baseline. This is address
discovery with zero native comparisons, not proof of every branch or full-route
native behavior. The 231-call comparison is the concrete new integration gain.
Next, close the explicit 53F2 score/reward dependency; after that, prioritize
measured scheduling and a native playable slice over unrelated helper coverage.

Pinned evidence: `re/exit_tally_validation.json`. Current totals:
**91 bounded simulation mappings plus two partial mappings / 102 indexed
functions**, **24,295 classified ROM bytes**. Partial mappings are 4770's
nonzero-D2 alternative and 5132's 53F2 branch. Broader world/P2 scheduling,
rendering, audio playback and native playability remain outstanding.
See [[01_Project/NEXT_ACTIONS]].


The explicit 53F2 gap is superseded by
[[03_Reverse_Engineering/findings/FIND-0024-secondary-score]]: valid packed-decimal
secondary tally/reward loops now execute natively. Session 023's scope and results
above remain historical; invalid consumed digit patterns still reject explicitly.
