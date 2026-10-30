---
id: FIND-0042
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# 6C00: picking up, carrying and swapping fruit

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/pickup_hit_step.json`; validation: `re/pickup_hit_validation.json`.
Source: `src/sim/collision_probe.*`, `src/sim/trail.hpp`, `src/sim/mixed_pool.*`.
Evidence: `tools/pickup_hit_compare.py`, `tools/genesis_pair_initializer.py`.
Continues [[03_Reverse_Engineering/findings/FIND-0039-setup-tail]] (pickups and
links) and [[03_Reverse_Engineering/findings/FIND-0028-trail-allocator-client]]
(the 6D8C emitter).

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[6C00,6C50)` | 14 | Request sound 0089/0006/00C0/0001 (FF0A9E..FF0AA4, JSR FCB32); +08 of 020D/0205/01FD branches to 6E32/6E8A/6E5E; A4 = control +1A2; TST.B mode: zero → 6D22 |
| `[6C50,6CDA)` | 34 | Exchange: swap +06, +10, +08, +0A, +0D and +42 with the link; each record names its new holder (pickup last); X − 8; 59BC; 3/3; callback 6CDA |
| `[6CDA,6CF4)` | 5 | 5964, then 2/2 and callback 6CF4 |
| `[6CF4,6D22)` | 10 | Mode 81; 6B44 frames from the FF312C word the record's +4 names; X + 8; 6BB2 cadence from +10; service 6BD6, handler 12646 |
| `[6D22,6D8C)` | 20 | FB06 pickup → link; the record names the link; handler 6D8C, service 12646, +36 = 0, +4A = A5, ten FF80 history words; pickup X − 8, 59BC |
| `[59BC,5A06)` | 12 | Mode 85, frames 021E/021E/0227, target 0227, 3/3, both selectors 12646, callback FAA4, +12 AND 9FFF |
| `[5964,59AE)` | 12 | Mode 87, frames 0227/021E/0227, target 021E, 3/3, both selectors 12646, callback FAA4, +12 AND 9FFF |
| `[FB06,FB1A)` | 8 | Copy 78 bytes (A6) → (A4), preserving A4/A6 |

564 bytes / 115 instructions, none previously classified. 6CC0, 6CDA and 6D86 use
JSR (xxx).W. The walk reads the handler and service after presentation, so a
pickup re-dressed by 6CF4 runs 6BD6 in the same walk.

**Interpretation (probable):** this is the carried-fruit mechanic. The first
touch turns the control's dormant +1A2 link into the trail emitter that follows
the player showing the fruit; the touched fruit vanishes and frees its slot.
Touching another fruit while carrying swaps them: the emitter takes the new
fruit and the ground fruit vanishes, returns and re-forms as the swapped kind.
Records follow the objects holding each fruit.

## Native implementation

`Pickup` gains `PickupPhase` (collectable, vanishing, swapped_out, swapped_in);
`TrailEmitter` gains an optional `CarriedPickup` (count, record, extents).
`walk_pickup` runs one scheduled walk with the phase's callback (FAA4 release,
6CDA, 6CF4 re-dress from a supplied kind) and returns the contact.
`MixedPool::walk_pickup` and `MixedPool::step(..., PickupWorld*)` apply 6C00
with an explicit `PickupWorld` (control identities, +1A2 links, FF447A records,
FF312C kinds, FCB32 requests): `carry_pickup` (6D22), `exchange_carried`,
`begin_pickup_vanish`. Everything commits together; family frames, an active
non-emitter link, an emitter without carried bytes, a missing link or record and
a collectable callback reject. Without a world a contact rejects as before.
`wiznliz-collision --pickup-hit` exposes it.

## Restricted original comparison

`--pickup-hit` walks one seeded pickup through 69AA (F76C, its callbacks, the
handler, 6BD6, AC5E, 6C00 and every callee; FCB32 returns at a selector
mismatch) with both control links (dormant or carrying), the records, kinds,
mailbox and free stack, for up to 64 walks with optional tracker departure and
a seeded phase. It checks every pickup, link and global byte outside the printed
fields and stops at the family branches or a seeded collectable callback.
**6,576 cases per debug/release/sanitize** match exactly: 974 P1 and 182 P2
conversions, 862 P1 and 143 P2 exchanges, 554 releases, 49 re-dresses that stay
collectable, 128 repeat hits, 137 family stops and the callback stop. All 115
new instructions execute (244 in all). GNU corroborates fourteen register forms.

## Ordinary recording evidence

A fresh hooked replay of frames 0..1066 with an independent unhooked endpoint
(`3f66b79f…`, equal) now traces, inside each walk, the link after its load
(6C48), the exchange/6D22 returns, FCB32 with the mailbox, the 6CDA/6CF4
callbacks, the records and kinds. It finds **two ordinary hits, both 6D22
conversions of P1's link 53**: pickup 54 at frame 780 and pickup 55 at frame 980.
Each requests 0089/0006/00C0/0001, turns link 53 into the carrying emitter (the
record follows it) and starts the pickup's vanish; pickups 54 and 55 release
their slots through FAA4 at frames 810 and 1010. Native `--pickup-hit` compares
**all 62 walks** (the two hits and 60 vanishing walks, including both releases)
one walk at a time from each original entry state, and consecutive walks chain
(each exit equals the next entry), so the result equals a continuous native run
of each hit pickup. Untouched links are supplied only as context.

**Correction:** session 043 expected by static reading that pickup 55 would take
the exchange path at 980. It does not: at frame 823 the unsupported hit7910 path
(P1 on the slot-63 probe) runs 5964 on link 53, rewrites +02/+04/+1A/+22/+26/
+42/+4A and clears its mode (79B2), so the link is dormant again by 980. By static
reading hit7910 delivers the carried fruit: with a carrying link it requests
008C, allocates through 59AE/F9E2 and F994, copies the emitter (FB06) into a new
object with callback 79B6 and leaves the link dormant; with a dormant link it is
a bare RTS (7A56). The exchange path is therefore compared only by restricted
cases. The record is in `re/pickup_hit_validation.json` (`link_53_between_hits`).
The earlier tail comparison still stops at 780, because `--tail-pool` steps
without a `PickupWorld`.

Update: [[03_Reverse_Engineering/findings/FIND-0043-fruit-delivery]] makes
hit7910 native. Its +42 store writes back the value just copied, so the record
keeps naming link 53 after the delivery; link 53 stays unchanged until the 980
conversion loads it.

Update: [[03_Reverse_Engineering/findings/FIND-0045-retained-world]] reaches both
hits inside the native retained world, from the world's own pickups and link,
and follows link 53 continuously as the emitter afterwards.

## Limits and next validation

Newly mapped: 6C00 (partial), 6D22, 6CDA, 6CF4, 59BC, 5964 and FB06; 6BD6 is now
bounded. Natively 59BC/5964/FB06 serve only the pickup paths (their gated-lead
and 7AD6 callers are not native). The 6E32/6E8A/6E5E family branches, the
mixed session's use of `PickupWorld`, continuous native following of the emitter
after a conversion, 7AD6/callback79B6, hit7910 and the gate producers remain
unreconstructed or unsupported. TASK-0010 remains in progress; **native
playability: none**.
