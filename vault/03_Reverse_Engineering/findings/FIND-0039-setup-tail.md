---
id: FIND-0039
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# 6A94 pickups, 6EB6 control links and the `[68A4,68BC)` setup tail

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/setup_tail_step.json`; validation: `re/setup_tail_validation.json`.
Source: `src/sim/collision_probe.*`, `src/sim/mixed_pool.*`. Evidence:
`tools/pair_initializer_compare.py --variant setup-tail`,
`tools/genesis_pair_initializer.py`. Continues
[[03_Reverse_Engineering/findings/FIND-0038-setup-prefix]] and bears on the trail
emitter of [[03_Reverse_Engineering/findings/FIND-0028-trail-allocator-client]].

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[68A4,68BC)` | 5 | BSR 6A94, `LEA FF0690,A5`, BSR 6EB6, `LEA FF0838,A5`, BSR 6EB6 (fragment) |
| `[6A94,6AF0)` | 26 | Clear 16 × 12 bytes from FF447A, FF31AC and FF31B0; for each of 16 FF312C kinds other than FFFF call 6AF0 |
| `[6AF0,6B44)` | 21 | Pop F9E2; +4A = A5, +42 = A3; write the (object, A0, A1) record; mode 81, position, extents 0010/0010, service 6BD6, countdown, handler 12646 |
| `[6B44,6BB2)` | 28 | Frames: signed kind < 14 → kind × 6 + 0260 (MULU.W, ADDI.W), end + 5; else 020D/020D/0214, 0205/0205/020C, or 01FD/01FD/0204 |
| `[6BB2,6BD6)` | 8 | Counter/reload 1/1 when the countdown is 2, else 5/5 |
| `[6EB6,6EC8)` | 4 | Pop F9E2, store it at +1A2 of the A5 control record, clear its mode (6EC8's shape) |

364 bytes / 92 instructions, none previously classified. 6A94 passes D0/D1 from
the next FF4C80 pair (**consumed only for created pickups**, Y + 16 by ADDI.W),
D2/D3 from that entry's FF312C kind and FF314C count, A0/A1 that entry's
addresses and A3 the next FF447A record. Each pickup inherits only the target;
6EB6's objects inherit position, +08..+0D, target, countdown and link as 6EC8's do.

Service 6BD6 has 78EE's miss shape (AC5E against FF0690, then FF0838 only behind
the FF33E2 gate); its hit target 6C00 requests a sound and, by static reading,
for ordinary kinds loads the control's +1A2 object and either initializes it as
the trail emitter through 6D22 (which starts with an FB06 copy of the pickup) or
exchanges state with it.

## Native implementation

A new `Pickup` pool type (variant 9) carries position, presentation, target,
countdown, control, extents and the logical FF447A record index. `step_pickup`
shares 78EE's miss logic and rejects a hit as `unsupported pickup-hit 6C00`.
`make_pickup` reproduces 6AF0/6B44/6BB2 with word arithmetic (including MULU.W
truncation). `initialize_pickups(state, PickupTables, control)` clears all
sixteen logical records, FF31AC (`activation_target`) and the FF31B0 rise gate
(when private globals are present), then creates pickups in entry order with
densely consumed positions. `initialize_control_link(state, player)` reuses the
dormant constructor and stores `control_links[player]`.
`initialize_level_setup_tail(state, tables, control)` runs 6A94 then both links,
all or nothing. `wiznliz-return-only` gains `--tail` and `--tail-pool`. The 6BD6
miss path is native through the shared logic but is not indexed until a
restricted corpus covers it.

## Restricted original comparison

`--setup-tail` executes `[68A4,68BC)` and every callee, stopping at 68BC. Each
case gives eighteen candidate slots, the 64 table words and per-member residue;
the harness seeds stale records, FF31AC, FF31B0 and both links, and checks
D4–D6/A4 preserved, A5/A6 at return, the head, every record, both clears, both
links and every byte outside each member's contracted set. **8,820 cases per
debug/release/sanitize** pass: 0..16 pickups with every frame family, signed and
negative kinds, count 2 cadence and Y wrap; the original stops at FA1E after each
of 0..17 pops; native creates 5,290 tails byte-identically and otherwise rejects
at the first failing member (1,833 exhausted, 1,697 unknown inheritance). 106
successful instructions execute, **92 new**. GNU corroborates the BSR, MOVE.L
register/postincrement, CLR.L postincrement and DBF forms.

## Ordinary recording evidence

A fresh hooked replay of frames 0..1066 with an independent unhooked endpoint
verifies one tail at frame 629 from the post-prefix stack. Of 16 FF312C entries
only the first two are not FFFF (kinds 5 and 6, counts 0), creating **pickups
55 and 54** at (02D0,00B0) and (0370,00B0) with records 0 and 1; 6EB6 then pops
**53** (A5 = FF0690) and **52** (A5 = FF0838). The frame-629 audit is complete
with the prefix (216 writes) and the tail (153 writes: three BSR pushes; 126 for
6A94, being the A3 save, 48 record clears, two global clears and 37 per pickup;
and 12 per link) as exact contiguous blocks, and no other allocator write that frame. At
each 6AF0 return the D2 upper word holds the MULU product's upper word, as the
validator now requires. Native builds the tail from the 68A4-entry stack and
matches every member, record and link.

Native then matches **146 walks**; at **frame 780** P1 overlaps pickup 54, whose
unsupported 6C00 path rewrites the pickup and, through 6D22, FB06-copies it into
dormant link 53, which becomes the trail emitter (handler 6D8C). Native rejects
at that walk with `unsupported pickup-hit 6C00 (primary)`; 286 later walks are
original-only. Pickup 55 is hit the same way at frame 980. Link 52 stays dormant
in the original to 1066 and equals the mixed-session seed there (natively it is
compared with the rest of the tail through frame 779); the control links never
change after 629. The P1 trail emitter's origin noted as open in
[[03_Reverse_Engineering/findings/FIND-0028-trail-allocator-client]] is
therefore observed here, though not reconstructed.

Update: [[03_Reverse_Engineering/findings/FIND-0042-pickup-hit]] reconstructs
the 6C00 hit (6D22, FB06, 59BC and the swap callbacks) and compares both ordinary
hits (780, 980) natively. The "same way" at 980 is confirmed: link 53 is dormant
again then, after the unsupported hit7910 at 823.

Update: [[03_Reverse_Engineering/findings/FIND-0045-retained-world]] runs the
tail with the rest of the setup in one native world through every loop to 1066,
past both hits; the per-group comparison above keeps its 780 bound.

## Limits and next validation

Newly mapped: 6A94, 6AF0, 6B44, 6BB2, 6EB6 and the fragment. The 6C00 pickup hit,
6D22 (trail-emitter initializer) and FB06, the 6BD6 miss path's restricted
corpus, 7AD6/callback79B6, hit7910, the setup from 68BC (7DB8, 6EF0, 7FBE, 7154,
735E, 7568, …), other F9E2 callers, FA30, pool resets and gate producers remain
unreconstructed or unsupported. The FF312C/FF314C/FF4C80 tables' producers are
not native. TASK-0010 remains in progress; **native playability: none**.
