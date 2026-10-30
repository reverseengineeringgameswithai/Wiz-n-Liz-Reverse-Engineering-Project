---
id: FIND-0030
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Native rising and gated visibility objects

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Exact ranges/hashes: `re/private_step.json`; evidence: `re/private_validation.json`.
Implementation: `src/sim/private_object.*`, integrated in `src/sim/mixed_pool.*`.

## Instruction-derived behavior

| Handler | Range | Exact effects |
| --- | --- | --- |
| FUNC-0113, rising | `[7808,783A)`, 50 bytes / 12 instructions | Load +4A into A5 without dereferencing it. Test the full FF31B0 longword. Zero writes Y=0106 and countdown +10=8. Nonzero preserves both at Y=00F6; otherwise decrement countdown, and only if its wrapped result is negative decrement Y and reload 8 |
| FUNC-0114, gated visibility | `[7CA4,7CC8)`, 36 bytes / eight instructions | FF31A6 word nonzero overwrites flags +12 with 2000. Then FF31A4 word nonzero overwrites X/Y with FF80. Zero gates preserve existing values; they do not restore earlier values |

The stop height is equality-only, not a clamp. Countdown 8000 decrements to
7FFF without moving; 8001 decrements to 8000 and moves. Countdown zero moves
immediately; Y zero wraps to FFFF. From Y=0106/countdown=8 with a nonzero gate,
144 calls reach 00F6 and subsequent handler calls preserve Y/countdown. A gate
with only its upper word set is nonzero. Visibility flags are replaced, not ORed.

`PrivateObject` has a typed `PrivateUpdate` selector and preserves position,
flags, presentation, target, countdown and logical control identity. The +4A
load does not justify resolving or requiring a live owner. Native code retains
that logical ID without original RAM addresses. Unknown invoked handlers reject.

The scheduled API tests activity once, advances F76C presentation, executes the
selected private handler, and includes the fixed return-only 12646 service.
Any invoked presentation callback rejects transactionally; prior presentation
changes are not published. Inactive objects skip this phase. Initializers,
other callbacks/services and producers of the three shared gates are excluded.

## Retained mixed session

The mixed pool now stores this typed object as transport kind 5, with a logical
subselector for the two handlers. The existing slot, generation, work-budget and
whole-session rollback rules apply. Missing shared globals reject when a private
object is invoked. A seven-field pool header seeds slot/free counts, RNG state/
mirror and the three gates; the older four-field header remains usable for
sessions without private objects. All later session rows remain physical held
masks only. No private state or gate is fed anew per invocation.

Ordinary movie `[1066,1100)` has two rising objects (slots 64/65) and two gated
visibility objects (56/57). These four are promoted from reservations to native
objects. Nine explicit reservations remain, including two inactive occupied
slots. 7A88 table motion, callback 79B6 and collision service 78EE's hit path are
not implemented. Selector, occupancy, allocator and write guards still reject
unmodeled behavior; original omitted objects continue executing normally.

All three FF31xx inputs are zero throughout this window. Exact snapshots at every
selected checkpoint, complete per-frame write traces and final RAM equality
establish that no producer writes them here, including transient writes. This
permits one seed for this interval; it does not reconstruct their producers or
justify freezing them elsewhere. Nonzero paths have restricted-original evidence,
not ordinary gameplay evidence or an edited full-machine capture in this pass.

The capture verifies presentation, handler entry/return and service order with
explicit A6, stack and caller checks, plus retained-state continuity. Native
comparison now includes all 136 private updates (68 per handler), in addition to
34 P1/emitter calls, 136 trail updates and twelve reversal updates. All nine
allocations/releases, full free-stack order and **327 ordered pool events** match
in each preset. There are 34 banner requests and two sound requests.

Fresh original capture: `local/generated/mixed-session/run-rg1kl63c/`. An
independent unhooked replay agrees at the declared exposed-state endpoint. Release
and sanitize revalidate this same original capture; they are additional native
comparisons, not additional original runs. No edits, drops or overflow. Cadence:
102 conversions, 136 polls, 34 inactive timers, 214 scratch writes, 9,767 managed
routine events and 52,895 native events. Audited writes: 1,621 managed objects,
490 reserved objects, 27 free-stack, zero private-gate writes.

## Validation and limitations

**277,232 original/native cases per preset** cover every countdown word, both
word gates, longword gate boundaries, equality stop, signed/wrapped arithmetic,
all presentation modes, inactive work, repeated lifetimes and callback rejection.
Both new handler ranges execute completely: twenty instructions. The full closed
comparison graph has 87 instructions, including existing phase/presentation/RTS.
Primary decoding and range hashes pass; four selected GNU checks corroborate.
GNU cannot decode the immediate MOVE.W instructions at 7CAC/7CBA; primary decode
and original execution cover them. No GNU completeness claim is made.

Authored tests additionally check gate changes across retained calls, flags
replacement, zero-gate preservation, whole-pool rollback after earlier release/
private work, missing globals, callbacks, work budgets and malformed transport/
evidence. **192 Python tests, zero skips; 40/40 CTests per preset** pass.
Trail 209,082 and reversal 203,586 cases pass in each preset; eight additional
sanitized corpora and the older 390-call P1 fixture in every preset pass freshly.

These 86 bytes were already classified by FIND-0029; no bytes are counted twice.
Totals become **104 bounded simulation mappings plus one partial / 114 indexed**,
with 26,205 classified / 1,022,371 unclassified bytes unchanged. Fresh eleven-corpus
executed union is 1,138 instructions; cumulative 1,487 includes older corpora not
rerun here. No full-function denominator or whole-world/frame parity is inferred.

Next reconstruct **7A88's table motion**, including its bounded loop, FF31BC
input/writers and presentation callback boundary. Keep 79B6 and 78EE's collision
hit explicit until separately verified. Boot, general world scheduling, rendering,
audio and initializers remain open. TASK-0010 stays in progress; **native
playability remains none**.
