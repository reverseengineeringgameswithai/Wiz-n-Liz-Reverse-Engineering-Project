---
id: FIND-0033
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Retained return-only objects and dormant occupancy

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/return_only_step.json`; validation: `re/return_only_validation.json`.
Source: `src/sim/return_only.*`, `src/sim/mixed_pool.*`.
Evidence: `tools/return_only_compare.py`, `tools/genesis_return_only_evidence.py`,
`tools/genesis_mixed_session.py`. This composes existing mapped routines;
no new original function mapping or classified ROM bytes are claimed.

## Dispatch and state contract

The original `[69AA,69C2)` slot phase tests the sign bit of object +00. Inactive
objects branch directly to 69C2 before any presentation, handler or service.
Active objects invoke F76C, load/invoke +16, then load/invoke +46. For the seven
objects in this contract, both selectors are exactly **12646 (RTS)** and the
stored callback is zero. The phase ends before the caller advances A6.

`ReturnOnlyObject` retains position, flags, mode, three presentation words,
counter/reload, target, countdown and opaque logical control ID. The typed
contract selects both RTS calls; it contains no original code pointers.
Presentation uses the existing byte/word wrapping semantics, old-frame target
comparison, loop/bounce boundaries and counter reload. Any invoked callback,
including the original null selector, rejects transactionally. A zero stored
callback is not interpreted as a successful function invocation.

A dormant object stays occupied. `MixedPool` now permits a dormant typed
return-only seed while still rejecting free-stack entries that name occupied
objects. It preserves generation and emits `PoolEventKind::inactive` (kind 3)
without consuming the active-update budget. These events are state observations,
not extra simulation updates. Ascending slot iteration, LIFO reuse, later-slot
birth behavior and all earlier rollback rules remain intact. No initializer,
activation producer or release for this new type is implemented. An explicit
active component input is checked normally and cannot inherit an earlier skip.

Pool transport kind **8** carries twelve state fields after its tag:
X, Y, flags, mode, first/begin/end, counter/reload, target, countdown, control ID.
Existing header forms and physical-only subsequent rows are unchanged. The
original adapter rejects unknown selectors/control identities and verifies
unrepresented byte +01, render word +14 and bytes +1E..+45 are zero. This does
not silently import unknown private state. The render clear remains an audited
zero write, not a native rendering implementation.

## Ordinary slot and writer evidence

| Slot / address | Activity | Retained behavior |
| --- | --- | --- |
| 52 / FFFF2B28 | mode 00 | Dormant, first word 541, never free |
| 58 / FFFF2CFC | mode 81 | Position 164,270; frames 916..921; reload 5; flags 0800 |
| 59 / FFFF2D4A | mode 81 | Position 161,270; frames 916..921; reload 4 |
| 60 / FFFF2D98 | mode 80 | Position 182,294; first word 915 |
| 61 / FFFF2DE6 | mode 80 | Position 150,294; first word 914 |
| 62 / FFFF2E34 | mode 80 | Position 182,262; first word 913 |
| 66 / FFFF2F6C | mode 00 | Dormant, first word 541, never free |

In movie `[1066,1100)`, each active slot has exactly one presentation and two
RTS invocations per phase. The dormant pair has only the active gate and 69C2
boundary. Complete per-frame routine evidence rejects extra invocations outside
this phase; stacks, selected A0, preserved A5/A6 and unrelated state are checked.
Every represented field is compared at the initial seed, phase boundaries and
final RAM. Each dormant observation is also emitted and compared natively.

The seven slots have **271 writes**: 101 animation writes for slots 58/59 and
170 zero rendering clears for the five active slots. Dormant slots have no
writes. The guard checks exact presentation next-PC/offset/width combinations,
ownership and render-zero values. Selector, activation, private-field and
foreign writes reject, including transients. Their occupancy and identities
never change; neither allocator nor release touches them in the measured window.

The retained pool now has **zero external reservations in this window**. Its
68 slots start with fifty free and eighteen typed occupied entries. The generic
`ExternalReservation` API remains for older explicitly scoped callers, but the
current capture adapter has no reservation fallback: unknown objects reject.
Removing reservations from this interval does not establish whole-world parity.

## Validation

**286,848 original/native cases per debug/release/sanitize** cover all mode and
counter bytes, every first-frame word in both directions, boundary products,
repeated calls, inactive callback traps and deterministic random preserved fields.
Original execution checks exact presentation/RTS cadence and unchanged object
bytes outside presentation, plus A5/A6 and balanced stacks. There are 3,295,984
presentation calls and 6,591,968 RTS calls per corpus. All **42 supported
successful instructions** execute; callback-path prefixes run only in rejection
checks. Static closure covers 67 instructions, with four GNU checks for BPL,
JSR, SUBQ.B and RTS. No new instruction coverage is added to cumulative totals.

Fresh ordinary capture and independent unhooked replay support **633 ordered
records** per native preset: 565 spawn/update/release events plus 68 inactive
observations. Added work is 170 active return-only updates; all prior P1/emitter,
trail/reversal/private/table/collision states, nine allocations/releases, full
free order/RNG, 34 banners and two sounds still match. Zero edits, dropped events
or overflow. Capture contains 9,973 routine / 52,895 native events, 2,111 managed
slot writes and 27 free-stack writes. Hidden-device state is outside the endpoint.

**198 Python tests, zero skips; 46/46 CTests per preset** pass. Tests distinguish
free versus dormant occupancy, exact event order/generations, exhausted capacity,
callback traps, raw-layout and writer rejection, extra invocation rejection,
and rollback after earlier presentation, release, emitter allocation/RNG, P1,
banner scratch and reversal allocation. Selected component and P1 regressions
are indexed in `re/return_only_validation.json`, with exact hashes and skips.

Totals stay **106 bounded mappings plus two partial / 117 indexed**;
26,257 classified / 1,022,319 unclassified bytes; 1,543 cumulative executed
instructions. This pass adds composition and retained state, not a new routine
mapping. **callback79B6 and collision-hit7910 remain unsupported.** TASK-0010 is
in progress; native playability **none**. Reference emulation remains test tooling.

Next reconstruct the **F9E2 allocator and 7B9C pair initializer**, including
A6 selection, defaults, free-stack/exhaustion boundaries and FF31C0 identity.
Static `[7B9C,7C26)` initializes two return-only objects whose fields match slots
58/59; their actual creation provenance is a lead to verify, not a movie claim.
The initializer and its allocator remain unimplemented in this checkpoint.
