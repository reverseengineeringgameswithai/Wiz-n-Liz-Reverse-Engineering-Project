---
id: FIND-0032
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Native control overlap and miss-only collision service

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Exact ranges/hashes:
`re/collision_step.json`; validation: `re/collision_validation.json`.
Source: `src/sim/collision_probe.*`, `src/sim/mixed_pool.*`.
Evidence recipes: `tools/collision_compare.py`, `tools/genesis_collision_evidence.py`
and `tools/genesis_mixed_session.py`.

## Instruction-derived behavior

FUNC-0116, AC5E..AC9C, is 62 bytes / nineteen instructions. A6 owns the object;
A5 supplies a control record, not another object. The helper reads object
+02/+04 (position), +1E/+20 (extent operands), control +42/+44 (tracked position),
and the FF13AE word. Flags, activity, object +4A and actor position are not read.

With all additions/subtractions truncated to words:

```text
x_distance = word(object.x + x_extent - control.x) & x_mask
x_limit = word(x_extent + 16)
if x_distance > x_limit: miss

y_distance = word(object.y + y_extent - control.y)
y_limit = word(y_extent + 12)
if y_distance > y_limit: miss
otherwise: overlap
```

Comparisons are unsigned and inclusive; only X is masked. The extent operands
are not normalized geometric half sizes. Threshold overflow is intentional:
FFF0+16 and FFF4+12 become zero; FFEF+16 and FFF3+12 become FFFF. X failure
short-circuits Y. D0's low word is zero on miss, FFFF on overlap, with matching
Z; object and control RAM are unchanged. Native `overlaps_control` returns a
boolean, not a 68000 register/ABI emulation.

FUNC-0117, the partial `[78EE,7910)` service, is 34 bytes / nine instructions.
It selects A5=FFFF0690, calls AC5E and branches to **unsupported hit7910** on
overlap. Only after a primary miss does it test the full FF33E2 word. Zero
returns at 790E; nonzero selects FFFF0838 and repeats the helper. A secondary
hit also reaches 7910; a secondary miss returns. Neither the caller's A5 nor
object +4A chooses the tested controls. The typed object's logical control ID
is preserved but not dereferenced. This is a partial service mapping, never a
claim that hit behavior is reconstructed.

The scheduled scope runs the active gate, F76C presentation, fixed 12646 RTS
handler and then the miss service. Inactive objects skip work. Any invoked
presentation callback rejects before collision work; stored callback zero is
not treated as a callable native handler. Hit, missing consumed P2 input and
callback failures publish no earlier presentation or session changes.

## Inputs and writers

P1 tracking lives at FF06D2/FF06D4, control +42/+44. The existing native wrapper
writes actor X+4 / Y+6 after its service, with word wrap, or FF80/FF80 when its
selector is FFFF. Original writer instructions are F91A/F924; native write
callbacks report next PCs F91E/F928. Sentinel writes are F92A/F930 and remain
covered by the prior dispatch corpus. The collision phase consumes the wrapper's
new tracking values, not actor coordinates or a per-frame reference feed.

Ordinary `[1066,1100)` contains **68 primary tracking writes**, exactly two per
wrapper. Complete write tracing checks addresses, widths, owner/control registers,
order and values, with initial/inter-call/final continuity and service inputs.
FF13AE=03FF, FF33E2=0 and P2 tracking FF087A/FF087C=0 remain fixed with no writes,
including transients. Their initialization and general producers are not native
mappings; P2 scheduling is unsupported. The component can consume explicit P2
tracking for synthetic service checks. Missing P2 data rejects only when needed.

An aligned full-ROM literal scan is saved locally as research context. The
absence of direct tracking-address literals does not exclude displacement or
indirect writers; the actual F91A/F924 writes use A5-relative operands. No
whole-game writer-completeness claim is inferred from that scan.

## Retained pool and movie evidence

Slot 63 / FFFF2E82 is now pool kind 7, `CollisionProbe`. Position, flags,
presentation, target/countdown, control identity and both extents persist.
The thirteen-field pool header extends the prior eight fields with X mask,
secondary gate, secondary-presence boolean and optional X/Y. Earlier header
forms remain valid for earlier scopes. P1 tracking is resolved after each native
wrapper; subsequent input rows remain physical held masks only.

Fresh ordinary recording execution and an independent unhooked replay agree at
the declared exposed-state endpoint. Each native preset matches **34 collision
updates and 395 ordered pool events**: also 34 P1/emitter, 136 trail, twelve
reversal, 136 private and 34 table updates; nine allocations/releases, complete
free order/RNG, 34 banners and two sounds. The new helper evidence checks
**32 X misses and two Y-only misses**, stack/caller identities, control selection,
comparison registers and Z at return. No hit or P2 invocation is invented.

Capture has 9,973 routine events and 52,895 native events, with zero edits,
drops or overflow. Managed writes total 1,840, reserved writes 271, free-stack
writes 27. Slot 63's only ordinary object write is the existing zero rendering
clear, verified separately; its service is read-only. Seven external reservations
remain: five active return-only objects and two inactive occupied slots.
This is scoped pool parity; hidden devices, world, frame, rendering and audio
remain outside the equivalence claim.

## Validation and limits

**478,345 original/native comparisons per debug/release/sanitize**:
341,497 overlap, 66,376 service and 70,472 scheduled cases. Word domains exhaust
X/Y distances, both extent operands, masks and the secondary gate; edge products,
seeded random inputs, repeated calls and all presentation modes add coverage.
All 28 new instructions execute. P1/P2 hits stop before 7910 in the restricted
original and reject in native code. Callback and missing-P2 boundaries reject.
The harness confines reads, writes and executable ranges; helper/service writes
are limited to stack, and scheduled writes to known presentation fields.

Primary ROM hash/decode and a 95-instruction closed graph pass; four selected
GNU checks corroborate ADD.W, CMP.W, BHI and RTS. No GNU claim is made for every
instruction. Authored tests cover inclusive edges, signed-looking unsigned values,
wrapped thresholds, sentinel tracking, short-circuit order and rollback after
release, table motion, emitter RNG/allocation, P1 movement, banner and reversal
allocation. **196 Python tests, zero skips; 44/44 CTests per preset** pass.
Table/private/trail/reversal corpora and the older 390-call P1 fixture pass per
preset; eight additional sanitized component corpora pass. Exact reports/hashes
and skips are in `re/collision_validation.json`.

One bounded helper and one partial service mapping promote **96 preclassified
bytes**. Totals: **106 bounded mappings plus two partial / 117 indexed**;
26,257 classified and 1,022,319 unclassified bytes, unchanged. Cumulative scoped
execution is 1,543 instructions; historical corpora outside this pass are not
silently counted as fresh tests. Native playability remains **none** and
TASK-0010 remains in progress. **callback79B6 and collision-hit7910 remain
explicitly unsupported.** Next replace the seven remaining return-only
reservations with verified typed presentation/occupancy state.

## Later refinement (session 039)

The miss-only claims above are scoped to `[1066,1100)`. The session-039 replay of
frames 0..1066 ([[03_Reverse_Engineering/findings/FIND-0037-collision-quad]])
shows the same slot-63 probe, created by 783A at frame 629, reaching the
unsupported 7910 hit path nine times at frames 823..831. The 03FF X mask wraps
P1 tracking X 0486..04BE into the probe's window. The first hit rewrote and
deactivated slot 53; the probe itself is unchanged. Hit7910 stays unsupported;
native retained comparisons of the probe stop and reject at the first hit.
