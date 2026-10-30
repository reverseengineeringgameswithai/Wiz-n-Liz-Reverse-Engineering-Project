---
id: FIND-0038
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# 6EC8/6EDC dormant initializers and the `[6886,68A4)` setup prefix

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/setup_prefix_step.json`; validation: `re/setup_prefix_validation.json`.
Source: `src/sim/mixed_pool.*`, `src/sim/return_only.*`. Evidence:
`tools/pair_initializer_compare.py --variant setup-prefix`,
`tools/genesis_pair_initializer.py`. Builds on
[[03_Reverse_Engineering/findings/FIND-0034-pair-initializer]],
[[03_Reverse_Engineering/findings/FIND-0035-visibility-pair]],
[[03_Reverse_Engineering/findings/FIND-0036-rising-pair]] and
[[03_Reverse_Engineering/findings/FIND-0037-collision-quad]].

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[6EC8,6EDC)` | 4 | `JSR F9E2`, `MOVE.L A6,FF31B4`, `MOVE.B #0,(A6)`, RTS |
| `[6EDC,6EF0)` | 4 | Same, storing FF31B8 |
| `[6886,68A4)` | 7 | `LEA FF0690,A5`, then BSR 6EC8, 6EDC, 7772, 783A, 7B9C, 7C26; falls through to 68A4 |

70 bytes / 15 instructions, none previously classified. The fragment lies inside
the level-setup routine (its entry precedes 6840), so it is a mapped fragment,
not an indexed function; 6EC8 and 6EDC are FUNC-0123/0124.

Each dormant initializer leaves F9E2's other defaults (frame +06 = 021D, flags 0,
+14 = 0, 12646/12646 selectors) and clears the mode byte, so the object is
dormant and the walk skips it. **Position +02/+04**, +08..+0D, target, countdown,
+01, +1A..+45 and the link are inherited from the slot. The prefix makes **twelve**
ordered pops (1+1+2+4+2+2); FF31B4, FF31B8 and FF31C0 name members 1, 2 and 10.
A ROM-wide literal search finds one reader each of FF31B4 (7B24) and FF31B8
(7AE8), both inside 7AD6.

## Native implementation

`InheritedObjectFields` gains optional `position`; `InheritanceNeeds` tells the
shared N-pop template which optional parts a member keeps. `make_dormant` and
`MixedPool::initialize_dormant` build the dormant `ReturnOnlyObject`, requiring
verified position and presentation. `MixedSessionState::dormant_anchors` holds the
logical FF31B4/FF31B8 identities; `initialize_dormant(state, DormantAnchor)`
commits allocation and identity together, and the mixed session requires a
present identity to stay live. `initialize_level_setup_prefix(state, control)`
runs all six initializers in order, with `control` the logical identity of
FF0690; any exhaustion or unknown inheritance leaves the pool and all three
identities unchanged. Seed tag 9 accepts a further two-field position tail.
`wiznliz-return-only` gains `--dormant-pool`, `--prefix` and `--prefix-pool`.

## Restricted original comparison

`--setup-prefix` executes `[6886,68A4)` and every callee from a 68-slot fixture and
stops at 68A4. Each case sets twelve popped slots, a fill byte and per-member
+01, target, countdown, link, callback, private fill, +08..+0D and position. The
harness checks preserved D0–D7/A1–A3, A5 = FF0690, A4 = probe and A6 = last
member, the head, FF31B4/FF31B8/FF31C0 (written only once their initializer
completes), and every byte outside each member's contracted set. **8,748 cases
per debug/release/sanitize** pass: the original stops at FA1E after each of 0..11
pops, and native creates 4,625 prefixes byte-identically, otherwise rejecting at
the first failing member in pop order (1,745 exhausted, 2,378 unknown
inheritance). 131 successful instructions execute, **15 new**. GNU corroborates
the six BSRs and the RTSes; it cannot decode the absolute LEA/MOVE or `MOVE #imm`
forms here.

## Ordinary recording evidence

A fresh hooked replay of frames 0..1066 with an independent unhooked endpoint
verifies one ordinary prefix, at frame 629, from a 68-entry stack: 6EC8 pops
**67**, 6EDC pops **66**, then 7772 65/64, 783A 63..60, 7B9C 59/58 and 7C26 57/56,
each between its BSR and return marks at one stack depth with A5 = FF0690. The
frame-629 audit is complete: the whole prefix is one contiguous **216-write**
block (six BSR pushes plus 12+12+43+65+40+38), with 36 other F9E2-form writes and
no foreign writer to any group slot, FF31B4, FF31B8 or FF31C0. Native builds the
whole prefix from the 6886-entry stack and matches all twelve members and three
identities.

Slot 66 stays dormant to 1066: native matches all 432 walks as inactive
observations, and its 1066 state equals the mixed-session seed. Slot 67 stays
dormant until **frame 853, when unsupported 7AD6 (reached from callback79B6 on
slot 47) copies slot 47 into it with FB06**: 78 byte writes, then a 7A88 handler
runs. 7AD6 took its FF31AC-zero branch (traced at 7B22), copied with A6 = slot
47 and A4 = slot 67, and released slot 47 via FAA4; its FF31AC store is static
reading (the write record keeps pool and identity writes only). Native matches slot 67's first 219 walks and stops
before the conversion, with no native counterpart to reject; 213 later walks are
original-only. FF31B4/FF31B8 never change after 629. Slot 47 was itself the copy
of slot 53 that the frame-823 7910 hit made
([[03_Reverse_Engineering/findings/FIND-0037-collision-quad]]), so this chain
explains how slot 67 becomes the 7A88 object of
[[03_Reverse_Engineering/findings/FIND-0031-table-motion]], as observation only.

Update: [[03_Reverse_Engineering/findings/FIND-0044-first-ingredient]] makes
the 853 conversion of slot 67 native (callback79B6 and 7AD6's FF31AC-zero path)
and compares its 213 later walks natively as the table object; the continuity
above still stops at the conversion.

## Limits and next validation

Only 6EC8, 6EDC and the prefix fragment are newly mapped. 7AD6/callback79B6,
FB06, hit7910, the rest of level setup from 68A4 (6A94, 6EB6 ×2, 7DB8, 6EF0,
7FBE, 7154, 735E, …), other F9E2 callers, FA30, pool resets and gate producers
remain unreconstructed or unsupported. TASK-0010 remains in progress; **native
playability: none**.
