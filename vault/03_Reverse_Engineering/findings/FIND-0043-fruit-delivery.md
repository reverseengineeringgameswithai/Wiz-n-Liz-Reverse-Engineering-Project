---
id: FIND-0043
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# 7910: delivering the carried fruit

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/delivery_step.json`; validation: `re/delivery_validation.json`. Source:
`src/sim/collision_probe.*`, `src/sim/mixed_pool.*`. Evidence:
`tools/delivery_compare.py`, `tools/genesis_pair_initializer.py`. Continues
[[03_Reverse_Engineering/findings/FIND-0042-pickup-hit]] (the carrying link) and
[[03_Reverse_Engineering/findings/FIND-0037-collision-quad]] (the 783A probe
whose 78EE service calls 7910).

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[7910,79B6)` | 37 | Return (79B4) while the long FF31B0 is nonzero. A4 = the touching control's +1A2 link; a zero mode byte returns at 7A56. Otherwise request sound 008C/0006/00C0/0001 (FF0A9E..FF0AA4, JSR FCB32); on the link: +4A = A5, +22 = +08, +26 = +0A; JSR 59AE at its position − (8,8); Y − 4; JSR 5964; position (00A4,00F6); callback 79B6; JSR F994 (the copy, A4); FB06 link → copy; the copy's +42 written back to the link; CLR.B the link's mode |
| `[59AE,59BC)` | 3 | JSR F9E2, then +02/+04 = D0/D1, falling into 59BC (mode 85, frames 021E/021E/0227, target 0227, 3/3, RTS selectors, FAA4 release, +12 AND 9FFF) |
| `[7A56,7A58)` | 1 | The RTS ending callback79B6's code; already classified with the `[7A46,7A58)` writer fragment |

180 new bytes / 40 new instructions (41 with 7A56). The first pop (F9E2, inside
59AE) is the sparkle and the second (F994) the copy; on an empty stack either
loops forever (FA1E, F9D0). 7972 and 797C use JSR (xxx).W. The link's Y − 4 is
dead: the (00A4,00F6) store overwrites it. The +42 store writes back the value
FB06 just copied, so **7910 changes no FF447A record**: the record still names
the link.

The copy's callback79B6 (not reconstructed) selects, through FF31AC, one of two
messages for the control's +46 via CB72. They are ROM data: D20E `01 14 FE 01 5A
"FIRST INGREDIENT COLLECTED!" FF` (FF31AC zero) and D22F `01 14 FE 01 5A "SECOND
INGREDIENT COLLECTED!"` followed by a further `FE 01 3C FE 01 5A` line.

**Interpretation (probable):** this is delivering a carried fruit as an
ingredient. Touching the probe (the 783A quad, the delivery point) while carrying
plays a sparkle where the carried fruit was and sends a copy of it to a fixed
position; 30 walks later its callback announces the first or second ingredient
and hands it to 7AD6. The player's link is free to carry again.

## Native implementation

`walk_collision_probe` runs one scheduled probe walk and returns the contact.
`MixedPool::walk_probe(id, inputs, rise_gate, world)` and `MixedPool::step`
(with a `PickupWorld` and the private globals' FF31B0) apply 7910: a nonzero
gate or a mode-zero link return; an active carrying `TrailEmitter` requests the
sound, then `deliver_carried` builds the sparkle (a `TrailParticle`: it has the
5A9A particle's shape with frames 021E..0227), the copy (new `DeliveredPickup`:
position, flags, presentation, target, control, the saved +22/+26 frames and the
carried count/record/extents) and the link left dormant (a mode-0
`ReturnOnlyObject` with the copy's other represented fields). The sparkle and the
copy pop in that order; fewer than two free entries, any other link, an emitter
without carried bytes and a missing link reject with no change. In `step` the
births emit spawn events and are walked in the same phase when their slots
follow the probe's. `step_delivered_pickup` walks the copy (presentation, RTS
selectors); its 79B6 callback rejects. Without a world a contact rejects as
before. `wiznliz-collision --probe-hit` and `--delivered` expose both.

Unrepresented copied bytes (the emitter's other history words and +36, both
slots' +1A, +1E.. residue of the sparkle's popped slot) are not read before
79B6 or the FAA4 release; the restricted harness checks them byte for byte.

## Restricted original comparison

`--probe-hit` walks one seeded probe through 69AA (F76C, its RTS handler, 78EE,
AC5E, 7910 and every callee: FCB32 to its selector-mismatch return, 59AE/F9E2/
59BC, 5964, F994 and FB06) with both links (dormant or carrying), FF31B0, the
78EE inputs and a free stack whose top two entries are explicit, for up to 64
walks with separate P1 and P2 departures. It stops at the allocator loops or a
seeded probe callback (CAF0). It checks every probe, link, created-object and
global byte outside the printed fields, that each copy equals its link except
the mode byte and that the pops are the stack's top entries in order.
`--delivered` walks a seeded sparkle or copy (stopping at 79B6) and checks every
byte outside the presentation and the free stack.

**8,557 cases per debug/release/sanitize** match exactly (4,425 probe walks and
4,132 later walks): 807 P1 and 202 P2 deliveries, 44 cases with two deliveries,
476 dormant returns, 781 closed FF31B0 gates, 836 repeat touches after a
delivery, 268 exhaustion and 67 probe-callback stops; 83 sparkle releases, 1,982
kept sparkles, 1,989 kept copies and 78 copy 79B6 stops. All 40 new instructions
execute (41 with 7A56; 206 in all). GNU corroborates 25 register/displacement
forms.

## Ordinary recording evidence

A fresh hooked replay of frames 0..1066 with an independent unhooked endpoint
now traces, inside each walk, the link after its load (7922), the sparkle after
59AE (7976), the dormant link and the copy after the final CLR.B (79B2), both
returns (79B4, 7A56), FCB32 with the mailbox, the free stack and the copy's
79B6 callback. It finds **nine ordinary 7910 hits, all P1 on the slot-63
probe**:

- **Frame 823 delivers** link 53's fruit (pickup 54's, carried since 780):
  sound 008C/0006/00C0/0001; the sparkle pops **slot 54** (the slot pickup 54
  released at 810, back on top of the stack) at the emitter's position − (8,8),
  then the copy pops **slot 47**; the copy equals link 53 except its mode byte.
- **Frames 824..831** find link 53 dormant and return at 7A56 with no request.
- Native `--probe-hit` compares all nine walks from each original entry state
  with the real free stack (the delivery's pops are its top two, in order).

Native `--delivered` then compares **all 60 later walks**, one at a time and
chained: the sparkle (slot 54) walks 824..853 and releases through FAA4 at 853;
the copy (slot 47) walks 824..852 and reaches 79B6 on its 30th walk at 853,
where native rejects. (Inside that unsupported callback, 7AD6 copies slot 47
into the dormant FF31B4 slot 67 and releases slot 47, as
[[03_Reverse_Engineering/findings/FIND-0038-setup-prefix]] observed.) Every
byte the native types do not represent is unchanged across those walks. Link 53
stays byte-identical from 823 until 6C00 loads it at 980, where the second 6D22
conversion of [[03_Reverse_Engineering/findings/FIND-0042-pickup-hit]] begins.

The retained-slot continuity still runs the pool without a `PickupWorld`, so it
keeps stopping at the probe's first hit (823) with the earlier rejection; the
hits are compared by the dedicated rows above.

Update: [[03_Reverse_Engineering/findings/FIND-0044-first-ingredient]] makes
the copy's 79B6 callback native on its first-ingredient path; the 853 walk and
slot 67's later walks now compare natively.

Update: [[03_Reverse_Engineering/findings/FIND-0045-retained-world]] reaches the
823 delivery inside the native retained world: the sparkle and the copy are
popped from the world's own free stack.

## Limits and next validation

Newly mapped: 7910 and 59AE (bounded). callback79B6 itself (frames back from
+22/+26, mode 81, 6BB2, the 7A88 table handler and 7A58 table, FF31AC with the
D22F/D20E messages through CB72, FF31BE/FF31BC and 7AD6), 7AD6, the 6C00 family
branches, the mixed session's `PickupWorld`, continuous native following of an
emitter between hits, the gated-pair leads, overlap-hit FF31C0 readers and the
gate producers remain unreconstructed or unsupported. TASK-0010 remains in
progress; **native playability: none**.
