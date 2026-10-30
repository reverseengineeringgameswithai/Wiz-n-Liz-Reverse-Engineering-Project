---
id: FIND-0029
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Retained P1 and ordered mixed allocation

Task: [[07_Tasks/TASK-0010-grounded-controller]]. Original ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Exact audit ranges: `re/mixed_session.json`; validation/provenance:
`re/mixed_session_validation.json`. Native implementation: `src/sim/mixed_pool.*`.

## What is now native

`MixedSessionState` retains P1 actor/control/tracking/scratch, invocation ordinal,
the trail emitter and RNG, both particle types, ordered logical slots and the
complete free stack. One initial seed is followed only by physical held-button
masks. The trail emitter now obtains owner position from native P1 and capacity
from the native pool; neither is fed anew from reference snapshots. The existing
banner and input phases precede P1, then the object loop walks forward once.

The bounded actor wrapper only creates reversal objects; it does not read or
update an existing effect. The session stages these requests with the current
shared free count, then assigns shared slot/generation identities in request
order before any world object runs. This preserves the recorded spawn position
before later actor movement, the allocator's capacity boundary, and the original
post-wrapper world ordering. Shared free order is not replaced with the staging
store's order. Returned actor spawn IDs are the shared IDs.

`MixedPool` seeds explicit occupied objects and a bottom-to-top free stack.
Allocation pops its last slot; release pushes the slot and retains final inactive
object state. Reuse increments a generation; stale identities reject. Slot
storage is host-sized with a 4,096-slot safety bound. The reference's 68 slots
are fixture input, not a hardcoded native capacity or enhanced-capacity claim.

The loop's iterator never rewinds. A newly allocated later slot executes in the
same pass; an earlier slot waits for the next pass. An earlier live particle can
release before the emitter, then be reallocated by the emitter that same pass.
The released reversal object still follows its owner and executes its fixed
return-only handler/service before the next slot. Reference order is established
at exact entry/return/stack boundaries, not inferred from a general call tree.

All state, requests, allocation IDs and RNG updates commit together only after
the invocation succeeds. Failures after banner/P1 movement, staged allocation,
earlier release, emitter allocation or RNG consumption roll back the entire
session. Unsupported ownership/callback/service/action contexts, duplicate/free
occupancy seeds and exhausted work/capacity fail explicitly. A mixed session
cannot also carry the older dedicated P1 effect pool.

## Initial live state and actual movie evidence

The ordinary unchanged user movie at frame boundary 1066 has 68 slots at
`FFFF1B50 + index*78`, ending before FFFF3008. Fifty are free, four are already
live trail particles, one is emitter FFFF2B76, and thirteen are external
reservations. Two of those reservations are inactive but absent from the free
stack; preserving that distinction is necessary.

The window `[1066,1100)` observes one P1 reversal allocation at 1067 (slot 55,
FFFF2C12) and eight emitter allocations. All nine releases belong to these
managed particle kinds; four releases finish particles alive at the initial
boundary. There is no allocation by another client, fixed allocator F9E2 call,
foreign RNG consumer, or reservation occupancy change in this window.

Fresh comparison results per native preset:

| Compared behavior | Count |
| --- | --- |
| Retained P1 invocations and banners | 34 each |
| Ordered sound requests | 2 |
| Retained emitter invocations / RNG calls | 34 / 16 |
| Trail-particle updates, including initial live particles | 136 |
| Reversal updates, including release follow | 12 |
| Shared allocations / releases | 9 / 9 |
| Ordered native spawn/update/release events | 191 |

The eight new trail lifetimes still contribute 97 updates; the initial four
particles contribute the remaining 39. Six newborn trail particles wait until
the next frame and two run immediately in later slots. The full free stack is
checked at every selected original checkpoint and every native invocation, not
just its length. All native object event states and generations match.

The final original capture is `local/generated/mixed-session/run-vt8017re/`,
with an independent unhooked replay agreeing on exposed endpoint state. Every
native preset revalidates that capture and runs its current native build. These
are three native comparisons of one final original capture, not three new
original runs. A preceding discovery capture is separate. Canonical hashes cover
declared exposed state, not every hidden CPU/device bit.

The capture validates 9,767 managed routine events and 52,895 native events with
no drops/overflow. There are 102 control conversions, 136 input polls and 34
inactive timer calls; those quantities are distinct from actor invocations.
214 scratch writes retain the banner-before-P1 contract. All 1,205 managed-slot,
906 reserved-slot and 27 free-stack writes have explicit source/field guards.

## Explicit external reservations

The thirteen `ExternalReservation` objects represent only occupied slots whose
omitted private execution is audited not to interfere with the retained native
scope. They are **not** native implementations of those objects. Unknown original
selectors, changed occupancy, allocator callers or writes reject evidence.
The scoped worker never edits or freezes these original objects.

| Observed selector | Exact static audit | Measured omitted work |
| --- | --- | --- |
| 7808 | `[7808,783A)`, 12 instructions | Linked control, FF31B0 gate; private Y/countdown. This window follows the gate-zero path, writing Y=0106 and counter=8 |
| 7CA4 | `[7CA4,7CC8)`, eight instructions | FF31A6/31A4 may replace private flags/X/Y; observed calls return without those writes |
| 7A88 | `[7A88,7AD6)`, nineteen instructions; 48-byte table `[7A58,7A88)` | FF31BC loop count, private toggle/table cursor/Y/X/reversal countdown; no allocator call |
| 12646 | Previously verified RTS | Private F76C animation or no work; return-only service |
| +46 service 78EE | `[78EE,7910)`, nine instructions; helper `[AC5E,AC9C)`, nineteen | Register-only wrapped overlap query against P1 tracking. All 34 calls return through 790E; hit path 7910 rejects |

7808 and 7CA4 each run twice per invocation; 7A88 and 78EE run once. The capture
checks exact caller/return stack and rejects 79B6 callback execution. Rendering
B126 only clears an already-zero private +14 word. No reservation writes P1,
managed objects, free stack or RNG in this interval. Private motion/presentation
state is intentionally excluded from the native comparison; reservations cannot
be assumed safe in another interval without a fresh audit.

The five new static ranges classify **260 code bytes / 67 instructions** plus
48 table bytes. Their hashes, graph with explicit unsupported exit 7910, primary
decode and five compatible GNU checks pass. They add **308 classified bytes**,
not native function mappings or restricted-original executed coverage. Totals:
26,205 classified / 1,022,371 unclassified ROM bytes; native mappings stay
102 bounded plus one partial / 112 indexed. Historical restricted union remains
1,467; ten freshly run corpora cover 1,118. Existing loop ranges are not counted
again.

## Validation and next boundary

Authored tests cover both reversal facings, initial live particles, nontrivial
free order, earlier/later births, same-pass release/reuse, stale generations,
word wrapping, retained sequences and failures after partially completed work.
Debug/release/sanitize each pass **190 Python tests, zero skips; 38/38 CTests**.
Existing trail (209,082) and reversal (203,586) comparisons pass in every preset;
eight additional sanitized corpora and the old 390-call P1 fixture in all presets
pass freshly. No native/reference mismatch occurred.

Next replace the audited private-object reservations with typed native updates,
beginning **7808 and 7CA4**, then 7A88's table motion. Pin shared FF31xx inputs and
presentation before integrating them; 78EE's collision-hit path remains a
separate unsupported boundary. Initializer 6D22, alternate RNG E948, broad world
scheduling, rendering/audio and boot remain open. TASK-0010 stays in progress;
**native playability remains none**.

Update (session 049): `step_mixed_session` now runs its object loop through
`step_world_phase` and can carry the level world (`MixedSessionState::world`);
[[03_Reverse_Engineering/findings/FIND-0046-world-session]] runs it from 669 with
the world established by the level setup. The `[1066,1100)` comparison above is
unchanged (same output digest).
