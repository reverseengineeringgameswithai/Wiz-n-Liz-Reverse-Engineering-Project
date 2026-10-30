---
id: FIND-0035
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# The 7C26 gated-visibility pair initializer

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/visibility_pair_step.json`; validation: `re/visibility_pair_validation.json`.
Source: `src/sim/private_object.*`, `src/sim/mixed_pool.*`. Evidence:
`tools/pair_initializer_compare.py --variant visibility`,
`tools/genesis_pair_initializer.py`. Builds on the F9E2 allocator and pool
inheritance rules of [[03_Reverse_Engineering/findings/FIND-0034-pair-initializer]]
and the 7CA4 handler of [[03_Reverse_Engineering/findings/FIND-0030-private-object-updates]].

## Static range and contract

`[7C26,7CA4)` is 126 bytes / 21 instructions, none previously classified. It is
the next call in level setup after 7B9C (`[6886,68A4)`, return 68A4). It calls
F9E2 twice and stores nine fields per member; the RTS is at 7CA2 and the 7CA4
handler begins immediately after.

| Member | Allocation | Stores after F9E2 |
| --- | --- | --- |
| First | Top free entry | mode 81, X/Y 287/152, frames 892/892/901, counter/reload 5/5, handler 7CA4 |
| Second | Next entry | mode 81, X/Y 287/184, frames 902/902/911, counter/reload 5/5, handler 7CA4 |

Unlike 7B9C it writes **no flags and no FF31C0**; F9E2's cleared +12 stays zero.
A6 is left naming the second member; at frame 629 it enters with A6 still naming
7B9C's second object, showing the setup sequence never restores A6. Fields F9E2
leaves untouched (+01, +0E target, +10 countdown, +1A, +1E..+45, +4A link) are
inherited from the slot. Mode 81 never tests target, so an inherited target
cannot fire while the mode stays 81. The 7CA4 handler then reads only the
shared FF31A6 (flags) and FF31A4 (hide) gate words.

## Native implementation

`make_visibility_pair_member` builds one `PrivateObject` (gated visibility)
from F9E2 defaults, 7C26 stores and explicit `InheritedObjectFields`.
`MixedPool::initialize_visibility_pair()` shares one transactional template
with `initialize_return_only_pair()`: two ordered LIFO pops, generation
increments, verified inheritance required, exhaustion or unknown inheritance
rejecting with no allocation. `InheritedObjectFields`, `PairMember` and
`ObjectPair` now live with the shared pool identities in `src/sim/reversal.hpp`.
No anchor is recorded. `wiznliz-private` gains `--pair` and `--pair-pool`; the
latter takes one explicit rise/flags/hide gate row per phase.

The mixed-session private seed adapter now also verifies that unrepresented
private bytes (+01, +1E..+45) are zero, matching the return-only adapter, rather
than silently discarding them. All four ordinary private objects satisfy it.

## Restricted original comparison

`--visibility-pair` executes only `[7C26,7CA4)` and `[F9E2,FA1E)`; FF31C0 is
readable but not writable and must stay unchanged. The same **8,714 cases per
debug/release/sanitize** as 7B9C pass: 3,989 identical pairs, 2,491 exhaustion
and 2,234 unrepresented-inheritance rejections. 35 successful instructions
execute, **21 of them new**; FA1E..FA30 never executes.

## Ordinary recording evidence

The fresh frames 0..1066 replay (shared with FIND-0034's evidence) covers both
initializers. 7C26 runs ordinarily twice:

- Frame 156 (caller 1EC58, after 7B9C at 1EC54) pops slots 41/40 and finishes
  in frame 157. A **level-6 VBlank interrupt** arrives before 7C50: its
  exception frame (interrupted PC long, saved SR 2000 word) is reported at that
  PC. The audit recognizes exactly that shape and records it; every other write
  in frames 156–157 is either an exact initializer/F9E2 write or touches neither
  pair slots nor FF31C0.
- Frame 629 (caller 68A4) pops **57 then 56** after 7B9C's 59/58.

Both creation groups have complete write traces: 40 exact 7B9C writes plus 38
exact 7C26 writes each. Slots 57/56 stay occupied with 59/58 through 33
allocations, 31 releases and 432 walks. FF31A4/FF31A6/FF31B0 are zero at every
phase entry of both slots, so the native 7CA4 step consumes zero gates. All 1,728 retained updates of
the four slots match natively, boundaries match every frame, and the 1066 states
equal the mixed-session seed rows. Write traces are complete in 435/436 frames
(632 dropped); there, all 711 writes to each of slots 57/56 are contracted
presentation, render-clear or 7CA4 forms with matching owner.

This establishes dynamic creation provenance for retained slots 57/56. The
fresh `[1066,1100)` mixed capture with the tightened adapter still matches
633 ordered records plus the FF31C0 anchor in every preset.

## Limits and next validation

Only 7C26 is newly mapped. Gate producers, the remaining level setup
(`6EC8`, `6EDC`, `7772`, `783A`, `6A94`, `6EB6` and later calls), other F9E2
callers, FA30, pool resets, 7AD6/callback79B6, overlap-hit FF31C0 readers and
collision-hit7910 remain unreconstructed or unsupported. Zero gates are an
observation for this interval, not a model of their producers.
TASK-0010 remains in progress; **native playability: none**.
