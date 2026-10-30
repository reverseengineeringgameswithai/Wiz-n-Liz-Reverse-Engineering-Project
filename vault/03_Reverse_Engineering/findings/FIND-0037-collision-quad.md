---
id: FIND-0037
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# The 783A collision quad initializer

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/collision_quad_step.json`; validation: `re/collision_quad_validation.json`.
Source: `src/sim/mixed_pool.*`, `src/sim/collision_probe.*`, `src/sim/return_only.*`.
Evidence: `tools/pair_initializer_compare.py --variant collision-quad`,
`tools/genesis_pair_initializer.py`. Builds on
[[03_Reverse_Engineering/findings/FIND-0034-pair-initializer]],
[[03_Reverse_Engineering/findings/FIND-0036-rising-pair]], the 78EE miss service of
[[03_Reverse_Engineering/findings/FIND-0032-collision-miss]] and the return-only
objects of [[03_Reverse_Engineering/findings/FIND-0033-return-only-objects]].

## Static range and contract

`[783A,78EE)` is 180 bytes / 31 instructions, none previously classified. Level
setup calls it at 6898 (return 689C), after 7772 and before 7B9C. It calls F9E2
four times (783A, 787A, 789E, 78C2) and returns at 78EC.

| Member | Allocation | Stores after F9E2 |
| --- | --- | --- |
| Probe | Top free entry | mode 80, **+4A = caller A5**, X/Y 150/262, frame +06 = 912, handler +16 = 12646, **service +46 = 78EE**, +1E/+20 = 0038/0008; then `LEA (A6),A4` |
| Right | Next entry | mode 80, X = probe X then `ADDI.W #$20`, Y = probe Y, frame 913 |
| Below | Next entry | mode 80, X = probe X, Y = probe Y then `ADDI.W #$20`, frame 914 |
| Diagonal | Next entry | mode 80, X and Y both copied then +0x20, frame 915 |

The three later members keep F9E2's 12646/12646 selectors and are return-only
objects. **No member writes +08/+0A, +0C/+0D, +0E target or +10 countdown, and the
last three do not write +4A**, so those bytes are inherited from the slot. Mode
80 has bit 0 clear, so presentation never advances the frame and never tests the
target. There is no flags or FF31C0 store. On return A4 names the probe and A6
the diagonal member; A5 and the other registers are preserved.

## Native implementation

`MixedPool::initialize_group<N>` generalizes the shared F9E2 template to N
ordered, all-or-nothing pops; the three pair initializers keep their two-pop
wrapper. `InheritedObjectFields` gains optional `InheritedPresentation` (+08/+0A
words, +0C/+0D counter/reload). `MixedPool::initialize_collision_quad(control)`
requires that tail, as well as target, countdown and link, on every popped slot,
and builds `make_quad_probe` (a `CollisionProbe`, control as an explicit logical
input) followed by three `make_quad_return_only` members whose positions derive
from the probe's with word wrap. Exhaustion at any pop or unknown inheritance at
any member rejects with no allocation, generation or free-order change; the
original instead loops forever at FA1E. The pairs overwrite +08..+0D and do not
need the tail. Seed tag 9 accepts an optional four-field presentation tail.

`wiznliz-collision` gains `--quad` (authored cases) and `--quad-pool` (seeded
pool; a fourth header field gives the logical control, and each phase supplies
explicit 78EE inputs). As for 7772, the adapter conservatively requires a
mappable residue link on the probe slot although 783A overwrites it, and treats
any nonzero +01, +1A..+45 residue as unknown even where 783A rewrites +1E..+21.

## Restricted original comparison

`--collision-quad` executes only `[783A,78EE)` and `[F9E2,FA1E)` over a 68-slot
fixture. Each case sets four popped slots, the caller A5, a fill byte and, per
member, +01, target, countdown, link, callback, private fill and independent
+08/+0A/+0C/+0D values. It checks preserved registers, A4 = probe, A6 = last
member, the head, FF31C0 unchanged and every unwritten byte. **8,746 cases per
debug/release/sanitize** pass. The original creates 4,542 quads and stops at
FA1E after 0/1/2/3 pops in 1,058/1,062/1,054/1,030 cases. Native creates the
2,592 quads whose inheritance is representable, byte-identical to the original,
and otherwise rejects at the first failing member in pop order: 3,372 as
exhausted and 2,782 as unknown inheritance. 45 successful instructions execute, **31 new**;
FA1E..FA30 never executes. GNU corroborates the link `MOVE.L`, the `LEA` and the
RTS; it cannot decode the immediate, A4-relative `MOVE.W` or `ADDI.W` forms here.

## Ordinary recording evidence

A fresh hooked replay of frames 0..1066 of the unchanged recording, with an
independent unhooked endpoint match, verifies 783A together with 7772, 7B9C and
7C26. 783A runs once, at frame 629 (caller 6898, A5 = FF0690), popping **63, 62,
61 then 60**; every inherited byte of those slots is zero apart from F9E2's
selectors. The frame-629 creation audit is complete, with exact contiguous
blocks of **65** (783A), 43 (7772), 40 (7B9C) and 38 (7C26) writes plus 54 other
F9E2-form writes and no foreign writer to any group slot or FF31C0. 65 F9E2 and
32 F994 calls occur in the interval; FA30 does not run.

Slots 63..60 then stay occupied with the three pairs (ten retained slots)
through 33 allocations, 31 releases and 432 walks. The probe's 78EE service runs
once per walk with X mask 03FF, a zero P2 gate and no P2 tracking. Native
initialization from the 783A-entry stack, verified inheritance (including the
zero +08..+0D tail) and the mapped control matches the original. **Native then
matches the first 189 retained walks, through frame 822.**

**At frames 823..831 the ordinary movie reaches the unsupported 7910 hit path
nine times**, always from the slot-63 probe inside its own 78EE service. P1
tracking X runs 0486..04BE; the 03FF mask wraps that to 134..190, within the
probe's inclusive X window. Native rejects exactly at the first hit walk with
`unsupported collision-hit7910 (primary)`; the remaining 243 walks (nine with
hits) are original-only continuity. The quad's own bytes never change: each
walk and frame boundary matches, slots 60..63 receive only contracted
render-clear writes, and their frame-1066 states equal the mixed-session seed
rows of [[03_Reverse_Engineering/findings/FIND-0032-collision-miss]] and
[[03_Reverse_Engineering/findings/FIND-0033-return-only-objects]]. This
establishes dynamic creation provenance for retained slots 63..60.

### Observed hit side effects (not reconstructed)

At frame 823 slot 53 was the active trail emitter and had just run its own 6D8C
update. Inside the probe's 78EE service, 7910 found FF31B0 zero and loaded slot
53 through P1 control +1A2. By static straight-line reading it then writes the
request words FF0A9E..FF0AA4 and calls FCB32 and 59AE; those globals are outside
the retained write record. The observed slot-53 writes follow: +4A = FF0690,
+08/+0A copied to +22/+26, Y − 4, a 5964 reinitialization (mode 87, frames
0227/021E/0227, target 021E, counter/reload 3/3, 12646/12646 selectors,
callback FAA4, flags 0), position 00A4/00F6, callback +1A = 79B6, one F994
allocation (slot 47), +42 = FFFF4486 and finally mode 0. The other eight hits
found slot 53 inactive and returned at 7A56. By 1066 slot 53 is an active trail
emitter again. These are observations of one recording, not a reconstructed hit
service; they bear on slot 53's unexplained type history noted in
[[03_Reverse_Engineering/findings/FIND-0036-rising-pair]].

Update: [[03_Reverse_Engineering/findings/FIND-0043-fruit-delivery]] makes the
7910 hit native and compares all nine ordinary hits (823 delivers; the sparkle and
the copy pop slots 54 and 47) and the created objects' later walks. The
continuity above still runs without a `PickupWorld` and so still stops at 823.

## Limits and next validation

Only 783A is newly mapped. Collision-hit7910 and everything it reaches (FCB32,
59AE, 5964, FB06 and the slot-53 retargeting), the P2 collision producer, the
FF31B0/FF31A4/FF31A6 gate producers, the rest of level setup (6EC8 → 67,
6EDC → 66, 6A94, 6EB6 and later), other F9E2 callers, FA30, pool resets,
7AD6/callback79B6 and the overlap-hit FF31C0 readers remain unreconstructed or
unsupported. TASK-0010 remains in progress; **native playability: none**.
