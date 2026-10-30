---
id: FIND-0036
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# The 7772 rising pair initializer

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/rising_pair_step.json`; validation: `re/rising_pair_validation.json`.
Source: `src/sim/private_object.*`, `src/sim/mixed_pool.*`. Evidence:
`tools/pair_initializer_compare.py --variant rising`,
`tools/genesis_pair_initializer.py`. Builds on
[[03_Reverse_Engineering/findings/FIND-0034-pair-initializer]],
[[03_Reverse_Engineering/findings/FIND-0035-visibility-pair]] and the 7808
handler of [[03_Reverse_Engineering/findings/FIND-0030-private-object-updates]].

## Static range and contract

`[7772,7808)` is 150 bytes / 27 instructions, none previously classified. Level
setup calls it at 6894 (return 6898), before 783A and 7B9C. It calls F9E2 twice.

| Member | Allocation | Stores after F9E2 |
| --- | --- | --- |
| First | Top free entry | mode 81, **+4A = caller A5**, X/Y 158/262, frames 922/922/927, counter/reload 5/5, handler 7808, **countdown +10 = 0**; then `LEA (A6),A4` |
| Second | Next entry | **+4A = caller A5**, mode 81, **X = first X, then +0x20 (word)**, **Y = first Y** (both via A4), frames 928/928/933, 5/5, handler 7808, countdown 0 |

There is no flags or FF31C0 store. On return A4 names the first object and A6
the second; A5 and the other registers are preserved. Because 7772 writes the
link and countdown itself, only +01, +0E target, +1A and +1E..+45 are inherited
from the slot. Mode 81 never tests the target. The 7808 handler later consumes
only the FF31B0 rise gate (closed gate: Y=0106, countdown 8).

## Native implementation

`make_rising_pair_member(member, inherited, control, first)` builds one rising
`PrivateObject`: the control is an explicit logical caller input, countdown is
zero, and the second member's position is computed from the first member's
(X+0x20 with word wrap, same Y). `MixedPool::initialize_rising_pair(control)`
uses the shared two-pop template, feeding the first member's position to the
second. Inheritance (target plus zero unrepresented bytes) must be verified;
exhaustion or unknown inheritance rejects without allocation.
`wiznliz-private` gains `--rising-pair` (the shared case's register field is the
caller A5) and `--rising-pair-pool` (a fourth header field gives the logical
control). The ordinary adapter maps A5 through the same 0/FF0690/FF0838 table
and rejects unmapped controls; it conservatively also requires a mappable
residue link, though 7772 overwrites it.

## Restricted original comparison

`--rising-pair` seeds A5 from the case and checks A5 preserved, A4 = first
object, A6 = second and every unwritten byte unchanged. **8,714 cases per
debug/release/sanitize** pass with the shared outcome split (3,989 identical,
2,491 exhaustion, 2,234 unrepresented inheritance). 41 successful instructions
execute, **27 new**; FA1E..FA30 never executes. Eight GNU register-form checks
plus four 7772 forms (link stores, countdown clear, LEA) and RTS corroborate the
decoder; GNU cannot decode `MOVE.W d16(An),d16(An)` or `ADDI.W` here.

## Ordinary recording evidence

The fresh frames 0..1066 replay now validates 7772, 7B9C and 7C26 together.
7772 runs once, at frame 629 (caller 6898, A5 = FF0690), popping **65 then 64**
from a 66-entry stack; there is no 7772 run at frame 156. The frame-629 creation
group has a complete write trace with exact blocks of 43 (7772), 40 (7B9C) and
38 (7C26) writes, plus 90 other F9E2-form writes and no foreign writer to any
pair slot or FF31C0. Native initialization from the 7772-entry stack with the
mapped control matches.

Slots 65/64 then stay occupied with 59/58/57/56 through 33 allocations, 31
releases and 432 walks. FF31B0/FF31A4/FF31A6 are zero at every phase entry of
these slots; native 7808 therefore pins Y=0106 and reloads countdown 8, and all
2,592 retained updates of the six slots match. Boundaries match every frame and
the 1066 states equal the mixed-session seed rows. Write traces are complete in
435/436 frames (632 dropped); there, 1,566 and 1,559 writes to slots 64/65 are
contracted presentation, render-clear or 7808 forms with matching owner.
This establishes dynamic creation provenance for retained slots 65/64.

## Limits and next validation

Only 7772 is newly mapped. The FF31B0 rise-gate producer and the remaining level
setup (6EC8 → 67, 6EDC → 66, the four-object 783A → 63..60, 6A94, 6EB6 and
later calls), other F9E2 callers, FA30, pool resets, 7AD6/callback79B6,
overlap-hit FF31C0 readers and collision-hit7910 remain unreconstructed or
unsupported. TASK-0010 remains in progress; **native playability: none**.
